"""Configuración de la app, leída de variables de entorno / `.env`."""

import uuid
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "PsicoIA API"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- Base de datos ---
    database_url: str
    db_echo: bool = False
    # Neon y Supabase entregan por defecto una URL que pasa por PgBouncer en modo
    # transaction, donde los prepared statements del servidor rompen. Desactivarlos
    # cuesta muy poco en este workload y evita errores intermitentes difíciles de leer.
    db_prepared_statements: bool = False

    # --- IA ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    ia_provider: Literal["auto", "mock", "gemini"] = "auto"

    # --- Auth (provisorio) ---
    # Mientras no haya login, `get_terapeuta_actual()` resuelve contra este ID.
    # Cuando entre el JWT, esta setting se borra y no cambia nada más.
    terapeuta_seed_id: uuid.UUID = uuid.UUID("00000000-0000-4000-8000-000000000001")

    @field_validator("database_url")
    @classmethod
    def _normalizar_driver(cls, v: str) -> str:
        """Fuerza el driver psycopg 3 sin importar en qué forma se pegue la URL.

        Neon entrega `postgresql://...` y algunos proveedores todavía `postgres://...`;
        SQLAlchemy necesita el sufijo explícito para elegir el dialecto async.
        """
        if "+" in v.split("://", 1)[0]:
            return v
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    @property
    def proveedor_ia_efectivo(self) -> Literal["mock", "gemini"]:
        """Resuelve `auto`: sin API key el sistema cae al mock en vez de fallar."""
        if self.ia_provider != "auto":
            return self.ia_provider
        return "gemini" if self.gemini_api_key.strip() else "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # los valores vienen del entorno


settings = get_settings()
