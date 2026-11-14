"""A faction's leader deletes it: it is archived, its members are freed."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import documentation, join_requests
from app.database import Currency, Faction, Offer, Role, User
from app.misc import OfferStatus


def _member(env, user_id=10, name="rory", role_name="Recrue"):  # noqa: F811
    s = env.Session()
    role = Role(role_id=30 + user_id, name=role_name, faction_id=1)
    s.add(role)
    s.commit()
    s.add(
        User(
            user_id=user_id,
            username=name,
            hashed_password=PW_HASH,
            faction_id=1,
            role_id=role.role_id,
        )
    )
    s.commit()
    s.close()


def _delete(env, who="alice", faction_id=1):  # noqa: F811
    return env.client.delete(f"/factions/delete/{faction_id}", headers=env.h(who))


def test_the_leader_deletes_the_faction_and_frees_the_members(env):  # noqa: F811
    _member(env)
    assert _delete(env).status_code == 204

    s = env.Session()
    for user_id in (1, 10):
        user = s.get(User, user_id)
        assert user.faction.name == "Sans Faction"
        assert user.role.name == "Membre"
    faction = s.get(Faction, 1)
    assert faction.deleted_at is not None
    assert faction.name.startswith("Alpha [supprimée #1]")
    s.close()


def test_a_deleted_faction_leaves_the_listings_but_keeps_its_page(env):  # noqa: F811
    _delete(env)
    ids = [f["faction_id"] for f in env.client.get("/factions/list").json()]
    assert 1 not in ids
    assert 1 not in env.client.get("/factions/member_counts").json()
    detail = env.client.get("/factions/detail/1").json()
    assert detail["deleted_at"] is not None  # past trades still show its name


def test_its_name_is_free_again(env):  # noqa: F811
    _delete(env)
    r = env.client.post(
        "/factions/create",
        json={"name": "Alpha", "description": "again"},
        headers=env.h("alice"),
    )
    assert r.status_code == 201


def test_only_the_leader_or_an_admin_can_delete(env):  # noqa: F811
    _member(env)
    assert _delete(env, "rory").status_code == 403
    assert _delete(env, "newbie").status_code == 403
    assert env.client.delete("/factions/delete/1").status_code == 401
    assert env.Session().get(Faction, 1).deleted_at is None


def test_the_no_faction_faction_cannot_be_deleted(env):  # noqa: F811
    s = env.Session()
    no_faction = s.query(Faction).filter_by(name="Sans Faction").one()
    fid = no_faction.faction_id
    s.close()
    assert _delete(env, "alice", fid).status_code in (400, 403)


def test_deleting_twice_is_a_404(env):  # noqa: F811
    assert _delete(env).status_code == 204
    assert _delete(env).status_code == 404
    assert _delete(env, faction_id=999).status_code == 404


def test_open_offers_are_cancelled_and_nobody_can_join_any_more(env):  # noqa: F811
    r = env.client.post(
        "/offers/create",
        json={
            "offer_type": "SELL",
            "item_description": "épée",
            "currency_name": "Diamant",
            "price_per_unit": 1,
            "quantity": 3,
            "faction_id": 1,
        },
        headers=env.h("alice"),
    )
    assert r.status_code == 201, r.text
    oid = r.json()["offer_id"]
    assert _delete(env).status_code == 204

    s = env.Session()
    assert s.get(Offer, oid).status == OfferStatus.CANCELLED
    s.close()
    # Nobody can join a deleted faction any more
    r = env.client.patch("/users/join/1", headers=env.h("newbie"))
    assert r.status_code == 404


def test_pending_join_requests_are_withdrawn(env):  # noqa: F811
    env.client.app.include_router(join_requests.router)
    s = env.Session()
    s.get(Faction, 1).requires_approval = True
    s.commit()
    s.close()
    r = env.client.post(
        "/join_requests", json={"faction_id": 1}, headers=env.h("newbie")
    )
    assert r.status_code == 201
    assert _delete(env).status_code == 204
    r = env.client.get("/join_requests/mine", headers=env.h("newbie"))
    assert r.json() is None
    r = env.client.post(
        "/join_requests", json={"faction_id": 1}, headers=env.h("newbie")
    )
    assert r.status_code == 404
    s = env.Session()
    assert s.query(User).filter_by(username="newbie").one().faction.name == (
        "Sans Faction"
    )
    s.close()


def test_the_currency_goes_unless_trades_use_it(env):  # noqa: F811
    assert _delete(env).status_code == 204
    s = env.Session()
    assert s.query(Currency).filter_by(faction_id=1).count() == 0
    s.close()


def test_documents_are_archived_not_lost(env, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    h = env.h("alice")
    env.client.post(
        "/documents/create", json={"title": "Règles", "content": "x"}, headers=h
    )
    assert _delete(env).status_code == 204
    root = tmp_path / "documents" / "AOS"
    assert not (root / "alpha").exists()
    assert (root / "_archive" / "alpha-1" / "regles.md").is_file()
    assert env.client.get("/documents/faction/1").json() == []


def test_a_failed_deletion_puts_the_documents_back(
    env, monkeypatch, tmp_path
):  # noqa: F811
    from sqlalchemy.orm import Session

    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    env.client.post(
        "/documents/create",
        json={"title": "Règles", "content": "x"},
        headers=env.h("alice"),
    )

    def failing_commit(self):
        raise RuntimeError("database down")

    env.client.raise_server_exceptions = False
    with monkeypatch.context() as m:
        m.setattr(Session, "commit", failing_commit)
        assert _delete(env).status_code == 500

    # The folder came back and the faction is untouched
    assert (tmp_path / "documents" / "AOS" / "alpha" / "regles.md").is_file()
    assert not (tmp_path / "documents" / "AOS" / "_archive" / "alpha-1").exists()
    s = env.Session()
    assert s.get(Faction, 1).deleted_at is None
    assert s.get(User, 1).faction.name == "Alpha"
    s.close()
