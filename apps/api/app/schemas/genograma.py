"""Contratos HTTP del genograma.

`GenogramaRespuesta` está pensado para que el frontend lo pase casi directo a
React Flow: `nodos` -> `nodes`, `conexiones` -> `edges`.
"""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CalidadVinculo, Genero, RolNodo, TipoVinculo


class Posicion(BaseModel):
    """Payload del `onNodeDragStop` de React Flow."""

    pos_x: float
    pos_y: float


class NodoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    etiqueta: str
    nombre: str | None
    rol: RolNodo
    genero: Genero
    fecha_nacimiento: date | None
    fallecido: bool
    pos_x: float
    pos_y: float
    notas: str | None
    es_indice: bool


class ConexionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    origen_id: uuid.UUID
    destino_id: uuid.UUID
    tipo_vinculo: TipoVinculo
    calidad_vinculo: CalidadVinculo | None
    etiqueta: str | None


class GenogramaRespuesta(BaseModel):
    paciente_id: uuid.UUID
    nodos: list[NodoRespuesta]
    conexiones: list[ConexionRespuesta]


class NodoCrear(BaseModel):
    etiqueta: str = Field(min_length=1, max_length=120)
    nombre: str | None = Field(default=None, max_length=200)
    rol: RolNodo = RolNodo.OTRO
    genero: Genero = Genero.DESCONOCIDO
    pos_x: float = 0.0
    pos_y: float = 0.0
    notas: str | None = None


class ConexionCrear(BaseModel):
    origen_id: uuid.UUID
    destino_id: uuid.UUID
    tipo_vinculo: TipoVinculo = TipoVinculo.OTRO
    calidad_vinculo: CalidadVinculo | None = None
    etiqueta: str | None = Field(default=None, max_length=120)


class MencionSesion(BaseModel):
    """Una sesión donde aparece un nodo — lo que alimenta el panel lateral."""

    sesion_id: uuid.UUID
    fecha_sesion: str
    menciones: int
    contexto: str | None
    resumen_ia: str | None
    tags: list[str]
