from sqlalchemy_utils import create_database, database_exists

from app.database.database import engine


def create_tables():
    """Create the database if it doesn't exist yet.

    Table creation itself is handled by Alembic migrations, not here.
    """
    if not database_exists(engine.url):
        create_database(engine.url)
        print("Database created")


if __name__ == "__main__":
    create_tables()
