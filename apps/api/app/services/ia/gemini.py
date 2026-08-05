"""Proveedor de IA sobre la Interactions API de Gemini.

Se usa `client.aio.interactions.create` — la API vigente; `models.generate_content`
quedó como legacy. Verificado contra google-genai 2.16.0: `create` acepta kwargs
directos y la respuesta expone `output_text`.
"""

import copy
import logging
from typing import Any

from google import genai
from pydantic import ValidationError

from app.schemas.ia import SalidaIA
from app.services.ia.base import ContextoPaciente, ErrorProveedorIA
from app.services.ia.prompts import INSTRUCCIONES, construir_prompt

logger = logging.getLogger(__name__)

# Claves de JSON Schema que no aportan a la generación y que conviene no mandar.
_CLAVES_A_QUITAR = ("title", "default")


def _inlinear_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Resuelve los `$ref`/`$defs` que genera Pydantic dejando el schema plano.

    Pydantic emite los submodelos como `{"$ref": "#/$defs/TagIA"}`. El soporte de
    referencias en los structured outputs de los proveedores es irregular, así que
    se inlinean antes de mandarlo. De paso se sacan `title` y `default`, que sólo
    agregan ruido al schema.
    """
    schema = copy.deepcopy(schema)
    defs: dict[str, Any] = schema.pop("$defs", {})

    def resolver(nodo: Any) -> Any:
        if isinstance(nodo, dict):
            referencia = nodo.get("$ref")
            if isinstance(referencia, str) and referencia.startswith("#/$defs/"):
                destino = defs[referencia.rsplit("/", 1)[-1]]
                extra = {k: v for k, v in nodo.items() if k != "$ref"}
                return {**resolver(copy.deepcopy(destino)), **extra}
            return {
                clave: resolver(valor)
                for clave, valor in nodo.items()
                if clave not in _CLAVES_A_QUITAR
            }
        if isinstance(nodo, list):
            return [resolver(item) for item in nodo]
        return nodo

    return resolver(schema)


def _forzar_requeridos(schema: dict[str, Any]) -> dict[str, Any]:
    """Marca como obligatorias TODAS las propiedades, en todos los niveles.

    Sin esto el schema pedía un solo campo: `resumen_clinico`. Los demás llevan
    `default_factory=list` o `default=""` en `SalidaIA`, y Pydantic considera no
    requerido a todo campo con default, así que quedaban fuera de `required`.

    La consecuencia era silenciosa y grave: devolver `tags`, `entidades` y
    `alertas_proxima_sesion` vacíos CUMPLÍA el contrato. El modelo no fallaba,
    hacía lo mínimo que se le pedía, y variaba entre llamadas. Medido antes de
    este cambio: 1 de cada 4 respuestas traía las entidades. Las otras 3 dejaban
    el genograma sin nodos y la sesión sin recordatorios, sin ningún error.

    Los defaults se mantienen del lado de Python a propósito: si aun así llega
    una respuesta incompleta, `SalidaIA` la parsea en vez de reventar.
    """
    schema = copy.deepcopy(schema)

    def recorrer(nodo: Any) -> Any:
        if isinstance(nodo, dict):
            nodo = {clave: recorrer(valor) for clave, valor in nodo.items()}
            propiedades = nodo.get("properties")
            if isinstance(propiedades, dict) and propiedades:
                nodo["required"] = list(propiedades)
            return nodo
        if isinstance(nodo, list):
            return [recorrer(item) for item in nodo]
        return nodo

    return recorrer(schema)


ESQUEMA_SALIDA = _forzar_requeridos(_inlinear_refs(SalidaIA.model_json_schema()))


class GeminiIA:
    """Implementa `ProveedorIA` contra la API de Gemini."""

    nombre = "gemini"

    def __init__(self, api_key: str, modelo: str) -> None:
        self._cliente = genai.Client(api_key=api_key)
        self.modelo = modelo

    async def procesar(self, notas: str, contexto: ContextoPaciente | None = None) -> SalidaIA:
        try:
            interaccion = await self._cliente.aio.interactions.create(
                model=self.modelo,
                system_instruction=INSTRUCCIONES,
                input=construir_prompt(notas, contexto),
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": ESQUEMA_SALIDA,
                },
            )
        except Exception as error:  # noqa: BLE001 — el SDK levanta varios tipos
            # Sin `exc_info` y sin el texto de las notas: son datos clínicos.
            logger.error("Falló la llamada a Gemini (%s): %s", self.modelo, type(error).__name__)
            raise ErrorProveedorIA(f"El proveedor de IA falló: {type(error).__name__}") from error

        crudo = interaccion.output_text or ""
        try:
            return SalidaIA.model_validate_json(crudo)
        except ValidationError as error:
            logger.error("Gemini devolvió una respuesta que no valida contra SalidaIA")
            raise ErrorProveedorIA(
                "La respuesta del modelo no respetó el schema esperado.", crudo=crudo
            ) from error
