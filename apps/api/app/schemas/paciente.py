"""Contratos HTTP de pacientes.

Separados de `models/`: la respuesta pública no expone `terapeuta_id` ni `datos`.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoPaciente, Prioridad


class PacienteCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    apellido: str = Field(min_length=1, max_length=120)
    fecha_nacimiento: date | None = None
    email: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    motivo_consulta: str | None = None


class PacienteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    apellido: str
    fecha_nacimiento: date | None
    email: str | None
    telefono: str | None
    motivo_consulta: str | None
    estado: EstadoPaciente
    created_at: datetime


class RecordatorioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sesion_id: uuid.UUID
    texto: str
    prioridad: Prioridad
    resuelto: bool
    created_at: datetime
