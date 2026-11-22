"""Currencies shared between factions: issuers, requests and invitations,
renames, and the money admin."""

import pytest
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import admin, admin_market
from app.database import (AuditLog, CurrencyFaction, CurrencyHistory, Faction,
                          GlobalRole, Role, User)

DIAMANT = 1  # the currency of the fixture, issued by Alpha (1)


@pytest.fixture
def senv(env):  # noqa: F811
    """Alpha (alice, manage_funds) issues Diamant. Beta has bob (manage_funds)
    and carl (no permission). Gamma has gus (manage_funds). mona is a money
    admin in no real faction."""
    env.client.app.include_router(admin.router)
    env.client.app.include_router(admin_market.router)
    s = env.Session()
    s.add_all(
        [
            Faction(faction_id=2, name="Beta", is_approved=True),
            Faction(faction_id=4, name="Gamma", is_approved=True),
        ]
    )
    s.commit()
    s.add_all(
        [
            Role(role_id=2, name="Trésorier", faction_id=2, manage_funds=True),
            Role(role_id=3, name="Membre", faction_id=2),
            Role(role_id=4, name="Trésorier", faction_id=4, manage_funds=True),
        ]
    )
    s.commit()
    for user_id, name, faction_id, role_id in (
        (10, "bob", 2, 2),
        (11, "carl", 2, 3),
        (12, "gus", 4, 4),
        (13, "mona", 3, 20),
    ):
        s.add(
            User(
                user_id=user_id,
                username=name,
                hashed_password=PW_HASH,
                faction_id=faction_id,
                role_id=role_id,
            )
        )
    s.commit()
    s.add(GlobalRole(user_id=13, role="money_admin"))
    s.commit()
    s.close()
    return env


def _links(env):
    s = env.Session()
    rows = sorted(
        (link.faction_id, link.is_issuer)
        for link in s.query(CurrencyFaction).filter_by(currency_id=DIAMANT)
    )
    s.close()
    return rows


def _audit(env):
    s = env.Session()
    rows = [(a.actor_name, a.action) for a in s.query(AuditLog).order_by("log_id")]
    s.close()
    return rows


def _join(env, faction_user="bob"):
    """`faction_user`'s faction asks for Diamant and alice accepts."""
    c = env.client
    r = c.post(f"/currencies/{DIAMANT}/links/request", headers=env.h(faction_user))
    assert r.status_code == 201, r.text
    rid = r.json()["request_id"]
    r = c.post(f"/currencies/links/{rid}/accept", headers=env.h("alice"))
    assert r.status_code == 200, r.text
    return rid


# ── Renaming ──────────────────────────────────────────────────────────────


def test_a_used_currency_can_be_renamed(senv):
    c, h = senv.client, senv.h("alice")
    offer = {
        "offer_type": "SELL",
        "item_description": "Fer",
        "currency_name": "Diamant",
        "price_per_unit": 2,
        "quantity": 3,
        "user_id": 1,
    }
    r = c.post("/offers/create", json=offer, headers=h)
    assert r.status_code == 201, r.text
    offer_id = r.json()["offer_id"]
    assert r.json()["currency_id"] == DIAMANT

    r = c.put(f"/currencies/update/{DIAMANT}", json={"name": "Rubis"}, headers=h)
    assert r.status_code == 202, r.text
    assert r.json()["name"] == "Rubis"

    # the offer follows; the old name is free and no longer known
    assert (
        c.get(f"/offers/detail/{offer_id}", headers=h).json()["currency_name"]
        == "Rubis"
    )
    offer["currency_name"] = "Diamant"
    assert c.post("/offers/create", json=offer, headers=h).status_code == 400

    # the rename is in the history, with the total unchanged
    history = c.get(f"/currencies/history/{DIAMANT}", headers=h).json()
    assert history[0]["currency_name"] == "Rubis"
    assert "Diamant" in history[0]["notes"] and "Rubis" in history[0]["notes"]
    assert history[0]["old_total_in_circulation"] == (
        history[0]["new_total_in_circulation"]
    )


