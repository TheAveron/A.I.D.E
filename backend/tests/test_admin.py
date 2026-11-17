"""The administration panel's API and the audit trail."""

import pytest
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)
from test_trains import tenv  # noqa: F401  (pytest fixture)

from app.api import admin
from app.database import AuditLog, Faction, Role, User


@pytest.fixture
def aenv(tenv):  # noqa: F811
    """tenv (train routers, "rails" train admin, "root" admin, "mina"/"rory"
    in Alpha) + the admin router."""
    tenv.client.app.include_router(admin.router)
    tenv.audit = lambda who="root", **p: tenv.client.get(
        "/admin/audit", params=p, headers=tenv.h(who)
    )
    return tenv


def _entries(aenv, who="root", **params):
    r = aenv.audit(who, **params)
    assert r.status_code == 200, r.text
    return [
        (e["actor_name"], e["action"], e["target_name"], e["detail"]) for e in r.json()
    ]


def test_only_staff_read_the_audit_trail(aenv):
    assert aenv.audit("alice").status_code == 403
    assert aenv.audit("newbie").status_code == 403
    assert aenv.audit("root").status_code == 200
    assert aenv.audit("rails").status_code == 200
    assert aenv.client.get("/admin/audit").status_code == 401
    assert aenv.audit("root", limit=0).status_code == 422
    assert aenv.audit("root", limit=201).status_code == 422


def test_granting_and_revoking_roles_is_recorded(aenv):
    # the grant of "rails" in the fixture is already there
    assert _entries(aenv) == [("root", "role_granted", "rails", "train_admin")]
    aenv.client.put("/global-roles/42/train_admin", headers=aenv.h("root"))  # again
    aenv.client.delete("/global-roles/42/train_admin", headers=aenv.h("root"))
    aenv.client.delete("/global-roles/42/train_admin", headers=aenv.h("root"))  # again
    assert _entries(aenv) == [
        ("root", "role_revoked", "rails", "train_admin"),
        ("root", "role_granted", "rails", "train_admin"),
    ]


def test_filters_and_paging(aenv):
    aenv.client.delete("/global-roles/42/train_admin", headers=aenv.h("root"))
    assert [e[1] for e in _entries(aenv, action="role_revoked")] == ["role_revoked"]
    assert _entries(aenv, target_type="faction") == []
    assert len(_entries(aenv, limit=1)) == 1
    assert len(_entries(aenv, skip=1)) == 1


def _train(aenv, who="newbie", **kw):
    aenv.line("A") if aenv.client.get("/lines/A").status_code == 404 else None
    return aenv.train(who, **{"line": "A", "service": "O", **kw})


def test_a_train_admin_overriding_an_owner_is_recorded(aenv):
    tid = _train(aenv).json()["train_id"]
    put = lambda who, **b: aenv.client.put(  # noqa: E731
        f"/trains/{tid}", json=b, headers=aenv.h(who)
    )
    assert put("newbie", common_name="Moi").status_code == 200  # the owner: nothing
    assert put("rails", service="E").status_code == 200
    assert _entries(aenv, "root", target_type="train") == [
        ("rails", "train_changed", "A-O01 Moi", "A-O01 Moi -> A-E01 Moi")
    ]
    assert (
        aenv.client.delete(f"/trains/{tid}", headers=aenv.h("rails")).status_code == 204
    )
    assert _entries(aenv, "root", target_type="train")[0][:3] == (
        "rails",
        "train_retired",
        "A-E01 Moi",
    )


def test_a_train_admin_on_their_own_things_leaves_no_trace(aenv):
    tid = _train(aenv, "rails").json()["train_id"]
    aenv.client.put(
        f"/trains/{tid}", json={"common_name": "x"}, headers=aenv.h("rails")
    )
    aenv.client.delete(f"/trains/{tid}", headers=aenv.h("rails"))
    s = aenv.client.post(
        "/stations", json={"name": "Mine", "x": 1, "z": 1}, headers=aenv.h("rails")
    ).json()["station_id"]
    aenv.client.put(f"/stations/{s}", json={"x": 2}, headers=aenv.h("rails"))
    aenv.client.delete(f"/stations/{s}", headers=aenv.h("rails"))
    assert _entries(aenv, target_type="train") == []
    assert _entries(aenv, target_type="station") == []


