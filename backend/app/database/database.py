"""
database.py

Handles PostgreSQL database connection using SQLAlchemy, with configuration
loaded from an external database.ini file. Used throughout A.I.D.E backend
for ORM operations and dependency injection.
"""

import configparser
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.session import Session

# CONFIGURATION


def load_db_config(filename=None, section="postgresql") -> dict:
    """
    Reads database configuration from a .ini file.
    """
    filename = (
        filename
        or Path(__file__).parent.parent.parent / "app" / "config" / "database.ini"
    )

    parser = configparser.ConfigParser()
    parser.read(filename)

    if not parser.has_section(section):
        raise Exception(f"Section '{section}' not found in the config file: {filename}")

    return {param[0]: param[1] for param in parser.items(section)}


# SQLALCHEMY SETUP (ORM)


def build_database_url(params: dict) -> URL:
    """Database URL from the .ini parameters.

    Built with URL.create so that characters such as "@", ":" or "/" in the
    user name or password are escaped instead of breaking the URL.
    """
    return URL.create(
        "postgresql",
        username=params["user"],
        password=params["password"],
        host=params["host"],
        port=int(params["port"]),
        database=params["database"],
    )


_db_params = load_db_config()
SQLALCHEMY_DATABASE_URL = build_database_url(_db_params)

# pool_pre_ping: test a pooled connection before using it, so a connection the
# database server closed meanwhile (restart, idle timeout) is replaced instead
# of failing the request.
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# FASTAPI DEPENDENCY


def get_db():
    """
    FastAPI dependency for getting a database session.
    Yields a SQLAlchemy session that is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
