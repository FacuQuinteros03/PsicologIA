"""quitar derivado_por de la ficha de admision

Revision ID: 7390820ee1b8
Revises: baec577fc7e8
Create Date: 2026-08-04 22:14:25.057347

"""
from collections.abc import Sequence

import sqlalchemy as sa
# SQLModel genera tipos propios (AutoString); sin este import las migraciones
# autogeneradas fallan con NameError.
import sqlmodel

from alembic import op

revision: str = '7390820ee1b8'
down_revision: str | None = 'baec577fc7e8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column('pacientes', 'derivado_por')


def downgrade() -> None:
    """Recrea la columna, pero NO los datos: lo que hubiera en `derivado_por`
    se pierde en el upgrade y vuelve en NULL. En esta base sólo había el valor
    del seed, así que no hay nada real que rescatar; si esto se corriera sobre
    una base con pacientes cargados, habría que respaldar la columna antes."""
    op.add_column('pacientes', sa.Column('derivado_por', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
