"""Regression tests for the second backend pass: registration, conflicts,
public user data, atomic faction creation, documents, offers listing and the
database URL.

Self-contained like test_bug_fixes.py: SQLite in memory, a small FastAPI app
with only the routers under test, real JWTs.
"""

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth, documentation, faction, offer, user
from app.core.security import create_access_token, hash_password
from app.crud import faction as faction_crud
from app.database import (Base, Currency, Faction, Offer, Role, User, get_db)
from app.database.database import build_database_url
from app.misc import OfferStatus, OfferType

PW_HASH = hash_password("pw")


@pytest.fixture
def env():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    s = Session()
    s.add_all([
        Faction(faction_id=1, name="Alpha", is_approved=True),
        Faction(faction_id=3, name="Sans Faction", is_approved=True),
    ])
    s.commit()
    s.add_all([
        Role(role_id=1, name="Chef", faction_id=1, accept_offers=True,
             create_offers=True, manage_funds=True, handle_members=True,
             manage_roles=True, manage_docs=True, view_transactions=True),
        Role(role_id=20, name="Membre", faction_id=3, view_transactions=True),
        Role(role_id=21, name="Invité", faction_id=3),
    ])
    s.commit()
    s.add_all([
        User(user_id=1, username="alice", hashed_password=PW_HASH, faction_id=1,
             role_id=1, email="alice@example.com"),
        User(user_id=2, username="newbie", hashed_password=PW_HASH, faction_id=3,
             role_id=20),
    ])
    s.add(Currency(name="Diamant", faction_id=1, total_in_circulation=0))
    s.commit()
    s.close()

    app = FastAPI()
    for module in (auth, user, faction, offer, documentation):
        app.include_router(module.router)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override

    class Env:
        pass

    e = Env()
    e.client = TestClient(app, raise_server_exceptions=False)
    e.Session = Session
    e.h = lambda name: {"Authorization": "Bearer " + create_access_token({"sub": name})}
    return e


# ------------------------------------------------------------ registration
class TestRegistration:
    def register(self, env, username="fresh", password="pw12345"):
        return env.client.post(
            "/auth/register", json={"username": username, "password": password}
        )

    def test_a_valid_registration_works(self, env):
        r = self.register(env)
        assert r.status_code == 201, r.text
        assert r.json()["username"] == "fresh"

    def test_a_taken_username_is_a_409(self, env):
        assert self.register(env, "alice").status_code == 409

    def test_two_registrations_racing_for_one_name_give_409_not_500(
        self, env, monkeypatch
    ):
        # Both requests passed the "is it taken?" check before either inserted:
        # simulate it by making the check blind to the existing account.
        monkeypatch.setattr(auth, "get_user_by_username", lambda db, name: None)
        r = self.register(env, "alice")
        assert r.status_code == 409 and "taken" in r.json()["detail"]

    def test_username_longer_than_the_column_is_a_422(self, env):
        assert self.register(env, "x" * 51).status_code == 422
        assert self.register(env, "x" * 50).status_code == 201

    def test_blank_username_is_a_422(self, env):
        assert self.register(env, "   ").status_code == 422
        assert self.register(env, "").status_code == 422

    def test_password_longer_than_bcrypt_accepts_is_a_422(self, env):
        assert self.register(env, "p72", "a" * 72).status_code == 201
        assert self.register(env, "p73", "a" * 73).status_code == 422
        # 40 two-byte characters = 80 bytes, only 40 characters
        assert self.register(env, "pmb", "é" * 40).status_code == 422

    def test_empty_password_is_a_422(self, env):
        assert self.register(env, "nopw", "").status_code == 422

    def test_login_with_an_overlong_password_is_a_401_not_a_500(self, env):
        r = env.client.post(
            "/auth/login", json={"username": "alice", "password": "a" * 200}
        )
        assert r.status_code == 401

    def test_login_still_works(self, env):
        r = env.client.post("/auth/login", json={"username": "alice", "password": "pw"})
        assert r.status_code == 202


# -------------------------------------------------------- public user data
class TestUsersDoNotLeakEmails:
    def test_lookups_by_id_name_and_faction_hide_the_email(self, env):
        by_id = env.client.get("/users/detail/1").json()
        by_name = env.client.get("/users/from_name/alice").json()
        by_faction = env.client.get("/users/faction/1").json()
        for payload in (by_id, by_name, *by_faction):
            assert "email" not in payload
            assert payload["username"] == "alice"

    def test_the_public_view_keeps_what_the_frontend_uses(self, env):
        payload = env.client.get("/users/detail/1").json()
        assert {"user_id", "username", "is_admin", "created_at", "faction_id",
                "role_id"} <= set(payload)

    def test_me_still_shows_your_own_email(self, env):
        r = env.client.get("/users/me", headers=env.h("alice"))
        assert r.json()["email"] == "alice@example.com"


