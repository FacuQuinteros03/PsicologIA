"""Proveedor de IA sin red, basado en heurísticas.

Es el default cuando no hay `GEMINI_API_KEY`, así que el proyecto arranca y se
demuestra sin credenciales, y los tests corren sin salir a internet.

No pretende ser bueno: reformatea las notas y detecta patrones léxicos. Lo que sí
garantiza es devolver un `SalidaIA` válido con la misma forma que devolvería
Gemini, que es lo que necesita el frontend para desarrollarse en paralelo. La
respuesta viaja con `proveedor: "mock"` para que nunca se confunda con la real.
"""

import re

from app.models.enums import CalidadVinculo, Genero, Prioridad, RolNodo, TipoVinculo
from app.schemas.ia import AlertaIA, EntidadIA, SalidaIA, TagIA

# tag -> palabras que lo disparan
TEMAS: dict[str, tuple[str, ...]] = {
    "ansiedad": ("ansiedad", "ansios", "angustia", "angustiad", "panico", "pánico", "nervios"),
    "animo": ("triste", "tristeza", "bajon", "bajón", "desganad", "llorar", "llanto"),
    "trabajo": ("trabajo", "laboral", "jefe", "jefa", "oficina", "empleo", "despido", "renunc"),
    "familia-de-origen": ("mama", "mamá", "papa", "papá", "madre", "padre", "hermano", "hermana"),
    "pareja": ("pareja", "novio", "novia", "marido", "esposa", "esposo", "matrimonio"),
    "sueño": ("dormir", "duerme", "insomnio", "sueño", "despierta"),
    "duelo": ("duelo", "murio", "murió", "falleci", "perdida", "pérdida"),
    "autoestima": ("autoestima", "no sirvo", "no puedo", "inutil", "inútil", "culpa"),
    "limites": ("limite", "límite", "decir que no", "se aprovech"),
    "encuadre": ("sesion", "sesión", "espaciar", "frecuencia", "horario", "honorarios"),
}

# patrón -> (etiqueta canónica, rol, género, vínculo con la persona consultante)
PERSONAS: tuple[tuple[str, str, RolNodo, Genero, TipoVinculo], ...] = (
    (r"\b(mam[aá]|madre|vieja)\b", "Mamá", RolNodo.MADRE, Genero.FEMENINO, TipoVinculo.FILIAL),
    (r"\b(pap[aá]|padre|viejo)\b", "Papá", RolNodo.PADRE, Genero.MASCULINO, TipoVinculo.FILIAL),
    (r"\bhermana\b", "Hermana", RolNodo.HERMANO, Genero.FEMENINO, TipoVinculo.HERMANO),
    (r"\bhermano\b", "Hermano", RolNodo.HERMANO, Genero.MASCULINO, TipoVinculo.HERMANO),
    (r"\babuela\b", "Abuela", RolNodo.ABUELO, Genero.FEMENINO, TipoVinculo.FILIAL),
    (r"\babuelo\b", "Abuelo", RolNodo.ABUELO, Genero.MASCULINO, TipoVinculo.FILIAL),
    (r"\b(jefa)\b", "Jefa", RolNodo.LABORAL, Genero.FEMENINO, TipoVinculo.LABORAL),
    (r"\b(jefe)\b", "Jefe", RolNodo.LABORAL, Genero.MASCULINO, TipoVinculo.LABORAL),
    (r"\b(novia|esposa)\b", "Pareja", RolNodo.PAREJA, Genero.FEMENINO, TipoVinculo.PAREJA),
    (r"\b(novio|marido|esposo)\b", "Pareja", RolNodo.PAREJA, Genero.MASCULINO, TipoVinculo.PAREJA),
    (r"\bpareja\b", "Pareja", RolNodo.PAREJA, Genero.DESCONOCIDO, TipoVinculo.PAREJA),
    (r"\bhija\b", "Hija", RolNodo.HIJO, Genero.FEMENINO, TipoVinculo.PARENTAL),
    (r"\bhijo\b", "Hijo", RolNodo.HIJO, Genero.MASCULINO, TipoVinculo.PARENTAL),
    (r"\bamiga\b", "Amiga", RolNodo.AMIGO, Genero.FEMENINO, TipoVinculo.AMISTAD),
    (r"\bamigo\b", "Amigo", RolNodo.AMIGO, Genero.MASCULINO, TipoVinculo.AMISTAD),
)