def test_lines_and_stations_overrides_are_recorded(aenv):
    aenv.line("A", who="mina")  # a line of Alpha
    assert (
        aenv.client.put(
            "/lines/A", json={"name": "Nord"}, headers=aenv.h("mina")
        ).status_code
        == 200
    )
    assert (
        aenv.client.put(
            "/lines/A", json={"name": "Sud"}, headers=aenv.h("rails")
        ).status_code
        == 200
    )
    sid = aenv.client.post(
        "/stations", json={"name": "Alpha", "x": 1, "z": 1}, headers=aenv.h("alice")
    ).json()["station_id"]
    assert (
        aenv.client.put(
            "/lines/A/stops", json={"station_ids": [sid]}, headers=aenv.h("rails")
        ).status_code
        == 200
    )
    assert (
        aenv.client.put(
            f"/stations/{sid}", json={"x": 5}, headers=aenv.h("alice")
        ).status_code
        == 200
    )
    assert (
        aenv.client.put(
            f"/stations/{sid}", json={"x": 6}, headers=aenv.h("rails")
        ).status_code
        == 200
    )
    aenv.client.put("/lines/A/stops", json={"station_ids": []}, headers=aenv.h("rails"))
    assert (
        aenv.client.delete(f"/stations/{sid}", headers=aenv.h("rails")).status_code
        == 204
    )
    assert aenv.client.delete("/lines/A", headers=aenv.h("rails")).status_code == 204
    assert [(e[0], e[1], e[2]) for e in _entries(aenv, target_type="line")] == [
        ("rails", "line_deleted", "A"),
        ("rails", "line_changed", "A"),  # stops emptied
        ("rails", "line_changed", "A"),  # stops set
        ("rails", "line_changed", "A"),  # renamed
    ]
    assert [(e[1], e[2]) for e in _entries(aenv, target_type="station")] == [
        ("station_deleted", "Alpha"),
        ("station_changed", "Alpha"),
    ]


def test_a_train_admin_only_reads_train_matters(aenv):
    tid = _train(aenv).json()["train_id"]
    aenv.client.put(
        f"/trains/{tid}", json={"common_name": "x"}, headers=aenv.h("rails")
    )
    all_actions = {e[1] for e in _entries(aenv, "root")}
    assert {"role_granted", "train_changed"} <= all_actions
    seen = {e[1] for e in _entries(aenv, "rails")}
    assert seen == {"train_changed"}
    # asking for another kind does not widen what they see
    assert _entries(aenv, "rails", action="role_granted") == []
    assert _entries(aenv, "rails", target_type="user") == []


def test_users_can_be_searched_by_admins_only(aenv):
    get = lambda who, **p: aenv.client.get(
        "/admin/users", params=p, headers=aenv.h(who)
    )  # noqa: E731
    assert get("alice").status_code == 403
    assert get("rails").status_code == 403  # a train admin is not an admin
    r = get("root")
    assert r.status_code == 200
    names = [u["username"] for u in r.json()]
    assert names == sorted(names) and {"alice", "newbie", "root", "rails"} <= set(names)
    alice = next(u for u in r.json() if u["username"] == "alice")
    assert alice["email"] == "alice@example.com"
    assert (alice["faction_name"], alice["role_name"]) == ("Alpha", "Chef")
    assert [u["username"] for u in get("root", q="ALI").json()] == ["alice"]
    assert [u["username"] for u in get("root", q="example.com").json()] == ["alice"]
    assert get("root", q="%").json() == []  # wildcards are plain characters
    assert [u["username"] for u in get("root", role="train_admin").json()] == ["rails"]
    assert next(u for u in get("root").json() if u["username"] == "rails")[
        "global_roles"
    ] == ["train_admin"]
    assert len(get("root", limit=1).json()) == 1
    assert get("root", limit=0).status_code == 422
    assert "hashed_password" not in r.text


def test_an_admin_resets_a_password(aenv):
    url = "/admin/users/2/password"
    body = {"new_password": "brand-new"}
    assert aenv.client.post(url, json=body, headers=aenv.h("alice")).status_code == 403
    assert aenv.client.post(url, json=body, headers=aenv.h("rails")).status_code == 403
    assert aenv.client.post(url, json=body).status_code == 401
    assert (
        aenv.client.post(
            url, json={"new_password": "abc"}, headers=aenv.h("root")
        ).status_code
        == 422
    )
    assert (
        aenv.client.post(
            url, json={"new_password": "é" * 40}, headers=aenv.h("root")
        ).status_code
        == 422
    )
    assert (
        aenv.client.post(
            "/admin/users/999/password", json=body, headers=aenv.h("root")
        ).status_code
        == 404
    )
    assert aenv.client.post(url, json=body, headers=aenv.h("root")).status_code == 204

    login = aenv.client.post(
        "/auth/login", json={"username": "newbie", "password": "brand-new"}
    )
    assert login.status_code == 202, login.text
    assert ("root", "password_reset", "newbie", None) in _entries(aenv)
    assert "brand-new" not in str(_entries(aenv))
    notes = (
        aenv.client.get("/notifications", headers=aenv.h("newbie")) if False else None
    )
    s = aenv.Session()
    from app.database import Notification

    assert (
        s.query(Notification).filter_by(user_id=2, kind="password_reset").count() == 1
    )
    s.close()


