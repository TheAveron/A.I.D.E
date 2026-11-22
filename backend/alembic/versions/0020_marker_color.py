"""a colour for generic points of interest

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-22 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020"
down_revision: Union[str, Sequence[str], None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("map_markers", sa.Column("color", sa.String(length=7), nullable=True))


def downgrade() -> None:
    op.drop_column("map_markers", "color")
