"""one spawn per map

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-17 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: Union[str, Sequence[str], None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Spawns made before the rule: keep the oldest of each map, the others
    # become plain points (nothing is deleted).
    op.execute(
        "UPDATE map_markers SET kind = 'generic' "
        "WHERE kind = 'spawn' AND marker_id NOT IN ("
        "SELECT MIN(marker_id) FROM map_markers "
        "WHERE kind = 'spawn' GROUP BY map_name)"
    )
    op.create_index(
        "uq_map_one_spawn",
        "map_markers",
        ["map_name"],
        unique=True,
        postgresql_where="kind = 'spawn'",
    )


def downgrade() -> None:
    op.drop_index("uq_map_one_spawn", table_name="map_markers")
