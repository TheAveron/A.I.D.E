from database.database import Base, engine
from database.models import (Currency, Faction, Offer, OfferHistory, Role,
                             Transaction, User)
from sqlalchemy_utils import create_database, database_exists


def create_tables():
    """Create all database tables"""
    # Create all tables

    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.create_all(bind=engine)

        print("All tables created successfully!")


if __name__ == "__main__":
    create_tables()
