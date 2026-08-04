"""Registro central de modelos.

Importar todo desde acá cumple dos funciones: resuelve las referencias por string
de las `Relationship` al configurar los mappers, y le da a Alembic el metadata
completo para el autogenerate. Si un modelo no se importa acá, su tabla no existe
para las migraciones.
"""

from app.models.enums import (
    CalidadVinculo,
    EstadoIA,
    EstadoPaciente,
    Genero,
    Prioridad,
    RolNodo,
    TipoVinculo,
)
from app.models.genograma import ConexionGenograma, NodoGenograma
from app.models.links import SesionNodoLink
from app.models.paciente import Paciente
from app.models.recordatorio import Recordatorio
from app.models.sesion import Sesion
from app.models.terapeuta import Terapeuta

__all__ = [
    "CalidadVinculo",
    "ConexionGenograma",
    "EstadoIA",
    "EstadoPaciente",
    "Genero",
    "NodoGenograma",
    "Paciente",
    "Prioridad",
    "Recordatorio",
    "RolNodo",
    "Sesion",
    "SesionNodoLink",
    "Terapeuta",
    "TipoVinculo",
]
