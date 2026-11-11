"""Regression tests for the bug-fix pass on offers, members, factions,
transactions/history visibility and documents.

Self-contained: SQLite in memory, a small FastAPI app with only the routers
under test (no frontend build needed), real JWTs.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import (documentation, faction, offer, offer_history, transactions,
                     user)
from app.core.security import create_access_token, hash_password
from app.crud import faction as faction_crud
from app.database import (Base, Currency, Faction, Offer, OfferHistory, Role,
                          Transaction, User, get_db)
from app.misc import FactionPermission, check_faction_permission

PW_HASH = hash_password("pw")  # bcrypt is slow: hash once, not once per user per test

ALL = dict(
    accept_offers=True, create_offers=True, manage_funds=True,
    handle_members=True, manage_roles=True, manage_docs=True,
    view_transactions=True,
)


@pytest.fixture
def env():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    # Same session settings as production (autoflush off).
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    s = Session()
    s.add_all([
        Faction(faction_id=1, name="Alpha", is_approved=True),
        Faction(faction_id=2, name="Beta", is_approved=True),
        Faction(faction_id=3, name="Sans Faction", is_approved=True),
    ])
    s.commit()
    roles = [
        Role(role_id=1, name="Chef", faction_id=1, **ALL),
        Role(role_id=2, name="Marchand", faction_id=1, accept_offers=True,
             create_offers=True, view_transactions=True),
        Role(role_id=3, name="Membre", faction_id=1, view_transactions=True),
        Role(role_id=4, name="Chef Adjoint", faction_id=1, accept_offers=True,
             create_offers=True, handle_members=True, manage_roles=True,
             view_transactions=True),
        Role(role_id=5, name="Invité", faction_id=1),
        Role(role_id=6, name="Recruteur", faction_id=1, handle_members=True,
             view_transactions=True),
        Role(role_id=10, name="Chef", faction_id=2, **ALL),
        Role(role_id=11, name="Invité", faction_id=2),
        Role(role_id=20, name="Membre", faction_id=3, view_transactions=True),
        Role(role_id=21, name="Invité", faction_id=3),
        Role(role_id=22, name="Chef", faction_id=3, **ALL),
    ]
    s.add_all(roles)
    s.commit()

    def mk(uid, name, fid, rid, admin=False):
        return User(user_id=uid, username=name, hashed_password=PW_HASH,
                    faction_id=fid, role_id=rid, is_admin=admin)

    s.add_all([
        mk(1, "alice", 1, 1), mk(2, "bob", 1, 2), mk(3, "carol", 2, 10),
        mk(4, "dave", 1, 3), mk(5, "adjoint", 1, 4), mk(6, "recruteur", 1, 6),
        mk(7, "newbie", 3, 20), mk(8, "newbie2", 3, 20), mk(9, "invite", 1, 5),
        mk(10, "sanschef", 3, 22),
    ])
    s.add(Currency(name="Diamant", faction_id=1, total_in_circulation=0))
    s.commit()
    s.close()

    app = FastAPI()
    for module in (offer, user, faction, transactions, offer_history, documentation):
        app.include_router(module.router)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    client = TestClient(app, raise_server_exceptions=False)

    class Env:
        pass

    e = Env()
    e.client, e.Session = client, Session
    e.h = lambda name: {"Authorization": "Bearer " + create_access_token({"sub": name})}
    return e


def new_offer(env, who="alice", **over):
    body = dict(offer_type="SELL", item_description="Fer", currency_name="Diamant",
                price_per_unit=2.0, quantity=10, user_id=1)
    body.update(over)
    r = env.client.post("/offers/create", json=body, headers=env.h(who))
    assert r.status_code == 201, r.text
    return r.json()


def db_offer(env, offer_id=1):
    s = env.Session()
    o = s.get(Offer, offer_id)
    out = (o.quantity, o.status.value, o.price_per_unit)
    s.close()
    return out


def history(env, offer_id=1):
    s = env.Session()
    rows = [(h.action.value, h.actor_user_id, h.actor_faction_id)
            for h in s.query(OfferHistory).filter_by(offer_id=offer_id)
            .order_by(OfferHistory.history_id)]
    s.close()
    return rows


# ------------------------------------------------------------------ offers
class TestAcceptOffer:
    def test_returns_body_matching_response_model_and_records_purchase(self, env):
        new_offer(env)
        r = env.client.post("/offers/accept/1", json={"buyer_user_id": 2, "quantity": 4},
                            headers=env.h("bob"))
        assert r.status_code == 202, r.text
        assert set(r.json()) == {"offer_id", "transaction_id", "status"}
        assert r.json()["status"] == "OPEN"
        assert db_offer(env)[:2] == (6, "OPEN")
        s = env.Session()
        assert s.query(Transaction).count() == 1
        s.close()

    def test_full_purchase_closes_offer(self, env):
        new_offer(env)
        r = env.client.post("/offers/accept/1", json={"buyer_user_id": 2},
                            headers=env.h("bob"))
        assert r.status_code == 202 and r.json()["status"] == "CLOSED"
        assert db_offer(env)[:2] == (0, "CLOSED")

    @pytest.mark.parametrize("qty", [0, -5])
    def test_non_positive_quantity_rejected(self, env, qty):
        new_offer(env)
        r = env.client.post("/offers/accept/1", json={"buyer_user_id": 2, "quantity": qty},
                            headers=env.h("bob"))
        assert r.status_code == 422
        assert db_offer(env)[0] == 10  # untouched (was inflatable before)

    def test_cannot_buy_more_than_available_or_own_or_closed(self, env):
        new_offer(env)
        h = env.h("bob")
        assert env.client.post("/offers/accept/1", json={"buyer_user_id": 2, "quantity": 11},
                               headers=h).status_code == 400
        assert env.client.post("/offers/accept/1", json={"buyer_user_id": 1},
                               headers=env.h("alice")).status_code == 403
        env.client.post("/offers/accept/1", json={"buyer_user_id": 2}, headers=h)
        assert env.client.post("/offers/accept/1", json={"buyer_user_id": 2},
                               headers=h).status_code == 400

    def test_faction_purchase_is_logged_against_the_faction(self, env):
        new_offer(env, who="carol", user_id=3)
        r = env.client.post("/offers/accept/1", json={"buyer_faction_id": 1, "quantity": 1},
                            headers=env.h("bob"))
        assert r.status_code == 202, r.text
        assert history(env)[-1] == ("ACCEPTED", None, 1)


class TestOfferCreation:
    def test_requires_authentication(self, env):
        r = env.client.post("/offers/create", json=dict(
            offer_type="BUY", item_description="x", currency_name="Diamant",
            price_per_unit=1, quantity=1, user_id=1))
        assert r.status_code == 401

    def test_cannot_create_in_someone_elses_name(self, env):
        r = env.client.post("/offers/create", json=dict(
            offer_type="BUY", item_description="x", currency_name="Diamant",
            price_per_unit=1, quantity=1, user_id=1), headers=env.h("bob"))
        assert r.status_code == 403

    def test_exactly_one_owner(self, env):
        base = dict(offer_type="BUY", item_description="x", currency_name="Diamant",
                    price_per_unit=1, quantity=1)
        for owner in ({}, {"user_id": 2, "faction_id": 1}):
            r = env.client.post("/offers/create", json={**base, **owner}, headers=env.h("bob"))
            assert r.status_code == 400

    def test_faction_offer_needs_create_offers_in_that_faction(self, env):
        base = dict(offer_type="SELL", item_description="x", currency_name="Diamant",
                    price_per_unit=1, quantity=1, faction_id=1)
        assert env.client.post("/offers/create", json=base, headers=env.h("dave")).status_code == 403
        assert env.client.post("/offers/create", json={**base, "faction_id": 2},
                               headers=env.h("bob")).status_code == 403
        assert env.client.post("/offers/create", json=base, headers=env.h("bob")).status_code == 201

    @pytest.mark.parametrize("field,value", [("price_per_unit", 0), ("price_per_unit", -1),
                                             ("quantity", 0), ("quantity", -3),
                                             ("item_description", "")])
    def test_invalid_values_rejected(self, env, field, value):
        body = dict(offer_type="SELL", item_description="x", currency_name="Diamant",
                    price_per_unit=1, quantity=1, user_id=1)
        body[field] = value
        r = env.client.post("/offers/create", json=body, headers=env.h("alice"))
        assert r.status_code == 422

    def test_unknown_currency_is_a_clean_400(self, env):
        r = env.client.post("/offers/create", json=dict(
            offer_type="SELL", item_description="x", currency_name="Nope",
            price_per_unit=1, quantity=1, user_id=1), headers=env.h("alice"))
        assert r.status_code == 400 and "Nope" in r.json()["detail"]

    def test_init_quantity_is_set_by_the_server(self, env):
        created = new_offer(env, quantity=5, init_quantity=999)
        assert created["init_quantity"] == 5


class TestOfferModificationAndCancellation:
    def test_anonymous_cannot_modify_or_cancel(self, env):
        new_offer(env)
        assert env.client.put("/offers/update/1", json={"price_per_unit": 0.01}).status_code == 401
        assert env.client.delete("/offers/delete/1").status_code == 401
        assert db_offer(env)[1:] == ("OPEN", 2.0)

    def test_only_the_owner_can(self, env):
        new_offer(env)
        assert env.client.put("/offers/update/1", json={"price_per_unit": 1},
                              headers=env.h("bob")).status_code == 403
        assert env.client.delete("/offers/delete/1", headers=env.h("bob")).status_code == 403
        assert db_offer(env)[1:] == ("OPEN", 2.0)

    def test_owner_update_works_and_is_logged(self, env):
        new_offer(env)
        r = env.client.put("/offers/update/1", json={"price_per_unit": 3.5},
                           headers=env.h("alice"))
        assert r.status_code == 202, r.text
        assert db_offer(env)[2] == 3.5
        assert history(env) == [("CREATED", 1, None), ("UPDATED", 1, None)]

    def test_owner_cancel_works_and_is_logged(self, env):
        new_offer(env)
        assert env.client.delete("/offers/delete/1", headers=env.h("alice")).status_code == 204
        assert db_offer(env)[1] == "CANCELLED"
        assert history(env)[-1] == ("CANCELLED", 1, None)

    def test_cannot_reopen_or_close_by_hand_or_touch_finished_offers(self, env):
        new_offer(env)
        h = env.h("alice")
        for status in ("OPEN", "CLOSED"):
            assert env.client.put("/offers/update/1", json={"status": status},
                                  headers=h).status_code == 400
        env.client.delete("/offers/delete/1", headers=h)
        assert env.client.put("/offers/update/1", json={"price_per_unit": 1},
                              headers=h).status_code == 400
        assert env.client.delete("/offers/delete/1", headers=h).status_code == 400

    def test_faction_offer_managed_by_members_with_create_offers(self, env):
        new_offer(env, who="alice", user_id=None, faction_id=1)
        assert env.client.delete("/offers/delete/1", headers=env.h("dave")).status_code == 403
        assert env.client.delete("/offers/delete/1", headers=env.h("carol")).status_code == 403
        assert env.client.delete("/offers/delete/1", headers=env.h("bob")).status_code == 204
        assert history(env)[-1] == ("CANCELLED", None, 1)

    def test_unknown_offer_is_404(self, env):
        assert env.client.delete("/offers/delete/99", headers=env.h("alice")).status_code == 404


# ------------------------------------------------------------ members / roles
class TestJoiningAFaction:
    def test_joining_gives_the_guest_role_of_that_faction(self, env):
        r = env.client.patch("/users/update/7", json={"faction_id": 1, "role_id": 5},
                             headers=env.h("newbie"))
        assert r.status_code == 200, r.text
        s = env.Session()
        u = s.get(User, 7)
        assert (u.faction_id, u.role_id) == (1, 5)
        s.close()

    def test_role_is_not_up_to_the_client(self, env):
        # role 1 = Chef of Alpha: the old endpoint accepted this.
        r = env.client.patch("/users/update/7", json={"faction_id": 1, "role_id": 1},
                             headers=env.h("newbie"))
        assert r.status_code == 403
        r = env.client.patch("/users/update/7", json={"faction_id": 2, "role_id": 10},
                             headers=env.h("newbie"))
        assert r.status_code == 403
        s = env.Session()
        assert s.get(User, 7).faction_id == 3
        s.close()

    def test_role_only_update_on_self_is_refused(self, env):
        r = env.client.patch("/users/update/4", json={"role_id": 1}, headers=env.h("dave"))
        assert r.status_code == 403

    def test_joining_without_sending_a_role_works(self, env):
        r = env.client.patch("/users/update/7", json={"faction_id": 2}, headers=env.h("newbie"))
        assert r.status_code == 200
        s = env.Session()
        assert s.get(User, 7).role_id == 11
        s.close()

    def test_leaders_cannot_walk_out_but_unaffiliated_chef_can(self, env):
        assert env.client.patch("/users/update/1", json={"faction_id": 2},
                                headers=env.h("alice")).status_code == 403
        assert env.client.patch("/users/update/10", json={"faction_id": 2},
                                headers=env.h("sanschef")).status_code == 200

    def test_other_invalid_joins(self, env):
        h = env.h("newbie")
        assert env.client.patch("/users/update/7", json={"faction_id": 3}, headers=h).status_code == 400
        assert env.client.patch("/users/update/7", json={"faction_id": 999}, headers=h).status_code == 404
        assert env.client.patch("/users/update/4", json={"faction_id": 1},
                                headers=env.h("dave")).status_code == 400
        assert env.client.patch("/users/update/7", json={}, headers=h).status_code == 200

    def test_requires_authentication_and_existing_user(self, env):
        assert env.client.patch("/users/update/7", json={"faction_id": 1}).status_code == 401
        assert env.client.patch("/users/update/99", json={"role_id": 3},
                                headers=env.h("alice")).status_code == 404


class TestAssigningRoles:
    def assign(self, env, who, target, role_id, **extra):
        return env.client.patch(f"/users/update/{target}", json={"role_id": role_id, **extra},
                                headers=env.h(who))

    def test_leader_can_promote_a_guest(self, env):
        assert self.assign(env, "alice", 9, 3).status_code == 200
        s = env.Session()
        assert s.get(User, 9).role_id == 3
        s.close()

    def test_needs_handle_members(self, env):
        assert self.assign(env, "dave", 9, 3).status_code == 403
        assert self.assign(env, "bob", 9, 3).status_code == 403

    def test_other_factions_are_off_limits(self, env):
        assert self.assign(env, "carol", 9, 3).status_code == 403           # target elsewhere
        assert self.assign(env, "alice", 9, 11).status_code == 404          # role elsewhere
        assert self.assign(env, "alice", 9, 3, faction_id=2).status_code == 403  # move out

    def test_leader_role_untouchable(self, env):
        assert self.assign(env, "adjoint", 9, 1).status_code == 403         # assign Chef
        assert self.assign(env, "adjoint", 1, 3).status_code == 403         # demote the Chef

    def test_cannot_hand_out_powers_you_lack(self, env):
        # "recruteur" has handle_members only; Chef Adjoint carries manage_roles
        assert self.assign(env, "recruteur", 9, 4).status_code == 403
        assert self.assign(env, "recruteur", 9, 3).status_code == 200       # Membre: fine

    def test_stale_role_from_another_faction_grants_nothing(self, env):
        s = env.Session()
        s.get(User, 4).role_id = 1          # dave holds Alpha's Chef role...
        s.get(User, 4).faction_id = 2       # ...but sits in Beta
        s.commit()
        s.close()
        with pytest.raises(HTTPException) as e:
            s = env.Session()
            check_faction_permission(s.get(User, 4), FactionPermission.MANAGE_ROLES)
        assert e.value.status_code == 403


# ---------------------------------------------------------------- factions
class TestFactions:
    def test_creation_works_without_any_documents_folder(self, env, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)  # no documents/AOS anywhere
        r = env.client.post("/factions/create", json={"name": "Gamma"}, headers=env.h("newbie"))
        assert r.status_code == 201, r.text
        s = env.Session()
        assert s.get(User, 7).faction_id == r.json()["faction_id"]
        s.close()

    def test_names_sharing_a_documents_folder_are_refused(self, env):
        assert env.client.post("/factions/create", json={"name": "Team 1"},
                               headers=env.h("newbie")).status_code == 201
        r = env.client.post("/factions/create", json={"name": "Team 2"}, headers=env.h("newbie2"))
        assert r.status_code == 400 and "similar" in r.json()["detail"]

    def test_names_without_letters_are_refused(self, env):
        r = env.client.post("/factions/create", json={"name": "1234"}, headers=env.h("newbie"))
        assert r.status_code == 400

    def test_rename_cannot_collide_either(self, env):
        r = env.client.put("/factions/update/1", json={"name": "beta 7"}, headers=env.h("alice"))
        assert r.status_code == 400
        assert env.client.put("/factions/update/1", json={"name": "Alpha Prime"},
                              headers=env.h("alice")).status_code == 202

    def test_delete_of_a_still_referenced_faction_is_a_409_not_a_500(self):
        db = MagicMock()
        db.commit.side_effect = IntegrityError("stmt", {}, Exception("fk"))
        with pytest.raises(HTTPException) as e:
            faction_crud.delete_faction(db, MagicMock())
        assert e.value.status_code == 409
        db.rollback.assert_called_once()


# ------------------------------------------- transactions / history visibility
class TestVisibility:
    def trade(self, env):
        new_offer(env)                                              # alice sells (user offer 1)
        new_offer(env, who="alice", user_id=None, faction_id=1)     # Alpha sells (faction offer 2)
        env.client.post("/offers/accept/1", json={"buyer_user_id": 2}, headers=env.h("bob"))
        env.client.post("/offers/accept/2", json={"buyer_user_id": 3}, headers=env.h("carol"))

    def ids(self, r):
        return sorted(t["offer_id"] for t in r.json())

    def test_anonymous_is_refused(self, env):
        assert env.client.get("/transactions/").status_code == 401
        assert env.client.get("/history").status_code == 401

    def test_transactions_only_for_people_involved(self, env):
        self.trade(env)
        get = lambda who, q="": env.client.get(f"/transactions/{q}", headers=env.h(who))
        assert self.ids(get("bob")) == [1, 2]       # bought #1; Alpha member with view_transactions -> Alpha's #2
        assert self.ids(get("carol")) == [2]        # bought #2
        assert self.ids(get("alice")) == [1, 2]     # sold #1, and Alpha's #2 (view_transactions)
        assert self.ids(get("dave")) == [2]         # Alpha member with view_transactions
        assert get("invite").json() == []           # guest: no view_transactions, no part in trades
        assert get("newbie").json() == []

    def test_filters_narrow_but_never_widen(self, env):
        self.trade(env)
        get = lambda who, q: env.client.get(f"/transactions/?{q}", headers=env.h(who))
        assert self.ids(get("alice", "faction_id=1")) == [2]
        assert self.ids(get("alice", "user_id=1")) == [1]
        assert get("newbie", "user_id=3").json() == []          # unrelated viewer: nothing
        assert self.ids(get("bob", "user_id=3")) == [2]         # only via Alpha's own offer
        assert get("newbie", "faction_id=1").json() == []

    def test_history_is_scoped_too(self, env):
        self.trade(env)
        get = lambda who, q="": env.client.get(f"/history{q}", headers=env.h(who))
        assert {h["offer_id"] for h in get("alice").json()} == {1, 2}
        assert {h["offer_id"] for h in get("bob").json()} == {1, 2}  # own #1 + Alpha's #2
        assert get("invite").json() == []      # guest: no view_transactions
        assert get("newbie").json() == []
        assert get("newbie", "?offer_id=1").json() == []
        assert {h["offer_id"] for h in get("alice", "?offer_id=2").json()} == {2}


# --------------------------------------------------------------- documents
class TestDocuments:
    def test_path_traversal_is_blocked(self, env):
        probe = Path(documentation.DOCS_DIR).parent / "zz_probe_doc.md"
        probe.write_text("# outside the documents folder")
        try:
            r = env.client.get("/documents/%2e%2e/doc/zz_probe_doc")
            assert r.status_code == 404
            r = env.client.get("/documents/%2e%2e/faction_doc/%2e%2e/zz_probe_doc")
            assert r.status_code == 404
        finally:
            probe.unlink()

    def test_documents_are_found_whatever_the_working_directory(self, env, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        r = env.client.get("/documents/CubeCrusaders/faction_doc/lois/territoires")
        assert r.status_code == 200 and "Territoires" in r.json()["content"]

    def test_nta_contract_page_resolves_despite_normalize_lowercasing(self, env):
        r = env.client.get("/documents/CubeCrusaders/faction_doc/marches/contractNTA")
        assert r.status_code == 200 and "slot" in r.json()["content"]

    def test_unknown_document_is_404(self, env):
        assert env.client.get("/documents/CubeCrusaders/doc/nope").status_code == 404

    def test_creating_a_document_needs_manage_docs(self, env, monkeypatch, tmp_path):
        monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
        body = {"title": "Reglement", "content": "hello"}
        assert env.client.post("/documents/create", json=body, headers=env.h("dave")).status_code == 403
        assert env.client.post("/documents/create", json=body).status_code == 401
        assert env.client.post("/documents/create", json=body, headers=env.h("alice")).status_code == 201
        assert env.client.post("/documents/create", json={"title": "123", "content": "x"},
                               headers=env.h("alice")).status_code == 400
