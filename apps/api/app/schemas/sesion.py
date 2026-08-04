"""Contratos HTTP de sesiones."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoIA


class SesionCrear(BaseModel):
    paciente_id: uuid.UUID
    notas_borrador: str = ""
    numero_sesion: int | None = None
    fecha_sesion: datetime | None = None


class SesionActualizar(BaseModel):
    """Guardado del borrador mientras el terapeuta tipea."""

    notas_borrador: str = Field(max_length=50_000)


class SesionResumen(BaseModel):
    """Fila del listado de historial. Sin `notas_borrador`: no hace falta en la lista."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fecha_sesion: datetime
    numero_sesion: int | None
    resumen_ia: str | None
    tags: list[str]
    estado_emocional: str | None
    ia_estado: EstadoIA


class SesionDetalle(SesionResumen):
    """Sesión completa. `ia_payload` queda fuera: es para auditoría interna."""

    paciente_id: uuid.UUID
    notas_borrador: str
    ia_modelo: str | None
    ia_procesado_at: datetime | None


class TagConteo(BaseModel):
    tag: str
    cantidad: int
