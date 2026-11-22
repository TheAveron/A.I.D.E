"""rename default currency Diamant -> Dolar

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-19 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: Union[str, Sequence[str], None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_NAME = "Diamant"
NEW_NAME = "Dollar"


def _rename_currency(old: str, new: str) -> None:
    """Rename a currency (its name is the primary key).

    The foreign keys pointing at currencies.name have no ON UPDATE CASCADE,
    so a plain UPDATE fails. Instead: copy the row under the new name,
    repoint every referencing row, then delete the old row. Referencing
    tables are read from the catalog, so none can be forgotten.

    Does nothing if `old` does not exist or `new` is already taken.
    """
    bind = op.get_bind()

    def exists(name: str) -> bool:
        row = bind.execute(
            sa.text("SELECT 1 FROM currencies WHERE name = :n"), {"n": name}
        ).first()
        return row is not None

    if not exists(old) or exists(new):
        return

    quote = bind.dialect.identifier_preparer.quote

    # Every column except the key and the unique faction_id is copied as is.
    other_cols = ", ".join(
        quote(c["name"])
        for c in sa.inspect(bind).get_columns("currencies")
        if c["name"] not in ("name", "faction_id")
    )

    faction_id = bind.execute(
        sa.text("SELECT faction_id FROM currencies WHERE name = :old"), {"old": old}
    ).scalar()

    # faction_id is UNIQUE: free it on the old row so the copy can take it.
    bind.execute(
        sa.text("UPDATE currencies SET faction_id = NULL WHERE name = :old"),
        {"old": old},
    )
    bind.execute(
        sa.text(
            f"INSERT INTO currencies (name, faction_id, {other_cols}) "
            f"SELECT :new, :faction_id, {other_cols} "
            "FROM currencies WHERE name = :old"
        ),
        {"new": new, "faction_id": faction_id, "old": old},
    )

    # Single-column foreign keys referencing currencies.name.
    references = bind.execute(sa.text("""
            SELECT c.conrelid::regclass::text AS tbl, a.attname AS col
            FROM pg_constraint c
            JOIN pg_attribute a
              ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
            JOIN pg_attribute af
              ON af.attrelid = c.confrelid AND af.attnum = c.confkey[1]
            WHERE c.contype = 'f'
              AND c.confrelid = 'currencies'::regclass
              AND cardinality(c.conkey) = 1
              AND af.attname = 'name'
            """)).all()
    for tbl, col in references:
        bind.execute(
            sa.text(f"UPDATE {tbl} SET {quote(col)} = :new WHERE {quote(col)} = :old"),
            {"new": new, "old": old},
        )

    bind.execute(sa.text("DELETE FROM currencies WHERE name = :old"), {"old": old})


def upgrade() -> None:
    """Upgrade schema."""
    _rename_currency(OLD_NAME, NEW_NAME)


def downgrade() -> None:
    """Downgrade schema."""
    # Restores the name migration 0001 expects when it is downgraded.
    _rename_currency(NEW_NAME, OLD_NAME)
