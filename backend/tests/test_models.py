# backend/app/tests/test_models.py

from backend.app.database import User, Faction, Offer, Currency


def test_create_user(session):
    user = User(username="test_user", email="user@example.com", password="pass")
    session.add(user)
    session.commit()
    result = session.query(User).filter_by(username="test_user").first()
    assert result.email == "user@example.com"


def test_create_faction_and_link_user(session):
    faction = Faction(name="Alpha", description="Test faction")
    user = User(
        username="member1", email="m1@example.com", password="pass", faction=faction
    )

    session.add(faction)
    session.add(user)
    session.commit()

    result = session.query(User).filter_by(username="member1").first()
    assert result.faction.name == "Alpha"


def test_currency_creation(session):
    currency = Currency(name="Credits")
    session.add(currency)
    session.commit()
    result = session.query(Currency).first()
    assert result.name == "Credits"


def test_offer_creation_and_user_relationships(session):
    user = User(username="creator", email="c@example.com", password="pass")
    accepter = User(username="accepter", email="a@example.com", password="pass")
    currency = Currency(name="Gold")

    session.add_all([user, accepter, currency])
    session.commit()

    offer = Offer(
        user_id=user.id,
        accepted_by_user_id=accepter.id,
        item_name="Laser Gun",
        quantity=1,
        price=500.0,
        currency=currency.id,
    )

    session.add(offer)
    session.commit()

    result = session.query(Offer).first()
    assert result.user.username == "creator"
    assert result.accepted_by_user.username == "accepter"
    assert result.item_name == "Laser Gun"
    assert result.currency == currency.id
