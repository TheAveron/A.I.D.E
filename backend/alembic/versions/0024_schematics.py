"""schematics: a gallery of structure files (.nbt)

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-23 18:00:00.000000

Three tables:
- schematics: title, description, author, preview image;
- schematic_versions: every uploaded file (numbered from 1), with the size
  and block count read from it and the "complies with the railway standards"
  badge;
- schematic_tags: free tags, lower case.

The files themselves are stored on disk (SCHEMATICS_DIR), not in the database.
Downgrade drops the tables; the files on disk are left in place.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0024"
down_revision: Union[str, Sequence[str], None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schematics",
        sa.Column("schematic_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author_user_id", sa.Integer(), nullable=True),
        sa.Column("preview_file", sa.String(length=64), nullable=True),
        sa.Column("preview_type", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("schematic_id"),
    )

    op.create_table(
        "schematic_versions",
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("schematic_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=64), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_x", sa.Integer(), nullable=False),
        sa.Column("size_y", sa.Integer(), nullable=False),
        sa.Column("size_z", sa.Integer(), nullable=False),
        sa.Column("block_count", sa.Integer(), nullable=False),
        sa.Column("data_version", sa.Integer(), nullable=True),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("compliant", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("compliant_by_user_id", sa.Integer(), nullable=True),
        sa.Column("compliant_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["schematic_id"], ["schematics.schematic_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["compliant_by_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("version_id"),
        sa.UniqueConstraint("schematic_id", "number", name="uq_schematic_version"),
    )

    op.create_table(
        "schematic_tags",
        sa.Column("schematic_id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(
            ["schematic_id"], ["schematics.schematic_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("schematic_id", "tag"),
    )
    op.create_index("ix_schematic_tags_tag", "schematic_tags", ["tag"])


def downgrade() -> None:
    op.drop_index("ix_schematic_tags_tag", table_name="schematic_tags")
    op.drop_table("schematic_tags")
    op.drop_table("schematic_versions")
    op.drop_table("schematics")
