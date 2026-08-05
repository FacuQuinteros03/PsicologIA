"""Tabla `pacientes`."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Numeric, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin, tipo_enum
from app.models.enums import EstadoPaciente, Frecuencia, Genero, Modalidad

if TYPE_CHECKING:
    from app.models.genograma import ConexionGenograma, NodoGenograma
    from app.models.sesion import Sesion
    from app.models.terapeuta import Terapeuta


class Paciente(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "pacientes"
    __table_args__ = (
        # Un terapeuta no puede tener dos pacientes con el mismo documento.
        # Postgres admite múltiples NULL en un UNIQUE, así que los pacientes sin
        # documento cargado no chocan entre sí.
        UniqueConstraint("terapeuta_id", "documento", name="uq_paciente_terapeuta_documento"),
    )

    terapeuta_id: uuid.UUID = Field(
        foreign_key="terapeutas.id",
        index=True,
        ondelete="CASCADE",
    )

    # --- Identificación ---
    nombre: str = Field(max_length=120)
    apellido: str = Field(max_length=120)
    documento: str | None = Field(default=None, max_length=30)
    fecha_nacimiento: date | None = Field(default=None)
    # `server_default` además del default de Python: sin él, agregar una columna
    # NOT NULL sobre una tabla que ya tiene filas falla en Postgres, y además
    # cubre los INSERT que no pasan por el ORM.
    genero: Genero = Field(
        default=Genero.DESCONOCIDO,
        sa_type=tipo_enum(Genero, "ck_pacientes_genero"),
        sa_column_kwargs={"server_default": Genero.DESCONOCIDO.value},
    )
    ocupacion: str | None = Field(default=None, max_length=150)

    # --- Contacto ---
    email: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    contacto_emergencia: str | None = Field(default=None, max_length=200)
    telefono_emergencia: str | None = Field(default=None, max_length=50)

    # --- Cobertura ---
    obra_social: str | None = Field(default=None, max_length=150)
    numero_afiliado: str | None = Field(default=None, max_length=80)

    # --- Encuadre clínico ---
    motivo_consulta: str | None = Field(default=None, sa_type=Text)
    fecha_inicio: date | None = Field(default=None)
    modalidad: Modalidad = Field(
        default=Modalidad.PRESENCIAL,
        sa_type=tipo_enum(Modalidad, "ck_pacientes_modalidad"),
        sa_column_kwargs={"server_default": Modalidad.PRESENCIAL.value},
    )
    frecuencia: Frecuencia = Field(
        default=Frecuencia.SEMANAL,
        sa_type=tipo_enum(Frecuencia, "ck_pacientes_frecuencia"),
        sa_column_kwargs={"server_default": Frecuencia.SEMANAL.value},
    )
    # Numeric y no float: con dinero, el binario flotante acumula error.
    honorarios: Decimal | None = Field(default=None, sa_type=Numeric(10, 2))

    estado: EstadoPaciente = Field(
        default=EstadoPaciente.ACTIVO,
        sa_type=tipo_enum(EstadoPaciente, "ck_pacientes_estado"),
    )

    # Administrativo, no clínico: lo clínico va en las sesiones.
    notas_administrativas: str | None = Field(default=None, sa_type=Text)

    # Extensión sin migración para lo que aparezca y no merezca columna.
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

    @property
    def edad(self) -> int | None:
        """Edad en años cumplidos. Se calcula, no se guarda: se desactualizaría."""
        if self.fecha_nacimiento is None:
            return None
        hoy = date.today()
        cumplio = (hoy.month, hoy.day) >= (
            self.fecha_nacimiento.month,
            self.fecha_nacimiento.day,
        )
        return hoy.year - self.fecha_nacimiento.year - (0 if cumplio else 1)
