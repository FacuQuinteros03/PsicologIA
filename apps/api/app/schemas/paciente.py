"""Contratos HTTP de pacientes.

Separados de `models/`: la respuesta pública nunca expone `terapeuta_id` ni el
JSONB interno `datos`.

Hay cuatro modelos y cada uno tiene su motivo:
- `PacienteCrear`     lo que se puede mandar al crear (sin `estado`: nace activo).
- `PacienteActualizar` todo opcional, semántica PATCH: lo que no viene no se toca.
- `PacienteRespuesta`  fila del listado, liviana.
- `PacienteDetalle`    ficha completa, con los contadores que necesita la UI.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoPaciente, Frecuencia, Genero, Modalidad, Prioridad


class PacienteBase(BaseModel):
    """Campos editables. Compartidos por creación y actualización."""

    # --- Identificación ---
    nombre: str = Field(min_length=1, max_length=120)
    apellido: str = Field(min_length=1, max_length=120)
    documento: str | None = Field(default=None, max_length=30)
    fecha_nacimiento: date | None = None
    genero: Genero = Genero.DESCONOCIDO
    ocupacion: str | None = Field(default=None, max_length=150)

    # --- Contacto ---
    email: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    contacto_emergencia: str | None = Field(default=None, max_length=200)
    telefono_emergencia: str | None = Field(default=None, max_length=50)

    # --- Cobertura ---
    obra_social: str | None = Field(default=None, max_length=150)
    numero_afiliado: str | None = Field(default=None, max_length=80)

    # --- Encuadre ---
    motivo_consulta: str | None = None
    fecha_inicio: date | None = None
    modalidad: Modalidad = Modalidad.PRESENCIAL
    frecuencia: Frecuencia = Frecuencia.SEMANAL
    honorarios: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)

    notas_administrativas: str | None = None


class PacienteCrear(PacienteBase):
    """`estado` no se acepta: todo paciente nuevo nace `activo`."""


class PacienteActualizar(BaseModel):
    """Todos los campos opcionales.

    El endpoint usa `exclude_unset`, así que mandar `{"telefono": null}` borra el
    teléfono, mientras que omitirlo lo deja como está. Es la diferencia entre
    "ponelo en vacío" y "no lo toques".
    """

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    apellido: str | None = Field(default=None, min_length=1, max_length=120)
    documento: str | None = Field(default=None, max_length=30)
    fecha_nacimiento: date | None = None
    genero: Genero | None = None
    ocupacion: str | None = Field(default=None, max_length=150)

    email: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    contacto_emergencia: str | None = Field(default=None, max_length=200)
    telefono_emergencia: str | None = Field(default=None, max_length=50)

    obra_social: str | None = Field(default=None, max_length=150)
    numero_afiliado: str | None = Field(default=None, max_length=80)

    motivo_consulta: str | None = None
    fecha_inicio: date | None = None
    modalidad: Modalidad | None = None
    frecuencia: Frecuencia | None = None
    honorarios: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)

    # Acá sí se puede cambiar: dar de alta, pausar o archivar un tratamiento.
    estado: EstadoPaciente | None = None
    notas_administrativas: str | None = None


class PacienteRespuesta(BaseModel):
    """Fila del listado. Sin los campos administrativos, que no se muestran ahí."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    apellido: str
    documento: str | None
    fecha_nacimiento: date | None
    edad: int | None
    genero: Genero
    email: str | None
    telefono: str | None
    motivo_consulta: str | None
    estado: EstadoPaciente
    modalidad: Modalidad
    frecuencia: Frecuencia
    created_at: datetime


class PacienteDetalle(PacienteRespuesta):
    """Ficha completa, para la pantalla de detalle y el formulario de edición."""

    ocupacion: str | None
    contacto_emergencia: str | None
    telefono_emergencia: str | None
    obra_social: str | None
    numero_afiliado: str | None
    fecha_inicio: date | None
    honorarios: Decimal | None
    notas_administrativas: str | None
    updated_at: datetime

    # Contadores de lo que cuelga del paciente. La UI los usa para el resumen de
    # la ficha y, sobre todo, para decir exactamente qué se pierde al borrar.
    total_sesiones: int = 0
    total_nodos: int = 0
    recordatorios_pendientes: int = 0


class RecordatorioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # None en los que carga el terapeuta a mano: no vienen de ninguna sesión.
    sesion_id: uuid.UUID | None
    texto: str
    prioridad: Prioridad
    resuelto: bool
    resuelto_at: datetime | None
    created_at: datetime


class RecordatorioCrear(BaseModel):
    """Alta manual. No todo lo que hay que recordar sale del procesamiento de notas."""

    texto: str = Field(min_length=1, max_length=1000)
    prioridad: Prioridad = Prioridad.MEDIA


class RecordatorioActualizar(BaseModel):
    """Todo opcional: lo que no se manda queda intacto.

    El caso frecuente es `{"resuelto": true}` al cerrar el punto en sesión, pero
    también se puede corregir el texto o la prioridad de uno que infirió la IA.
    """

    texto: str | None = Field(default=None, min_length=1, max_length=1000)
    prioridad: Prioridad | None = None
    resuelto: bool | None = None
