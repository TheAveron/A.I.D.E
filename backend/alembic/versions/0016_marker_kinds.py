"""marker kinds: the list of places the map shows with an icon

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-17 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016"
down_revision: Union[str, Sequence[str], None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """The old kinds had no icon: a base is a city, the rest a plain point."""
    op.execute("UPDATE map_markers SET kind = 'city' WHERE kind = 'base'")
    op.execute(
        "UPDATE map_markers SET kind = 'generic' "
        "WHERE kind IN ('resource', 'portal', 'landmark', 'other')"
    )


def downgrade() -> None:
    """Back to the five old kinds (the finer ones all become "other")."""
    op.execute("UPDATE map_markers SET kind = 'base' WHERE kind = 'city'")
    op.execute(
        "UPDATE map_markers SET kind = 'other' "
        "WHERE kind NOT IN ('base', 'resource', 'portal', 'landmark', 'other')"
    )
