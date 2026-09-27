"""
create_admin.py

One-off CLI utility to create a new admin user, or promote an existing
user to admin.

There is intentionally NO HTTP endpoint for this: exposing admin
creation over the API is exactly the privilege-escalation bug that was
removed from POST /auth/register (is_admin used to be a client-supplied
field on UserCreate). This script assumes whoever runs it already has
trusted access to the server / database (shell access, deploy access,
etc.) - the same trust level required to run alembic migrations.

Usage (run from the backend/ directory, with your virtualenv active and
app/config/.env / database.ini already configured):

    # Create a brand new admin account (prompts for a password if
    # --password is omitted, input is not echoed to the terminal):
    python -m scripts.create_admin --username alice

    # Promote an existing user to admin instead:
    python -m scripts.create_admin --promote --username alice
"""

import argparse
import getpass
import sys

from app.core.security import hash_password
from app.crud.user import create_user, get_user_by_username
from app.database import SessionLocal


def create_admin(username: str, password: str) -> None:
    db = SessionLocal()
    try:
        if get_user_by_username(db, username):
            print(
                f"Error: a user named '{username}' already exists. "
                f"Use --promote instead.",
                file=sys.stderr,
            )
            sys.exit(1)

        user = create_user(
            db=db,
            username=username,
            hashed_password=hash_password(password),
            admin=True,
        )
        print(f"Created admin user '{user.username}' (user_id={user.user_id}).")
    finally:
        db.close()


def promote_existing(username: str) -> None:
    db = SessionLocal()
    try:
        user = get_user_by_username(db, username)
        if not user:
            print(f"Error: no user named '{username}' found.", file=sys.stderr)
            sys.exit(1)
        if user.is_admin:
            print(f"'{username}' is already an admin. Nothing to do.")
            return

        user.is_admin = True
        db.commit()
        print(f"'{username}' promoted to admin.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create a new admin user, or promote an existing one. "
            "Run this only on a trusted machine with direct DB access."
        )
    )
    parser.add_argument("--username", required=True)
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Promote an existing user to admin instead of creating a new one.",
    )
    parser.add_argument(
        "--password",
        help=(
            "Password for the new admin account. If omitted, you will be "
            "prompted interactively (input is not echoed). Ignored with "
            "--promote."
        ),
    )
    args = parser.parse_args()

    if args.promote:
        promote_existing(args.username)
        return

    password = args.password or getpass.getpass("Password for new admin: ")
    if not password:
        print("Error: password cannot be empty.", file=sys.stderr)
        sys.exit(1)

    create_admin(args.username, password)


if __name__ == "__main__":
    main()
