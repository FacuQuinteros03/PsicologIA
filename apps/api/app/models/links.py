"""Tabla puente `sesion_nodo` — la que habilita el feature estrella.

Tocar "Mamá" en el canvas y ver sólo las sesiones donde aparece se resuelve con
un join contra esta tabla. Sin ella habría que escanear el texto de cada sesión.

A propósito **no** se expone como `Relationship(link_model=...)` en `Sesion` ni en
`NodoGenograma`: la fila lleva datos propios (`menciones`, `contexto`) que una
relación `secondary` no sabe escribir, y tener las dos cosas mapeando la misma
tabla dispara los warnings de "overlapping relationships" de SQLAlchemy. El
servicio inserta y consulta este modelo de forma explícita.

**Consecuencia a tener en cuenta:** sin `Relationship`, la unit of work de
SQLAlchemy no conoce la dependencia con `sesiones` y puede intentar insertar acá
antes que la fila padre. Si creás una `Sesion` y sus links en el mismo flush,
hacé `await session.flush()` en el medio.
"""

import uuid

from sqlalchemy import Text
from sqlmodel import Field, SQLModel


class SesionNodoLink(SQLModel, table=True):
    __tablename__ = "sesion_nodo"

    sesion_id: uuid.UUID = Field(
        foreign_key="sesiones.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    nodo_id: uuid.UUID = Field(
        foreign_key="nodos_genograma.id",
        primary_key=True,
        index=True,
        ondelete="CASCADE",
    )

    menciones: int = Field(default=1)
    # Fragmento de la nota donde apareció la persona: da contexto en el panel
    # lateral sin tener que abrir la sesión entera.
    contexto: str | None = Field(default=None, sa_type=Text)
