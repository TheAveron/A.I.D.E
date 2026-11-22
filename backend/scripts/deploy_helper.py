"""
deploy_helper.py

What deploy.bat and deploy.sh need from Python, the same on Windows and Linux.
Run from the backend/ directory, with the virtualenv active:

    # Dump the database (pg_dump, custom format) before a deployment changes
    # it; prints the file written in backend/backups/.
    python -m scripts.deploy_helper backup v1.4.0

    # Before going to another tag: the revision the database must be brought
    # down to with the CURRENT code (only it knows how to undo its own
    # migrations), or "none" when the target tag knows the current revision.
    python -m scripts.deploy_helper downgrade-target v1.3.2

pg_dump is looked for in PG_DUMP (its full path), then on PATH, then in the
usual PostgreSQL install folders on Windows.

Restoring a backup (stop the backend first):

    pg_restore --clean --if-exists -h HOST -p PORT -U USER -d DATABASE FILE
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

BACKEND = Path(__file__).resolve().parent.parent
REPO = BACKEND.parent
VERSIONS = "backend/alembic/versions"


# ---- backup ----


def find_pg_dump() -> Optional[str]:
    explicit = os.environ.get("PG_DUMP")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    found = shutil.which("pg_dump")
    if found:
        return found
    # Windows installer: C:\Program Files\PostgreSQL\<version>\bin
    candidates = glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe")
    candidates.sort(key=lambda p: int(re.sub(r"\D", "", Path(p).parts[-3]) or 0))
    return candidates[-1] if candidates else None


def backup(label: str) -> int:
    from app.database.database import load_db_config

    pg_dump = find_pg_dump()
    if not pg_dump:
        print(
            "pg_dump not found: install the PostgreSQL client tools, or set "
            "PG_DUMP to the full path of pg_dump",
            file=sys.stderr,
        )
        return 1
    params = load_db_config()
    folder = BACKEND / "backups"
    folder.mkdir(exist_ok=True)
    safe_label = re.sub(r"[^A-Za-z0-9._-]", "_", label)
    target = folder / f"aide_{safe_label}_{datetime.now():%Y%m%d-%H%M%S}.dump"
    env = {**os.environ, "PGPASSWORD": params["password"]}
    result = subprocess.run(
        [
            pg_dump,
            "--format=custom",
            "--host", params["host"],
            "--port", str(params["port"]),
            "--username", params["user"],
            "--file", str(target),
            params["database"],
        ],
        env=env,
    )
    if result.returncode != 0:
        target.unlink(missing_ok=True)
        print("pg_dump failed: the database was not saved", file=sys.stderr)
        return 1
    print(target)
    return 0


# ---- rollback ----

_REVISION = re.compile(r"^revision\b[^=\n]*=\s*['\"]([^'\"]+)['\"]", re.M)
_DOWN = re.compile(r"^down_revision\b[^=\n]*=\s*(.+)$", re.M)


def parse_migration(source: str) -> tuple[Optional[str], set[str]]:
    """The revision of a migration file and the ones it comes after."""
    revision = _REVISION.search(source)
    down = _DOWN.search(source)
    parents = set(re.findall(r"['\"]([^'\"]+)['\"]", down.group(1))) if down else set()
    return (revision.group(1) if revision else None), parents


def downgrade_target(
    current: set[str], migrations: dict[str, set[str]]
) -> Optional[str]:
    """Where the database must go down to before switching to a tag.

    `current` holds the database's revisions (empty for a new database),
    `migrations` maps each revision of the target tag to its parents. None
    when the target knows every current revision: a plain upgrade will do.
    """
    if not migrations:
        raise ValueError("The target has no migrations")
    if current <= migrations.keys():
        return None
    parents = set().union(*migrations.values())
    heads = [rev for rev in migrations if rev not in parents]
    if len(heads) != 1:
        raise ValueError(f"The target has {len(heads)} heads: {sorted(heads)}")
    return heads[0]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def migrations_of(tag: str) -> dict[str, set[str]]:
    """The migrations of a tag, read from git without checking it out."""
    migrations = {}
    for path in _git("ls-tree", "--name-only", f"{tag}:{VERSIONS}").split():
        if not path.endswith(".py"):
            continue
        revision, parents = parse_migration(_git("show", f"{tag}:{VERSIONS}/{path}"))
        if revision:
            migrations[revision] = parents
    return migrations


def current_revisions() -> set[str]:
    from alembic.migration import MigrationContext

    from app.database.database import engine

    with engine.connect() as connection:
        return set(MigrationContext.configure(connection).get_current_heads())


def print_downgrade_target(tag: str) -> int:
    try:
        target = downgrade_target(current_revisions(), migrations_of(tag))
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"Cannot tell where to go for {tag}: {error}", file=sys.stderr)
        return 1
    print(target or "none")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("backup").add_argument("label")
    commands.add_parser("downgrade-target").add_argument("tag")
    args = parser.parse_args()
    if args.command == "backup":
        return backup(args.label)
    return print_downgrade_target(args.tag)


if __name__ == "__main__":
    sys.exit(main())
