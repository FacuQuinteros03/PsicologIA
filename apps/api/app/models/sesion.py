"""Tabla `sesiones` — el corazón del producto."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import ARRAY, DateTime, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin, ahora_utc, tipo_enum
from app.models.enums import EstadoIA

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.recordatorio import Recordatorio


class Sesion(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "sesiones"
    __table_args__ = (
        # Listado del historial: siempre por paciente y de la más reciente hacia atrás.
        Index("ix_sesiones_paciente_fecha", "paciente_id", text("fecha_sesion DESC")),
        # Filtro temático: `tags && ARRAY['ansiedad']`.
        Index("ix_sesiones_tags", "tags", postgresql_using="gin"),
        # El índice full-text en español se crea en la migración (es una expresión
        # que Alembic no autogenera de forma estable). Ver `alembic/versions/`.
    )

    # Sin `index=True`: `ix_sesiones_paciente_fecha` ya lo cubre como prefijo
    # izquierdo, un índice suelto sobre la misma columna sería peso muerto.
    paciente_id: uuid.UUID = Field(
        foreign_key="pacientes.id",
        ondelete="CASCADE",
    )

    fecha_sesion: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
    )
    numero_sesion: int | None = Field(default=None)

    # Lo que el terapeuta tipea en vivo. Es la fuente de verdad y nunca se
    # sobrescribe con la salida del modelo: reprocesar la IA no puede perder
    # lo que la persona efectivamente escribió.
    notas_borrador: str = Field(default="", sa_type=Text)

    resumen_ia: str | None = Field(default=None, sa_type=Text)

    tags: list[str] = Field(
        default_factory=list,
        # MutableList hace que `sesion.tags.append(...)` marque la fila como sucia;
        # con un ARRAY plano SQLAlchemy no detecta la mutación in-place.
        sa_type=MutableList.as_mutable(ARRAY(Text())),
        sa_column_kwargs={"server_default": text("'{}'::text[]")},
    )

    estado_emocional: str | None = Field(default=None, max_length=120)

    # --- Trazabilidad del procesamiento IA ---
    ia_estado: EstadoIA = Field(
        default=EstadoIA.PENDIENTE,
        sa_type=tipo_enum(EstadoIA, "ck_sesiones_ia_estado"),
    )
    ia_modelo: str | None = Field(default=None, max_length=100)
    ia_procesado_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    # Respuesta cruda del proveedor: permite auditar qué generó el modelo y
    # reprocesar el parseo sin volver a pagar la llamada.
    ia_payload: dict[str, Any] | None = Field(default=None, sa_type=JSONB)

    paciente: "Paciente" = Relationship(back_populates="sesiones")
    recordatorios: list["Recordatorio"] = Relationship(
        back_populates="sesion",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
