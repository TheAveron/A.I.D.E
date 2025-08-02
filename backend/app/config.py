from database.database import Base, engine
from database.models import (Currency, Faction, Offer, OfferHistory, Role,
                             Transaction, User)
from sqlalchemy import create_engine


def create_tables():
    """Create all database tables"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")


if __name__ == "__main__":
    create_tables()
