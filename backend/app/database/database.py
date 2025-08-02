"""
database.py

Handles PostgreSQL database connection using SQLAlchemy, with configuration
loaded from an external database.ini file. Used throughout A.I.D.E backend
for ORM operations and dependency injection.
"""

import configparser
from ast import parse
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------


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


# ---------------------------------------------------------------------
# SQLALCHEMY SETUP (ORM)
# ---------------------------------------------------------------------

# Load config and construct connection URL
_db_params = load_db_config()
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{_db_params['user']}:{_db_params['password']}"
    f"@{_db_params['host']}:{_db_params['port']}/{_db_params['database']}"
)

# SQLAlchemy engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


# ---------------------------------------------------------------------
# FASTAPI DEPENDENCY
# ---------------------------------------------------------------------


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
