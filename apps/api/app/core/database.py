"""Engine y sesión async de SQLAlchemy/SQLModel."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

_connect_args: dict[str, Any] = {}
if not settings.db_prepared_statements:
    # psycopg 3: None desactiva por completo los prepared statements del servidor.
    _connect_args["prepare_threshold"] = None

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    # Postgres serverless cierra conexiones ociosas; sin pre_ping la primera query
    # después de un rato falla con "connection closed".
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=5,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    # Sin esto, leer un atributo después del commit dispara un refresh implícito
    # que en async explota con MissingGreenlet.
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: una sesión por request."""
    async with AsyncSessionLocal() as session:
        yield session