# ------------------------------------------------------ faction creation
class TestFactionCreation:
    def counts(self, env):
        s = env.Session()
        out = (s.query(Faction).count(), s.query(Role).count())
        s.close()
        return out

    def test_creation_gives_roles_and_makes_the_creator_leader(self, env):
        r = env.client.post("/factions/create", json={"name": "Gamma"},
                            headers=env.h("newbie"))
        assert r.status_code == 201, r.text
        s = env.Session()
        newbie = s.get(User, 2)
        assert newbie.faction_id == r.json()["faction_id"]
        assert newbie.role.name == "Chef"
        names = {x.name for x in s.query(Role).filter_by(faction_id=newbie.faction_id)}
        assert names == {"Chef", "Chef Adjoint", "Trésorier", "Marchand", "Membre",
                         "Invité"}
        s.close()

    def test_a_failure_while_creating_roles_leaves_nothing_behind(
        self, env, monkeypatch
    ):
        real = faction_crud.create_default_faction_roles

        def roles_then_crash(db, faction_id, user_id, commit=True):
            real(db, faction_id, user_id, commit=False)
            raise SQLAlchemyError("boom")

        monkeypatch.setattr(faction_crud, "create_default_faction_roles",
                            roles_then_crash)
        before = self.counts(env)
        r = env.client.post("/factions/create", json={"name": "Gamma"},
                            headers=env.h("newbie"))
        assert r.status_code == 500
        assert self.counts(env) == before
        s = env.Session()
        newbie = s.get(User, 2)
        assert (newbie.faction_id, newbie.role_id) == (3, 20)  # untouched
        s.close()

    def test_a_duplicate_name_is_a_409(self, env):
        r = env.client.post("/factions/create", json={"name": "Alpha"},
                            headers=env.h("newbie"))
        assert r.status_code == 409

    def test_two_creations_racing_for_one_name_give_409(self, env, monkeypatch):
        # The pre-checks see no clash (both requests passed them); the unique
        # constraint catches the second one.
        monkeypatch.setattr(faction_crud, "get_faction_by_name", lambda db, n: None)
        monkeypatch.setattr(faction_crud, "normalized_name_taken",
                            lambda db, n, exclude=None: False)
        before = self.counts(env)
        r = env.client.post("/factions/create", json={"name": "Alpha"},
                            headers=env.h("newbie"))
        assert r.status_code == 409
        assert self.counts(env) == before


# ---------------------------------------------------------------- documents
class TestDocumentCreation:
    def test_an_existing_document_is_never_overwritten(self, env, monkeypatch, tmp_path):
        monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
        h = env.h("alice")
        first = {"title": "Reglement", "content": "original"}
        assert env.client.post("/documents/create", json=first, headers=h).status_code == 201

        second = {"title": "Reglement", "content": "replacement"}
        r = env.client.post("/documents/create", json=second, headers=h)
        assert r.status_code == 409

        path = tmp_path / "documents" / "AOS" / "alpha" / "reglement.md"
        assert "original" in path.read_text(encoding="utf-8")
        assert "replacement" not in path.read_text(encoding="utf-8")

    def test_a_title_normalizing_to_the_same_name_is_also_a_conflict(
        self, env, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
        h = env.h("alice")
        assert env.client.post("/documents/create", json={"title": "Règlement", "content": "a"},
                               headers=h).status_code == 201
        assert env.client.post("/documents/create", json={"title": "reglement 2", "content": "b"},
                               headers=h).status_code == 409


# ------------------------------------------------------------------- offers
class TestOfferListing:
    @pytest.fixture
    def offers(self, env):
        s = env.Session()
        base = datetime(2026, 1, 1)
        for i in range(1, 6):
            s.add(Offer(
                offer_id=i,
                user_id=1 if i % 2 else None,
                faction_id=None if i % 2 else 1,
                offer_type=OfferType.SELL,
                item_description=f"item {i}",
                currency_name="Diamant",
                price_per_unit=1.0,
                quantity=1,
                init_quantity=1,
                status=OfferStatus.OPEN,
                created_at=base + timedelta(days=i),
            ))
        s.commit()
        s.close()
        return env

    def ids(self, env, query=""):
        r = env.client.get(f"/offers/list{query}")
        assert r.status_code == 200, r.text
        return [o["offer_id"] for o in r.json()]

    def test_newest_first(self, offers):
        assert self.ids(offers) == [5, 4, 3, 2, 1]

    def test_pages_follow_that_order_without_overlap(self, offers):
        assert self.ids(offers, "?limit=2") == [5, 4]
        assert self.ids(offers, "?limit=2&skip=2") == [3, 2]
        assert self.ids(offers, "?limit=2&skip=4") == [1]

    def test_ties_on_creation_time_keep_a_stable_order(self, env):
        s = env.Session()
        same = datetime(2026, 1, 1)
        for i in (1, 2, 3):
            s.add(Offer(offer_id=i, user_id=1, offer_type=OfferType.SELL,
                        item_description="x", currency_name="Diamant",
                        price_per_unit=1.0, quantity=1, init_quantity=1,
                        status=OfferStatus.OPEN, created_at=same))
        s.commit()
        s.close()
        assert self.ids(env) == [3, 2, 1]
        assert self.ids(env, "?limit=1&skip=1") == [2]

    def test_owner_filters(self, offers):
        assert self.ids(offers, "?user_id=1") == [5, 3, 1]
        assert self.ids(offers, "?faction_id=1") == [4, 2]
        assert self.ids(offers, "?user_id=999") == []

    def test_page_size_is_bounded(self, offers):
        assert offers.client.get("/offers/list?limit=0").status_code == 422
        assert offers.client.get("/offers/list?limit=201").status_code == 422
        assert offers.client.get("/offers/list?skip=-1").status_code == 422
        assert offers.client.get("/offers/list?limit=200").status_code == 200


# --------------------------------------------------------------- database
class TestDatabaseUrl:
    def test_special_characters_in_credentials_are_escaped(self):
        params = {"user": "u@ser", "password": "p@ss:w/rd#?%", "host": "db.local",
                  "port": "5433", "database": "aide"}
        url = build_database_url(params)
        rendered = url.render_as_string(hide_password=False)
        assert rendered.startswith("postgresql://u%40ser:")
        back = make_url(rendered)
        assert (back.username, back.password) == ("u@ser", "p@ss:w/rd#?%")
        assert (back.host, back.port, back.database) == ("db.local", 5433, "aide")

    def test_the_engine_pings_connections_before_use(self):
        from app.database.database import engine

        assert engine.pool._pre_ping is True
