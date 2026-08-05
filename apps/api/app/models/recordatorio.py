"""Tabla `recordatorios` — alertas para la próxima sesión.

Es tabla propia y no un array JSONB dentro de `sesiones` porque tiene estado
mutable (`resuelto`) y se consulta como "pendientes del paciente", cruzando todas
sus sesiones. Mutar e indexar el estado de un elemento dentro de un JSONB sería
dolor evitable.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Index, Text, text
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship

from app.models.base import UUIDMixin, ahora_utc, tipo_enum
from app.models.enums import Prioridad

if TYPE_CHECKING:
    from app.models.sesion import Sesion


class Recordatorio(UUIDMixin, table=True):
    __tablename__ = "recordatorios"
    __table_args__ = (
        # Índice parcial: la consulta real es siempre "qué me quedó pendiente".
        Index(
            "ix_recordatorios_pendientes",
            "paciente_id",
            postgresql_where=text("resuelto = false"),
        ),
    )

    # Nullable: es la sesión donde SE ORIGINÓ el recordatorio, y los que carga
    # el terapeuta a mano no vienen de ninguna. El dueño del recordatorio es el
    # paciente, no la sesión.
    sesion_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="sesiones.id",
        index=True,
        ondelete="CASCADE",
    )
    # Denormalizado a propósito: evita el join con `sesiones` en la consulta
    # más frecuente de la pantalla de paciente. Indexado porque el índice parcial
    # de abajo no sirve para el cascade de borrado de un paciente.
    paciente_id: uuid.UUID = Field(
        foreign_key="pacientes.id",
        index=True,
        ondelete="CASCADE",
    )

    texto: str = Field(sa_type=Text)
    prioridad: Prioridad = Field(
        default=Prioridad.MEDIA,
        sa_type=tipo_enum(Prioridad, "ck_recordatorios_prioridad"),
    )
    resuelto: bool = Field(default=False)
    resuelto_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    created_at: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
    )

    # `Optional["Sesion"]` y NO `"Sesion | None"`: SQLAlchemy resuelve la
    # anotación de un Relationship como nombre de clase, y la union escrita con
    # `|` la busca literalmente como si fuera una clase llamada "Sesion | None".
    sesion: Optional["Sesion"] = Relationship(back_populates="recordatorios")  # noqa: UP045
