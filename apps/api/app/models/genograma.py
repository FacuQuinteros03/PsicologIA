"""Tablas del genograma: `nodos_genograma` y `conexiones_genograma`."""

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin, tipo_enum
from app.models.enums import CalidadVinculo, Genero, RolNodo, TipoVinculo

if TYPE_CHECKING:
    from app.models.paciente import Paciente


class NodoGenograma(UUIDMixin, TimestampMixin, table=True):
    """Una persona de la red vincular del paciente."""

    __tablename__ = "nodos_genograma"
    __table_args__ = (
        # Permite que la extracción de entidades haga upsert por etiqueta en vez de
        # crear una "Mamá" nueva en cada sesión procesada.
        UniqueConstraint("paciente_id", "etiqueta", name="uq_nodo_paciente_etiqueta"),
    )

    paciente_id: uuid.UUID = Field(
        foreign_key="pacientes.id",
        index=True,
        ondelete="CASCADE",
    )

    # Cómo la nombra el paciente: "Mamá", "el jefe", "mi ex". Es la clave de
    # vinculación con lo que detecta la IA en las notas.
    etiqueta: str = Field(max_length=120)
    nombre: str | None = Field(default=None, max_length=200)

    rol: RolNodo = Field(default=RolNodo.OTRO, sa_type=tipo_enum(RolNodo, "ck_nodos_rol"))
    genero: Genero = Field(
        default=Genero.DESCONOCIDO,
        sa_type=tipo_enum(Genero, "ck_nodos_genero"),
    )

    fecha_nacimiento: date | None = Field(default=None)
    fallecido: bool = Field(default=False)
    fecha_fallecimiento: date | None = Field(default=None)

    # Posición en el canvas de React Flow. Se persiste en cada `onNodeDragStop`.
    pos_x: float = Field(default=0.0)
    pos_y: float = Field(default=0.0)

    notas: str | None = Field(default=None, sa_type=Text)
    # `true` sólo para el nodo que representa al propio paciente.
    es_indice: bool = Field(default=False)

    datos: dict[str, Any] = Field(
        default_factory=dict,
        sa_type=MutableDict.as_mutable(JSONB),
        sa_column_kwargs={"server_default": text("'{}'::jsonb")},
    )

    paciente: "Paciente" = Relationship(back_populates="nodos")


class ConexionGenograma(UUIDMixin, TimestampMixin, table=True):
    """Un vínculo entre dos nodos — el edge del grafo."""

    __tablename__ = "conexiones_genograma"
    __table_args__ = (
        UniqueConstraint(
            "origen_id", "destino_id", "tipo_vinculo", name="uq_conexion_origen_destino_tipo"
        ),
        CheckConstraint("origen_id <> destino_id", name="ck_conexion_no_autorreferente"),
    )

    # Denormalizado: permite traer todo el grafo del paciente en una sola query,
    # sin joins contra `nodos_genograma`.
    paciente_id: uuid.UUID = Field(
        foreign_key="pacientes.id",
        index=True,
        ondelete="CASCADE",
    )

    origen_id: uuid.UUID = Field(
        foreign_key="nodos_genograma.id",
        index=True,
        ondelete="CASCADE",
    )
    destino_id: uuid.UUID = Field(
        foreign_key="nodos_genograma.id",
        index=True,
        ondelete="CASCADE",
    )

    tipo_vinculo: TipoVinculo = Field(
        default=TipoVinculo.OTRO,
        sa_type=tipo_enum(TipoVinculo, "ck_conexiones_tipo_vinculo"),
    )
    calidad_vinculo: CalidadVinculo | None = Field(
        default=None,
        sa_type=tipo_enum(CalidadVinculo, "ck_conexiones_calidad_vinculo"),
    )
    etiqueta: str | None = Field(default=None, max_length=120)

    datos: dict[str, Any] = Field(
        default_factory=dict,
        sa_type=MutableDict.as_mutable(JSONB),
        sa_column_kwargs={"server_default": text("'{}'::jsonb")},
    )

    paciente: "Paciente" = Relationship(back_populates="conexiones")

    # Dos FKs apuntan a la misma tabla, así que hay que desambiguar cuál usa cada lado.
    origen: "NodoGenograma" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ConexionGenograma.origen_id]",
            "lazy": "selectin",
        }
    )
    destino: "NodoGenograma" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ConexionGenograma.destino_id]",
            "lazy": "selectin",
        }
    )
