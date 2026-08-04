"""Contrato del procesamiento de notas con IA.

Hay dos modelos a propósito:

- `SalidaIA` es **lo que el modelo tiene que generar**, y se le manda tal cual
  como `response_schema`.
- `NotasEstructuradas` es lo que devuelve la API: `SalidaIA` más la metadata que
  agregamos nosotros (proveedor, modelo, timestamp).

Detalle no obvio: en `SalidaIA` **ningún campo es opcional**. Un `str | None` de
Pydantic se serializa a `anyOf: [string, null]`, y el soporte de JSON Schema de
los proveedores de structured output es irregular con `anyOf`. Se usan valores
centinela (`""`, `OTRO`, `NEUTRAL`) y la conversión a `None` se hace de este lado.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import CalidadVinculo, Genero, Prioridad, RolNodo, TipoVinculo


class TagIA(BaseModel):
    tag: str = Field(
        description="Etiqueta temática en minúsculas, sin '#', separada con guiones. "
        "Ejemplos: 'ansiedad', 'duelo', 'familia-de-origen'."
    )
    relevancia: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Qué tan central fue el tema en la sesión, de 0 a 1.",
    )


class EntidadIA(BaseModel):
    """Una persona mencionada en las notas, candidata a nodo del genograma."""

    etiqueta: str = Field(
        description="Cómo la nombra el paciente, tal cual aparece en las notas: "
        "'Mamá', 'el jefe', 'mi ex'. Es la clave para vincular con el genograma."
    )
    nombre: str = Field(default="", description="Nombre propio si se menciona; vacío si no.")
    rol: RolNodo = Field(default=RolNodo.OTRO)
    genero: Genero = Field(default=Genero.DESCONOCIDO)
    contexto: str = Field(
        default="", description="Fragmento breve de la nota donde aparece la persona."
    )
    vinculo_con_paciente: TipoVinculo = Field(default=TipoVinculo.OTRO)
    calidad_vinculo: CalidadVinculo = Field(
        default=CalidadVinculo.NEUTRAL,
        description="Carga emocional del vínculo según lo relatado en la sesión.",
    )


class AlertaIA(BaseModel):
    texto: str = Field(description="Qué conviene retomar en la próxima sesión.")
    prioridad: Prioridad = Field(default=Prioridad.MEDIA)


class SalidaIA(BaseModel):
    """Lo que genera el modelo. Este schema es el que viaja como `response_format`."""

    resumen_clinico: str = Field(
        description="Reformulación de las notas en lenguaje clínico profesional, "
        "en tercera persona. No agrega información que no esté en las notas."
    )
    temas_principales: list[str] = Field(default_factory=list)
    tags: list[TagIA] = Field(default_factory=list)
    entidades: list[EntidadIA] = Field(default_factory=list)
    alertas_proxima_sesion: list[AlertaIA] = Field(default_factory=list)
    estado_emocional_percibido: str = Field(
        default="", description="Una o dos palabras. Vacío si las notas no lo permiten inferir."
    )


class NotasEstructuradas(SalidaIA):
    """Respuesta del endpoint: la salida del modelo más nuestra metadata."""

    proveedor: str
    modelo: str
    procesado_en: datetime
    sesion_id: uuid.UUID | None = None
    persistido: bool = False


class ProcesarNotasRequest(BaseModel):
    notas: str = Field(min_length=10, max_length=20_000)
    paciente_id: uuid.UUID | None = Field(
        default=None,
        description="Si viene, se le pasa al modelo el contexto del paciente "
        "(motivo de consulta y etiquetas del genograma ya existentes) para que "
        "reutilice 'Mamá' en lugar de inventar 'mi madre'.",
    )
    sesion_id: uuid.UUID | None = None
    persistir: bool = Field(
        default=False,
        description="Si es true, escribe el resultado en la sesión, hace upsert de "
        "los nodos del genograma y crea los recordatorios. Requiere `sesion_id`.",
    )

    @model_validator(mode="after")
    def _persistir_requiere_sesion(self) -> "ProcesarNotasRequest":
        if self.persistir and self.sesion_id is None:
            raise ValueError("`persistir=true` requiere `sesion_id`.")
        return self