CONFLICTO = ("pele", "discut", "discusion", "discusión", "grit", "conflicto", "bronca", "enoj")
CERCANIA = ("extrañ", "cariñ", "apoy", "cerca", "acompañ", "agradec")
DISTANCIA = ("no habla", "distante", "lejos", "nunca se mete", "no aparece", "ausente")

# Frases que marcan algo a retomar en la próxima sesión.
CUES_ALERTA = ("pregunta si", "quiere saber", "preguntar", "retomar", "recordar", "pendiente",
               "avisar", "traer", "chequear", "confirmar")
CUES_ALERTA_ALTA = ("riesgo", "urgente", "no puede mas", "no puede más", "crisis")


def _dividir(notas: str) -> list[str]:
    """Separa las notas en unidades: un bullet por línea, o frases si es prosa."""
    lineas = [
        re.sub(r"^[\s\-\*•·]+", "", linea).strip()
        for linea in notas.splitlines()
        if linea.strip()
    ]
    if len(lineas) > 1:
        return [linea for linea in lineas if linea]
    return [frase.strip() for frase in re.split(r"(?<=[.;])\s+", notas.strip()) if frase.strip()]


def _calidad(fragmento: str) -> CalidadVinculo:
    bajo = fragmento.lower()
    if any(palabra in bajo for palabra in CONFLICTO):
        return CalidadVinculo.CONFLICTIVO
    if any(palabra in bajo for palabra in DISTANCIA):
        return CalidadVinculo.DISTANTE
    if any(palabra in bajo for palabra in CERCANIA):
        return CalidadVinculo.CERCANO
    return CalidadVinculo.NEUTRAL


class MockIA:
    """Implementa `ProveedorIA` sin salir a la red."""

    nombre = "mock"
    modelo = "heuristico-v1"

    async def procesar(self, notas: str, contexto=None) -> SalidaIA:  # noqa: ANN001
        unidades = _dividir(notas)
        bajo = notas.lower()

        tags = [
            TagIA(tag=tag, relevancia=round(min(1.0, 0.4 + 0.2 * _cuenta(bajo, claves)), 2))
            for tag, claves in TEMAS.items()
            if _cuenta(bajo, claves)
        ]
        tags.sort(key=lambda t: t.relevancia, reverse=True)

        entidades = self._entidades(unidades)
        alertas = self._alertas(unidades)

        return SalidaIA(
            resumen_clinico=self._resumen(unidades),
            temas_principales=[tag.tag for tag in tags[:4]],
            tags=tags,
            entidades=entidades,
            alertas_proxima_sesion=alertas,
            estado_emocional_percibido=self._estado(bajo),
        )

    def _entidades(self, unidades: list[str]) -> list[EntidadIA]:
        vistas: dict[str, EntidadIA] = {}
        for unidad in unidades:
            for patron, etiqueta, rol, genero, vinculo in PERSONAS:
                if not re.search(patron, unidad, flags=re.IGNORECASE):
                    continue
                if etiqueta in vistas:
                    continue
                vistas[etiqueta] = EntidadIA(
                    etiqueta=etiqueta,
                    rol=rol,
                    genero=genero,
                    contexto=unidad,
                    vinculo_con_paciente=vinculo,
                    calidad_vinculo=_calidad(unidad),
                )
        return list(vistas.values())

    def _alertas(self, unidades: list[str]) -> list[AlertaIA]:
        alertas: list[AlertaIA] = []
        for unidad in unidades:
            bajo = unidad.lower()
            if any(cue in bajo for cue in CUES_ALERTA_ALTA):
                alertas.append(AlertaIA(texto=unidad, prioridad=Prioridad.ALTA))
            elif any(cue in bajo for cue in CUES_ALERTA):
                alertas.append(AlertaIA(texto=unidad, prioridad=Prioridad.MEDIA))
        return alertas

    def _resumen(self, unidades: list[str]) -> str:
        if not unidades:
            return ""
        cuerpo = "; ".join(unidad.rstrip(".") for unidad in unidades)
        return f"La persona consultante refiere: {cuerpo}."

    def _estado(self, bajo: str) -> str:
        for estado, claves in (
            ("angustia", ("angustia", "angustiad")),
            ("ansiedad", ("ansiedad", "ansios")),
            ("tristeza", ("triste", "llor")),
            ("enojo", ("enoj", "bronca")),
            ("alivio", ("tranquil", "mejor", "alivi")),
        ):
            if any(clave in bajo for clave in claves):
                return estado
        return ""


def _cuenta(texto: str, claves: tuple[str, ...]) -> int:
    return sum(texto.count(clave) for clave in claves)