def test_a_rename_to_a_taken_name_is_a_409(senv):
    c = senv.client
    r = c.post(
        "/currencies/create",
        json={"name": "Or", "faction_id": 2},
        headers=senv.h("bob"),
    )
    assert r.status_code == 201, r.text
    r = c.put(
        f"/currencies/update/{DIAMANT}", json={"name": "Or"}, headers=senv.h("alice")
    )
    assert r.status_code == 409
    s = senv.Session()
    assert s.query(CurrencyHistory).count() == 0  # nothing half-done
    s.close()


# ── Requests and invitations ──────────────────────────────────────────────


def test_a_faction_asks_and_an_issuer_accepts(senv):
    c = senv.client
    # carl has no manage_funds: he can't ask for his faction
    assert (
        c.post(f"/currencies/{DIAMANT}/links/request", headers=senv.h("carl"))
    ).status_code == 403
    r = c.post(f"/currencies/{DIAMANT}/links/request", headers=senv.h("bob"))
    assert r.status_code == 201
    rid = r.json()["request_id"]
    assert r.json()["kind"] == "REQUEST" and r.json()["faction_name"] == "Beta"
    # one pending request at a time
    assert (
        c.post(f"/currencies/{DIAMANT}/links/request", headers=senv.h("bob"))
    ).status_code == 409

    # the issuer sees it; the asking faction can't accept its own request
    pending = c.get(f"/currencies/{DIAMANT}/links", headers=senv.h("alice")).json()
    assert [p["request_id"] for p in pending] == [rid]
    assert (
        c.post(f"/currencies/links/{rid}/accept", headers=senv.h("bob"))
    ).status_code == 403
    assert (
        c.post(f"/currencies/links/{rid}/accept", headers=senv.h("alice"))
    ).status_code == 200
    assert _links(senv) == [(1, True), (2, False)]

    # Beta's members see the total; a user faction may not change the currency
    mine = c.get("/currencies/faction/2", headers=senv.h("carl")).json()
    assert "total_in_circulation" in mine and mine["can_manage"] is False
    outsider = c.get("/currencies/faction/2", headers=senv.h("gus")).json()
    assert "total_in_circulation" not in outsider
    r = c.put(
        f"/currencies/update/{DIAMANT}", json={"symbol": "D"}, headers=senv.h("bob")
    )
    assert r.status_code == 403


def test_an_issuer_invites_and_the_faction_accepts(senv):
    c = senv.client
    r = c.post(
        f"/currencies/{DIAMANT}/links/invite",
        json={"faction_id": 2},
        headers=senv.h("alice"),
    )
    assert r.status_code == 201
    rid = r.json()["request_id"]
    assert r.json()["kind"] == "INVITATION"

    # nobody signs a faction up on its behalf, not even a money admin
    for who in ("alice", "mona", "carl", "gus"):
        assert (
            c.post(f"/currencies/links/{rid}/accept", headers=senv.h(who))
        ).status_code == 403, who
    assert [
        p["request_id"]
        for p in c.get("/currencies/links/faction/2", headers=senv.h("bob")).json()
    ] == [rid]
    assert (
        c.post(f"/currencies/links/{rid}/accept", headers=senv.h("bob"))
    ).status_code == 200
    assert _links(senv) == [(1, True), (2, False)]
    # already dealt with
    assert (
        c.post(f"/currencies/links/{rid}/refuse", headers=senv.h("bob"))
    ).status_code == 409


def test_refusing_and_withdrawing(senv):
    c = senv.client
    rid = c.post(
        f"/currencies/{DIAMANT}/links/invite",
        json={"faction_id": 2},
        headers=senv.h("alice"),
    ).json()["request_id"]
    assert (c.post(f"/currencies/links/{rid}/refuse", headers=senv.h("bob"))).json()[
        "status"
    ] == "REFUSED"

    rid = c.post(f"/currencies/{DIAMANT}/links/request", headers=senv.h("bob")).json()[
        "request_id"
    ]
    # only the asking side withdraws
    r = c.delete(
        f"/currencies/links/{rid}", headers=senv.h("alice")
    )
    assert r.status_code == 403
    r = c.delete(f"/currencies/links/{rid}", headers=senv.h("bob"))
    assert r.status_code == 204
    assert _links(senv) == [(1, True)]


