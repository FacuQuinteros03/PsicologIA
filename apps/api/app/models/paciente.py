"""Tabla `pacientes`."""

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin, tipo_enum
from app.models.enums import EstadoPaciente

if TYPE_CHECKING:
    from app.models.genograma import ConexionGenograma, NodoGenograma
    from app.models.sesion import Sesion
    from app.models.terapeuta import Terapeuta


class Paciente(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "pacientes"

    terapeuta_id: uuid.UUID = Field(
        foreign_key="terapeutas.id",
        index=True,
        ondelete="CASCADE",
    )

    nombre: str = Field(max_length=120)
    apellido: str = Field(max_length=120)
    fecha_nacimiento: date | None = Field(default=None)
    email: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    motivo_consulta: str | None = Field(default=None, sa_type=Text)

    estado: EstadoPaciente = Field(
        default=EstadoPaciente.ACTIVO,
        sa_type=tipo_enum(EstadoPaciente, "ck_pacientes_estado"),
    )

    # Campos que todavía no merecen columna propia (obra social, encuadre, tarifa...).
    datos: dict[str, Any] = Field(
        default_factory=dict,
        sa_type=MutableDict.as_mutable(JSONB),
        sa_column_kwargs={"server_default": text("'{}'::jsonb")},
    )

    terapeuta: "Terapeuta" = Relationship(back_populates="pacientes")
    sesiones: list["Sesion"] = Relationship(
        back_populates="paciente",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
    nodos: list["NodoGenograma"] = Relationship(
        back_populates="paciente",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
    conexiones: list["ConexionGenograma"] = Relationship(
        back_populates="paciente",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()
