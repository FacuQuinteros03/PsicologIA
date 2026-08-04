"""Configuración de los tests.

Las variables de entorno se fijan **antes** de importar la app: `app.core.config`
instancia `Settings` al importarse, así que después ya sería tarde.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
# Fuerza el proveedor sin red aunque el entorno tenga una GEMINI_API_KEY cargada.
os.environ["IA_PROVIDER"] = "mock"

import uuid  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.deps import get_terapeuta_actual  # noqa: E402
from app.core.loop import configurar_event_loop  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Terapeuta  # noqa: E402

# Los tests de hoy no tocan la base, pero cuando se agreguen los de integración
# van a necesitar el selector loop en Windows.
configurar_event_loop()

TERAPEUTA_TEST = Terapeuta(
    id=uuid.UUID("00000000-0000-4000-8000-000000000001"),
    email="test@psicoia.local",
    nombre_completo="Terapeuta de Test",
)


@pytest.fixture
async def cliente() -> AsyncClient:
    """Cliente HTTP contra la app, con el terapeuta actual mockeado.

    No se toca la base: los tests de este archivo ejercitan el camino stateless
    de `/procesar-notas`, que no abre conexión.
    """
    app.dependency_overrides[get_terapeuta_actual] = lambda: TERAPEUTA_TEST
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://test") as cli:
        yield cli
    app.dependency_overrides.clear()