def test_a_faction_uses_one_currency_at_most(senv):
    c = senv.client
    r = c.post(
        "/currencies/create",
        json={"name": "Or", "faction_id": 2},
        headers=senv.h("bob"),
    )
    assert r.status_code == 201
    assert [(f["faction_name"], f["is_issuer"]) for f in r.json()["factions"]] == [
        ("Beta", True)
    ]
    assert (
        c.post(f"/currencies/{DIAMANT}/links/request", headers=senv.h("bob"))
    ).status_code == 409
    assert (
        c.post(
            f"/currencies/{DIAMANT}/links/invite",
            json={"faction_id": 2},
            headers=senv.h("alice"),
        )
    ).status_code == 409


# ── Issuers ───────────────────────────────────────────────────────────────


def test_a_currency_keeps_at_least_one_issuer(senv):
    c, h = senv.client, senv.h("alice")
    delete_issuer_response = c.delete(
        f"/currencies/{DIAMANT}/factions/1/issuer", headers=h
    )
    assert delete_issuer_response.status_code == 409
    r = c.delete(f"/currencies/{DIAMANT}/factions/1", headers=h)
    assert r.status_code == 409

    _join(senv)
    r = c.put(f"/currencies/{DIAMANT}/factions/2/issuer", headers=h)
    assert r.status_code == 200
    assert [f["is_issuer"] for f in r.json()["factions"]] == [True, True]
    # now Beta issues too: bob may change the currency, and Alpha may step down
    r = c.put(
        f"/currencies/update/{DIAMANT}", json={"symbol": "D"}, headers=senv.h("bob")
    )
    assert r.status_code == 202
    response = c.delete(
        f"/currencies/{DIAMANT}/factions/1/issuer", headers=h
    )
    assert response.status_code == 200
    assert _links(senv) == [(1, False), (2, True)]
    # alice's faction no longer issues it
    assert (
        c.put(f"/currencies/update/{DIAMANT}", json={"symbol": "X"}, headers=h)
    ).status_code == 403
    assert _audit(senv) == []  # no override in any of this


def test_a_faction_leaves_or_is_removed(senv):
    c = senv.client
    _join(senv)
    # carl can't make his faction leave; bob can
    assert (
        c.delete(f"/currencies/{DIAMANT}/factions/2", headers=senv.h("carl"))
    ).status_code == 403
    response = c.delete(f"/currencies/{DIAMANT}/factions/2", headers=senv.h("bob"))
    assert response.status_code == 200
    assert _links(senv) == [(1, True)]

    _join(senv)
    response = c.delete(f"/currencies/{DIAMANT}/factions/2", headers=senv.h("alice"))
    assert response.status_code == 200
    assert _links(senv) == [(1, True)]
    response = c.delete(f"/currencies/{DIAMANT}/factions/2", headers=senv.h("alice"))
    assert response.status_code == 404


# ── The money admin ───────────────────────────────────────────────────────


