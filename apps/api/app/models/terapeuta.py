"""Tabla `terapeutas` — raíz del multi-tenant."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.paciente import Paciente


class Terapeuta(UUIDMixin, TimestampMixin, table=True):
    """El dueño de los datos.

    Todavía no hay autenticación: el MVP trabaja contra un terapeuta seed. Cuando
    entre auth se agrega `hashed_password` acá y el resto del esquema no cambia,
    porque `pacientes` ya cuelga de esta tabla.
    """

    __tablename__ = "terapeutas"

    email: str = Field(max_length=255, unique=True, index=True)
    nombre_completo: str = Field(max_length=200)
    matricula: str | None = Field(default=None, max_length=100)

    pacientes: list["Paciente"] = Relationship(
        back_populates="terapeuta",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
