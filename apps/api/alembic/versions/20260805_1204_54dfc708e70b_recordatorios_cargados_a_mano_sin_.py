"""recordatorios cargados a mano sin sesion de origen

Revision ID: 54dfc708e70b
Revises: 7390820ee1b8
Create Date: 2026-08-05 12:04:12.267718

"""
from collections.abc import Sequence

import sqlalchemy as sa
# SQLModel genera tipos propios (AutoString); sin este import las migraciones
# autogeneradas fallan con NameError.
import sqlmodel

from alembic import op

revision: str = '54dfc708e70b'
down_revision: str | None = '7390820ee1b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column('recordatorios', 'sesion_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    """OJO: falla si existe algún recordatorio cargado a mano.

    Volver a NOT NULL sobre una columna que ya tiene NULLs es un error de
    Postgres, no un borrado silencioso. Para bajar de verdad hay que decidir
    antes qué hacer con esos recordatorios —borrarlos o adosarlos a una sesión—
    y recién después correr el downgrade.
    """
    op.alter_column('recordatorios', 'sesion_id',
               existing_type=sa.UUID(),
               nullable=False)
