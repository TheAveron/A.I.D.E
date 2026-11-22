"""shared currencies: an integer key, several factions, issuers

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-22 20:00:00.000000

A currency was keyed by its name and belonged to one faction. Now:
- `currencies.currency_id` is the key; offers, transactions and the currency
  history point at it, so a currency can be renamed even once it is used;
- `currency_factions` lists the factions using a currency (one currency per
  faction), the issuers flagged; each currency's former faction becomes its
  only issuer;
- `currency_link_requests` holds the pending requests and invitations.

Downgrade: every currency goes back to one faction (an issuer first, the
oldest link otherwise); the other links and the requests are lost.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0021"
down_revision: Union[str, Sequence[str], None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The tables pointing at a currency
REFERENCING = ("offers", "transactions", "currency_history")


def _drop_foreign_keys(table: str, column: str) -> None:
    """Drop the foreign keys of `table` on `column` (names read from the
    catalog: the first migrations let PostgreSQL name them)."""
    for fk in sa.inspect(op.get_bind()).get_foreign_keys(table):
        if fk["constrained_columns"] == [column] and fk["name"]:
            op.drop_constraint(fk["name"], table, type_="foreignkey")


def _drop_indexes(table: str, column: str) -> None:
    for index in sa.inspect(op.get_bind()).get_indexes(table):
        if column in index["column_names"]:
            op.drop_index(index["name"], table_name=table)


def _drop_primary_key(table: str) -> None:
    name = sa.inspect(op.get_bind()).get_pk_constraint(table)["name"]
    op.drop_constraint(name, table, type_="primary")


def upgrade() -> None:
    # 1. An integer key, filled for the existing rows by the sequence
    op.execute("ALTER TABLE currencies ADD COLUMN currency_id SERIAL")

    # currency_id must be the key before anything can reference it
    for table in REFERENCING:
        _drop_foreign_keys(table, "currency_name")
    _drop_primary_key("currencies")
    _drop_indexes("currencies", "name")
    op.create_primary_key("currencies_pkey", "currencies", ["currency_id"])
    op.create_unique_constraint("uq_currencies_name", "currencies", ["name"])

    # 2. Who uses which currency: each currency's faction issues it
    op.create_table(
        "currency_factions",
        sa.Column(
            "currency_id",
            sa.Integer,
            sa.ForeignKey("currencies.currency_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_issuer", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "joined_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("faction_id", name="uq_currency_factions_faction"),
    )
    op.execute("""
        INSERT INTO currency_factions (currency_id, faction_id, is_issuer, joined_at)
        SELECT currency_id, faction_id, TRUE, created_at
        FROM currencies WHERE faction_id IS NOT NULL
        """)
    # Its unique constraint, index and foreign key go with the column
    op.drop_column("currencies", "faction_id")

    # 3. The referencing tables point at the id
    for table in REFERENCING:
        op.add_column(table, sa.Column("currency_id", sa.Integer, nullable=True))
        op.execute(f"""
            UPDATE {table} SET currency_id = c.currency_id
            FROM currencies c WHERE c.name = {table}.currency_name
            """)
        op.alter_column(table, "currency_id", nullable=False)
        _drop_indexes(table, "currency_name")
        op.drop_column(table, "currency_name")
        op.create_foreign_key(
            f"{table}_currency_id_fkey",
            table,
            "currencies",
            ["currency_id"],
            ["currency_id"],
        )
        op.create_index(f"ix_{table}_currency_id", table, ["currency_id"])
    op.create_index(
        "ix_currency_history_currency_id_timestamp",
        "currency_history",
        ["currency_id", "timestamp"],
    )

    # 4. Requests and invitations
    op.create_table(
        "currency_link_requests",
        sa.Column("request_id", sa.Integer, primary_key=True),
        sa.Column(
            "currency_id",
            sa.Integer,
            sa.ForeignKey("currencies.currency_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("kind", sa.String(length=12), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.Integer,
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column(
            "decided_by_user_id",
            sa.Integer,
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "uq_currency_link_requests_one_pending",
        "currency_link_requests",
        ["currency_id", "faction_id"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDING'"),
    )


def downgrade() -> None:
    # 1. Each currency back to one faction: an issuer first, then the oldest
    op.add_column("currencies", sa.Column("faction_id", sa.Integer, nullable=True))
    op.execute("""
        UPDATE currencies SET faction_id = (
            SELECT cf.faction_id FROM currency_factions cf
            WHERE cf.currency_id = currencies.currency_id
            ORDER BY cf.is_issuer DESC, cf.joined_at, cf.faction_id
            LIMIT 1
        )
        """)
    op.drop_table("currency_link_requests")
    op.drop_table("currency_factions")

    # 2. The referencing tables point at the name again
    for table in REFERENCING:
        op.add_column(
            table, sa.Column("currency_name", sa.String(length=50), nullable=True)
        )
        op.execute(f"""
            UPDATE {table} SET currency_name = c.name
            FROM currencies c WHERE c.currency_id = {table}.currency_id
            """)
        op.alter_column(table, "currency_name", nullable=False)
        # Its foreign key and indexes go with the column
        op.drop_column(table, "currency_id")

    # 3. The name is the key again
    op.drop_constraint("uq_currencies_name", "currencies", type_="unique")
    _drop_primary_key("currencies")
    op.drop_column("currencies", "currency_id")  # drops its sequence too
    op.create_primary_key("currencies_pkey", "currencies", ["name"])
    op.create_index("ix_currencies_name", "currencies", ["name"])
    op.create_foreign_key(
        "currencies_faction_id_fkey",
        "currencies",
        "factions",
        ["faction_id"],
        ["faction_id"],
        ondelete="CASCADE",
    )
    # As the initial schema made it: one unique index (unique + index=True)
    op.create_index(
        "ix_currencies_faction_id", "currencies", ["faction_id"], unique=True
    )

    for table in REFERENCING:
        op.create_foreign_key(
            f"{table}_currency_name_fkey",
            table,
            "currencies",
            ["currency_name"],
            ["name"],
        )
    op.create_index("ix_offers_currency_name", "offers", ["currency_name"])
    op.create_index(
        "ix_currency_history_currency_name", "currency_history", ["currency_name"]
    )
    op.create_index(
        "ix_currency_history_currency_name_timestamp",
        "currency_history",
        ["currency_name", "timestamp"],
    )
