import asyncio
from logging.config import fileConfig
from typing import Any

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context
from app.core.config import settings
from app.core.loop import configurar_event_loop

# Importar el paquete registra todas las tablas en SQLModel.metadata.
import app.models  # noqa: F401  isort:skip

# Antes de cualquier asyncio.run(): psycopg async no corre sobre ProactorEventLoop.
configurar_event_loop()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# La URL vive en `.env`, no en alembic.ini: es una credencial.
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = SQLModel.metadata

# Índices creados a mano con `op.execute` porque son expresiones que el
# autogenerate de Alembic no compara de forma estable — sin esta lista los
# detectaría como "sobrantes" y los borraría en cada migración nueva.
INDICES_MANUALES = {"ix_sesiones_fts"}


def include_object(
    obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any
) -> bool:
    if type_ == "index" and name in INDICES_MANUALES:
        return False

    # Los CHECK de los enums los emite SQLAlchemy junto con la columna (ver
    # `tipo_enum` en models/base.py), pero NO quedan declarados en el metadata.
    # Alembic los encuentra en la base, no los ve del otro lado, y los marca
    # para borrar: cada migración nueva vendría con un `drop_constraint` de
    # todas las validaciones de enum. Por eso quedan fuera del diff.
    #
    # Contrapartida asumida: si algún día agregás un CheckConstraint declarado a
    # mano, el autogenerate no lo va a emitir y hay que escribirlo en la
    # migración. Es más barato que pelear con los falsos positivos.
    return type_ != "check_constraint"


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse (`alembic upgrade head --sql`)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
