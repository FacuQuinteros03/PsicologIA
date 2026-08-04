"""Mixins y helpers compartidos por todos los modelos."""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TypeVar

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel

E = TypeVar("E", bound=Enum)


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def tipo_enum(enum_cls: type[E], nombre: str) -> SAEnum:
    """Construye el tipo de columna para un enum del dominio.

    `native_enum=False` produce VARCHAR + CHECK en vez de un tipo ENUM nativo de
    Postgres: agregar un valor nuevo pasa a ser un cambio de constraint en lugar de
    un `ALTER TYPE`, que no es transaccional y complica los downgrades de Alembic.

    `values_callable` hace que se persista el *valor* del enum (`"activo"`) y no su
    nombre (`"ACTIVO"`), para que lo guardado coincida con lo que expone la API.

    Devuelve una instancia nueva en cada llamada: los tipos con constraint no se
    comparten entre tablas.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        name=nombre,
        values_callable=lambda e: [m.value for m in e],
    )


class UUIDMixin(SQLModel):
    """PK UUID generada en la app: permite armar grafos en memoria antes del INSERT."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class TimestampMixin(SQLModel):
    """`created_at` / `updated_at` con timezone.

    Se usa `sa_type` + `sa_column_kwargs` y no `sa_column`: un objeto `Column` sólo
    puede pertenecer a una tabla, así que compartirlo vía mixin rompería en la
    segunda clase que herede.
    """

    created_at: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
