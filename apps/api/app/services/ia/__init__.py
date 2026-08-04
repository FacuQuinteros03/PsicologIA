"""Selección del proveedor de IA."""

from functools import lru_cache

from app.core.config import settings
from app.services.ia.base import ContextoPaciente, ErrorProveedorIA, ProveedorIA
from app.services.ia.mock import MockIA

__all__ = ["ContextoPaciente", "ErrorProveedorIA", "ProveedorIA", "obtener_proveedor"]


@lru_cache
def obtener_proveedor() -> ProveedorIA:
    """Devuelve el proveedor configurado.

    `GeminiIA` se importa adentro a propósito: instanciar el cliente sin API key
    falla, y con `IA_PROVIDER=mock` no hay razón para tocar ese módulo.
    """
    if settings.proveedor_ia_efectivo == "gemini":
        from app.services.ia.gemini import GeminiIA

        return GeminiIA(api_key=settings.gemini_api_key, modelo=settings.gemini_model)
    return MockIA()
