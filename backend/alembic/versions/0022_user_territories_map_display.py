"""territories of players, and the map display saved on the account

Revision ID: 0022
Revises: 0021
Create Date: 2026-11-22 22:00:00.000000

- a territory belongs to a faction or to a player (`map_territories.user_id`,
  exactly one of the two), like the points of interest;
- `user_preferences.map_display` keeps what the map showed when the person
  left it.

Downgrade: the players' territories are deleted (an older version could not
show them).
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0022"
down_revision: Union[str, Sequence[str], None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("map_territories") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_map_territories_user",
            "users",
            ["user_id"],
            ["user_id"],
            ondelete="CASCADE",
        )
        batch.create_index("ix_map_territories_user_id", ["user_id"])
        batch.alter_column("faction_id", existing_type=sa.Integer(), nullable=True)
        batch.create_check_constraint(
            "ck_map_territory_one_owner",
            "(faction_id IS NOT NULL AND user_id IS NULL) OR "
            "(faction_id IS NULL AND user_id IS NOT NULL)",
        )
        batch.create_unique_constraint(
            "uq_territory_user_name", ["map_name", "user_id", "name"]
        )
    op.add_column(
        "user_preferences", sa.Column("map_display", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("user_preferences", "map_display")
    op.execute("DELETE FROM map_territories WHERE user_id IS NOT NULL")
    with op.batch_alter_table("map_territories") as batch:
        batch.drop_constraint("uq_territory_user_name", type_="unique")
        batch.drop_constraint("ck_map_territory_one_owner", type_="check")
        batch.alter_column("faction_id", existing_type=sa.Integer(), nullable=False)
        batch.drop_index("ix_map_territories_user_id")
        batch.drop_constraint("fk_map_territories_user", type_="foreignkey")
        batch.drop_column("user_id")