def _member(aenv, user_id=60, name="vic", role_name="Recrue2"):
    s = aenv.Session()
    role = Role(role_id=80 + user_id, name=role_name, faction_id=1)
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


def test_an_admin_removes_somebody_from_their_faction(aenv):
    _member(aenv)
    url = "/admin/users/{}/detach"
    assert aenv.client.post(url.format(60), headers=aenv.h("alice")).status_code == 403
    r = aenv.client.post(url.format(60), headers=aenv.h("root"))
    assert r.status_code == 200, r.text
    assert (r.json()["faction_name"], r.json()["role_name"]) == (
        "Sans Faction",
        "Membre",
    )
    assert ("root", "user_removed_from_faction", "vic", "Retiré de Alpha") in _entries(
        aenv
    )
    # no faction any more: nothing to do
    assert aenv.client.post(url.format(60), headers=aenv.h("root")).status_code == 400
    assert aenv.client.post(url.format(2), headers=aenv.h("root")).status_code == 400
    # a leader hands over first
    assert aenv.client.post(url.format(1), headers=aenv.h("root")).status_code == 409
    assert aenv.client.post(url.format(999), headers=aenv.h("root")).status_code == 404
    s = aenv.Session()
    assert s.get(User, 1).faction.name == "Alpha"
    from app.database import Notification

    assert s.query(Notification).filter_by(user_id=60, kind="kicked").count() == 1
    s.close()


def test_all_factions_are_listed_for_admins(aenv):
    s = aenv.Session()
    s.add(Faction(faction_id=7, name="Nouvelle", is_approved=False))
    s.commit()
    s.close()
    get = lambda **p: aenv.client.get(
        "/admin/factions", params=p, headers=aenv.h("root")
    )  # noqa: E731
    assert (
        aenv.client.get("/admin/factions", headers=aenv.h("alice")).status_code == 403
    )
    by_name = {f["name"]: f for f in get().json()}
    assert by_name["Nouvelle"]["is_approved"] is False
    assert by_name["Alpha"]["member_count"] >= 1
    assert [f["name"] for f in get(state="pending").json()] == ["Nouvelle"]
    assert "Nouvelle" not in [f["name"] for f in get(state="approved").json()]
    assert get(state="archived").json() == []
    assert [f["name"] for f in get(q="nouv").json()] == ["Nouvelle"]
    assert get(state="nope").status_code == 422
    # archived ones only show up in their own list
    assert (
        aenv.client.delete("/factions/delete/7", headers=aenv.h("root")).status_code
        == 204
    )
    assert "Nouvelle" not in [f["name"] for f in get().json()]
    archived = get(state="archived").json()
    assert len(archived) == 1 and archived[0]["deleted_at"] is not None


def test_approving_and_deleting_factions_is_recorded(aenv):
    put = lambda who, **b: aenv.client.put(
        "/factions/update/1", json=b, headers=aenv.h(who)
    )  # noqa: E731
    assert put("root", is_approved=True).status_code == 202  # no change: no entry
    assert put("root", is_approved=False).status_code == 202
    assert put("root", is_approved=True).status_code == 202
    assert [e[1] for e in _entries(aenv, target_type="faction")] == [
        "faction_approved",
        "faction_unapproved",
    ]
    # a leader deleting their own faction is not a staff action
    assert (
        aenv.client.delete("/factions/delete/1", headers=aenv.h("alice")).status_code
        == 204
    )
    assert "faction_deleted" not in [e[1] for e in _entries(aenv)]


def test_an_admin_deleting_a_faction_is_recorded(aenv):
    assert (
        aenv.client.delete("/factions/delete/1", headers=aenv.h("root")).status_code
        == 204
    )
    entry = next(e for e in _entries(aenv) if e[1] == "faction_deleted")
    assert entry[0] == "root" and entry[2] == "Alpha"


def test_an_audit_entry_survives_its_actor_and_target_names(aenv):
    aenv.client.put("/global-roles/42/train_admin", headers=aenv.h("root"))
    s = aenv.Session()
    s.query(AuditLog).update({AuditLog.actor_user_id: None})
    s.commit()
    s.close()
    assert ("root", "role_granted", "rails", "train_admin") in _entries(aenv)
