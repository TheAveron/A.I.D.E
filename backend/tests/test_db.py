import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import database


def test_load_db_config():
    """
    Test if the database.ini configuration is loaded correctly.
    """
    config = database.load_db_config()
    assert isinstance(config, dict)
    for key in ["host", "database", "user", "password", "port"]:
        assert key in config
        assert config[key]


def test_sqlalchemy_engine_connect():
    """
    Test if SQLAlchemy engine can connect to the database.
    """
    try:
        with database.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"SQLAlchemy could not connect to the database. Reason: {e}")


def test_get_db_session():
    """
    Test the session creation from get_db generator.
    """
    gen = database.get_db()
    db = next(gen)
    assert db is not None
    assert hasattr(db, "query")
    # Properly close the session
    try:
        next(gen)
    except StopIteration:
        pass