def test_a_money_admin_runs_every_currency_and_is_audited(senv):
    c, h = senv.client, senv.h("mona")
    # a plain outsider can't
    assert (
        c.put(
            f"/currencies/update/{DIAMANT}", json={"symbol": "G"}, headers=senv.h("gus")
        )
    ).status_code == 403

    r = c.put(
        f"/currencies/update/{DIAMANT}",
        json={"name": "Saphir", "total_in_circulation": 40},
        headers=h,
    )
    assert r.status_code == 202, r.text
    assert r.json()["can_manage"] is True
    assert c.get(f"/currencies/history/{DIAMANT}", headers=h).status_code == 200

    rid = c.post(f"/currencies/{DIAMANT}/links/request", headers=senv.h("bob")).json()[
        "request_id"
    ]
    assert c.post(f"/currencies/links/{rid}/accept", headers=h).status_code == 200
    assert c.put(f"/currencies/{DIAMANT}/factions/2/issuer", headers=h).status_code == (
        200
    )
    delete_resp = c.delete(f"/currencies/{DIAMANT}/factions/1", headers=h)
    assert delete_resp.status_code == 200
    assert _links(senv) == [(2, True)]

    assert [a for a in _audit(senv)] == [
        ("mona", "currency_changed"),
        ("mona", "currency_faction_added"),
        ("mona", "currency_issuer_changed"),
        ("mona", "currency_faction_removed"),
    ]

    # mona reads the currency part of the trail, nothing else
    trail = c.get("/admin/audit", headers=h)
    assert trail.status_code == 200
    assert {e["target_type"] for e in trail.json()} == {"currency"}
    assert trail.json()[-1]["detail"] == "nom → Saphir, total 0 → 40"


def test_a_refused_override_leaves_no_trace(senv):
    senv.client.post(
        "/currencies/create",
        json={"name": "Or", "faction_id": 2},
        headers=senv.h("bob"),
    )
    r = senv.client.put(
        f"/currencies/update/{DIAMANT}", json={"name": "Or"}, headers=senv.h("mona")
    )
    assert r.status_code == 409
    # the last issuer can't be removed, even by a money admin
    r = senv.client.delete(f"/currencies/{DIAMANT}/factions/1", headers=senv.h("mona"))
    assert r.status_code == 409
    assert _audit(senv) == []


def test_the_currency_list_is_public(senv):
    r = senv.client.get("/currencies", headers=senv.h("gus"))
    assert r.status_code == 200
    (diamant,) = r.json()
    assert diamant["name"] == "Diamant" and "total_in_circulation" not in diamant
    assert diamant["factions"][0]["faction_name"] == "Alpha"


def test_deleting_a_faction_keeps_its_currency_run(senv):
    c = senv.client
    _join(senv)
    # Alpha is the last issuer: its (archived) link stays, so the currency is
    # never left without one; a money admin can name another issuer later
    r = c.delete("/factions/delete/1", headers=senv.h("alice"))
    assert r.status_code == 204
    assert _links(senv) == [(1, True), (2, False)]


def test_deleting_a_faction_drops_its_link_and_invitations(senv):
    c = senv.client
    _join(senv, "bob")
    c.post(
        f"/currencies/{DIAMANT}/links/invite",
        json={"faction_id": 4},
        headers=senv.h("alice"),
    )
    # Gamma's and Beta's leaders delete their factions
    s = senv.Session()
    s.add_all(
        [
            Role(role_id=5, name="Chef", faction_id=4, manage_funds=True),
            Role(role_id=6, name="Chef", faction_id=2, manage_funds=True),
        ]
    )
    s.commit()
    s.query(User).filter_by(user_id=12).update({"role_id": 5})
    s.query(User).filter_by(user_id=10).update({"role_id": 6})
    s.commit()
    s.close()
    delete_gamma = c.delete("/factions/delete/4", headers=senv.h("gus"))
    assert delete_gamma.status_code == 204
    delete_beta = c.delete("/factions/delete/2", headers=senv.h("bob"))
    assert delete_beta.status_code == 204
    assert c.get(f"/currencies/{DIAMANT}/links", headers=senv.h("alice")).json() == []
    assert _links(senv) == [(1, True)]


def test_a_money_admin_has_the_currency_admin_tools(senv):
    c = senv.client
    listed = c.get("/admin/currencies", headers=senv.h("mona"))
    assert listed.status_code == 200
    assert [x["name"] for x in listed.json()] == ["Diamant"]
    r = c.post(
        "/admin/currencies",
        json={"name": "Or", "faction_id": 4},
        headers=senv.h("mona"),
    )
    assert r.status_code == 201
    # the rest of the admin tools stay for admins
    assert c.get("/admin/offers", headers=senv.h("mona")).status_code == 403
    assert c.get("/admin/currencies", headers=senv.h("bob")).status_code == 403
