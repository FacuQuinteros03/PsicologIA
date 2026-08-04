"""Punto de entrada de la API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as router_v1
from app.core.config import settings
from app.core.database import engine

# Importar el paquete registra todos los modelos en el metadata de SQLModel.
import app.models  # noqa: F401  isort:skip


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Copiloto terapéutico: notas asistidas por IA y genograma interactivo.",
    lifespan=lifespan,
    # En producción no se publica el esquema: /docs y /openapi.json le entregan a
    # cualquiera el mapa completo de la API, incluidos los nombres de campo del
    # historial clínico. En desarrollo siguen disponibles.
    docs_url=None if settings.es_produccion else "/docs",
    redoc_url=None if settings.es_produccion else "/redoc",
    openapi_url=None if settings.es_produccion else "/openapi.json",
)

# `allow_origins` sale de la config y por defecto está vacío. Nunca poner `["*"]`
# junto con `allow_credentials=True`: los navegadores lo rechazan, y si se
# forzara, cualquier sitio podría hacer requests autenticados contra la API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(router_v1, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "entorno": settings.environment,
        "proveedor_ia": settings.proveedor_ia_efectivo,
    }
