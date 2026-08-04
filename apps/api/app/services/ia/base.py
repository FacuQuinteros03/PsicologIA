"""Contrato de los proveedores de IA."""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.schemas.ia import SalidaIA


class ErrorProveedorIA(RuntimeError):
    """Falló la llamada al proveedor o la respuesta no respetó el schema.

    Lleva `crudo` cuando hubo respuesta pero no se pudo parsear, para poder
    guardarla en `sesiones.ia_payload` y auditar qué devolvió el modelo.
    """

    def __init__(self, mensaje: str, crudo: str | None = None) -> None:
        super().__init__(mensaje)
        self.crudo = crudo


@dataclass(frozen=True)
class ContextoPaciente:
    """Lo que sabemos del paciente y le sirve al modelo para no inventar.

    `etiquetas_conocidas` es la pieza clave: son los nodos que ya existen en el
    genograma. Pasárselas evita que el modelo devuelva "mi madre" cuando en el
    canvas esa persona ya se llama "Mamá", que es lo que rompería el upsert.
    """

    nombre: str | None = None
    motivo_consulta: str | None = None
    etiquetas_conocidas: tuple[str, ...] = ()
    tags_previos: tuple[str, ...] = field(default=())


@runtime_checkable
class ProveedorIA(Protocol):
    nombre: str
    modelo: str

    async def procesar(self, notas: str, contexto: ContextoPaciente | None = None) -> SalidaIA:
        """Convierte notas crudas en la estructura clínica. Levanta `ErrorProveedorIA`."""
        ...
