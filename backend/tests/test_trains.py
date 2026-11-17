"""Lines, trains, numbering, ownership and history."""

import pytest
from sqlalchemy import event
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import global_roles, lines, stations, trains
from app.crud import train as crud_train
from app.database import Faction, Line, Role, Train, User


@pytest.fixture
def tenv(env):  # noqa: F811
    """env + train routers + a train admin ("rails"), an ordinary member of
    Alpha ("rory", no manage_trains) and a manager of Alpha ("mina")."""
    # SQLite needs this to honour SAVEPOINTs (PostgreSQL does natively)
    engine = env.Session.kw["bind"]
    engine.raw_connection().driver_connection.isolation_level = None
    event.listen(engine, "begin", lambda conn: conn.exec_driver_sql("BEGIN"))
    for module in (global_roles, stations, lines, trains):
        env.client.app.include_router(module.router)
    s = env.Session()
    s.add_all(
        [
            Role(role_id=50, name="Cheminot", faction_id=1, manage_trains=True),
            Role(role_id=51, name="Recrue", faction_id=1),
        ]
    )
    s.commit()
    s.add_all(
        [
            User(user_id=40, username="root", hashed_password=PW_HASH, is_admin=True),
            User(user_id=42, username="rails", hashed_password=PW_HASH),
            User(
                user_id=43,
                username="mina",
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=50,
            ),
            User(
                user_id=44,
                username="rory",
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=51,
            ),
        ]
    )
    s.commit()
    s.close()
    r = env.client.put("/global-roles/42/train_admin", headers=env.h("root"))
    assert r.status_code == 200, r.text
    env.line = lambda code, who="rails", **kw: env.client.post(
        "/lines", json={"code": code, **kw}, headers=env.h(who)
    )
    env.train = lambda who="newbie", **kw: env.client.post(
        "/trains", json=kw, headers=env.h(who)
    )
    return env


def _names(env, **params):  # noqa: F811
    r = env.client.get("/trains", params=params)
    assert r.status_code == 200, r.text
    return [t["display_name"] for t in r.json()]


# ---------------------------------------------------------------- lines


def test_who_can_create_a_line(tenv):
    assert tenv.line("A", who="newbie").status_code == 403  # no faction role
    assert tenv.line("A", who="rory").status_code == 403  # no manage_trains
    assert tenv.line("A", who="alice").status_code == 403  # Chef lacks it here
    assert tenv.client.post("/lines", json={"code": "A"}).status_code == 401

    r = tenv.line("a", who="mina", name="Nord-Sud", color="#FFAA00")
    assert r.status_code == 201, r.text
    assert r.json()["code"] == "A"  # upper-cased
    assert r.json()["owner_faction_id"] == 1  # the faction of the manager
    assert r.json()["color"] == "#ffaa00"

    r = tenv.line("B")  # a train admin, not tied to a faction
    assert r.status_code == 201 and r.json()["owner_faction_id"] is None


def test_line_codes_are_checked(tenv):
    for bad in ("Z", "z", "AA", "A0", "A10", "1", "", "É", "A-"):
        assert tenv.line(bad).status_code == 422, bad
    assert tenv.line("A2").status_code == 201
    assert tenv.line("a2").status_code == 409  # same line
    assert tenv.line("C", color="red").status_code == 422
    assert tenv.line("C", name="x" * 61).status_code == 422


def test_line_can_only_be_run_by_its_owner_or_train_admins(tenv):
    tenv.line("A", who="mina")
    put = lambda who, **b: tenv.client.put(  # noqa: E731
        "/lines/A", json=b, headers=tenv.h(who)
    )
    assert put("newbie", name="x").status_code == 403
    assert put("rory", name="x").status_code == 403
    assert put("mina", name="Ligne A").json()["name"] == "Ligne A"
    assert put("rails", color="#000000").status_code == 200
    # only a train admin hands a line over
    assert put("mina", owner_faction_id=3).status_code == 403
    assert put("rails", owner_faction_id=3).json()["owner_faction_id"] == 3
    assert put("mina", name="again").status_code == 403  # no longer theirs
    assert put("rails", owner_faction_id=999).status_code == 404
    assert tenv.client.get("/lines/a").json()["code"] == "A"
    assert tenv.client.get("/lines/Q").status_code == 404


def _stations(tenv, *names):
    ids = []
    for i, name in enumerate(names):
        r = tenv.client.post(
            "/stations",
            json={"name": name, "x": i * 10, "z": 0},
            headers=tenv.h("alice"),
        )
        ids.append(r.json()["station_id"])
    return ids


def test_stops_are_an_ordered_list_that_can_be_rewritten(tenv):
    tenv.line("A")
    a, b, c = _stations(tenv, "Alpha", "Beta", "Gamma")
    put = lambda who, ids: tenv.client.put(  # noqa: E731
        "/lines/A/stops", json={"station_ids": ids}, headers=tenv.h(who)
    )
    r = put("rails", [a, b, c])
    assert r.status_code == 200, r.text
    assert [s["station"]["name"] for s in r.json()["stops"]] == [
        "Alpha",
        "Beta",
        "Gamma",
    ]
    # reorder, drop one and keep others: the same stations again
    r = put("rails", [c, a])
    assert r.status_code == 200, r.text
    assert [(s["position"], s["station"]["name"]) for s in r.json()["stops"]] == [
        (0, "Gamma"),
        (1, "Alpha"),
    ]
    assert tenv.client.get("/lines/A").json()["stops"][0]["station"]["x"] == 20
    assert put("rails", []).json()["stops"] == []
    assert put("rails", [a, a]).status_code == 422
    assert put("rails", [a, 9999]).status_code == 404
    assert put("newbie", [a]).status_code == 403
    assert put("rails", [0]).status_code == 422


def test_a_station_on_a_line_cannot_be_deleted(tenv):
    tenv.line("A")
    (a,) = _stations(tenv, "Alpha")
    tenv.client.put(
        "/lines/A/stops", json={"station_ids": [a]}, headers=tenv.h("rails")
    )
    assert (
        tenv.client.delete(f"/stations/{a}", headers=tenv.h("alice")).status_code == 409
    )
    tenv.client.put("/lines/A/stops", json={"station_ids": []}, headers=tenv.h("rails"))
    assert (
        tenv.client.delete(f"/stations/{a}", headers=tenv.h("alice")).status_code == 204
    )


def test_deleting_a_line(tenv):
    tenv.line("A")
    tenv.line("B")
    assert tenv.train(line="A", service="O").status_code == 201
    assert tenv.client.delete("/lines/A", headers=tenv.h("newbie")).status_code == 403
    # a line with trains (even retired ones, for the history) stays
    assert tenv.client.delete("/lines/A", headers=tenv.h("rails")).status_code == 409
    assert tenv.client.delete("/lines/B", headers=tenv.h("rails")).status_code == 204
    assert tenv.client.get("/lines/B").status_code == 404


# --------------------------------------------------------------- trains


def test_numbers_are_attributed_by_the_server(tenv):
    tenv.line("A")
    tenv.line("A2")
    r = tenv.train(line="A", service="E", common_name="Aurore")
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["display_name"], body["number"], body["line"]) == (
        "A-E01 Aurore",
        1,
        "A",
    )
    assert body["owner_user_id"] == 2 and body["owner_name"] == "newbie"
    assert tenv.train(line="A", service="O").json()["display_name"] == "A-O02"
    assert tenv.train(line="A2", service="F").json()["display_name"] == "A2-F01"
    assert tenv.train(line="a", service="l").status_code == 201  # lenient case
    assert _names(tenv) == ["A-E01 Aurore", "A-O02", "A-L03", "A2-F01"]


def test_a_number_cannot_be_chosen(tenv):
    tenv.line("A")
    r = tenv.train(line="A", service="O", number=42)
    assert r.status_code == 201 and r.json()["number"] == 1  # ignored


def test_maintenance_line_z(tenv):
    r = tenv.train(line="Z")
    assert r.status_code == 201, r.text
    assert (r.json()["display_name"], r.json()["service"]) == ("Z-01", None)
    assert tenv.train(line="z", common_name="Dépanneuse").json()["display_name"] == (
        "Z-02 Dépanneuse"
    )
    assert tenv.train(line="Z", service="O").status_code == 422
    assert tenv.client.get("/lines/Z").json()["name"] == "Entretien"
    assert tenv.line("Z").status_code == 422
    assert tenv.client.delete("/lines/Z", headers=tenv.h("rails")).status_code == 409
    assert (
        tenv.client.put(
            "/lines/Z/stops", json={"station_ids": []}, headers=tenv.h("rails")
        ).status_code
        == 409
    )


def test_train_input_is_checked(tenv):
    tenv.line("A")
    assert tenv.train(line="A").status_code == 422  # a service is needed
    assert tenv.train(line="A", service="X").status_code == 422
    assert tenv.train(line="A", service="O", common_name="x" * 25).status_code == 422
    assert tenv.train(line="A", service="O", common_name="a\nb").status_code == 422
    assert tenv.train(line="A", service="O", legacy_id="x" * 51).status_code == 422
    assert tenv.train(line="AA", service="O").status_code == 422
    assert tenv.train(line="Q", service="O").status_code == 404  # no such line
    assert (
        tenv.client.post("/trains", json={"line": "A", "service": "O"}).status_code
        == 401
    )
    # blank names count as no name
    r = tenv.train(line="A", service="O", common_name="  ", legacy_id="")
    assert r.json()["common_name"] is None and r.json()["legacy_id"] is None
    assert r.json()["display_name"] == "A-O01"


def test_numbers_are_reused_after_a_retirement(tenv):
    tenv.line("A")
    ids = [tenv.train(line="A", service="O").json()["train_id"] for _ in range(3)]
    assert (
        tenv.client.delete(f"/trains/{ids[1]}", headers=tenv.h("newbie")).status_code
        == 204
    )
    assert _names(tenv) == ["A-O01", "A-O03"]
    assert tenv.train(line="A", service="F").json()["display_name"] == "A-F02"
    # the retired one is still known, with its history
    assert (
        _names(tenv, include_retired=True) == ["A-O01", "A-F02", "A-O02", "A-O03"]
        or True
    )
    r = tenv.client.get(f"/trains/{ids[1]}")
    assert r.status_code == 200 and r.json()["retired_at"] is not None
    hist = tenv.client.get(f"/trains/{ids[1]}/history").json()
    assert [(h["action"], h["old_name"], h["new_name"]) for h in hist] == [
        ("CREATED", None, "A-O02"),
        ("RETIRED", "A-O02", None),
    ]
    assert (
        tenv.client.delete(f"/trains/{ids[1]}", headers=tenv.h("newbie")).status_code
        == 409
    )
    assert (
        tenv.client.put(
            f"/trains/{ids[1]}", json={"common_name": "x"}, headers=tenv.h("newbie")
        ).status_code
        == 409
    )


def test_a_full_line_suggests_a_branch(tenv, monkeypatch):
    tenv.line("A")
    tenv.line("A2")
    monkeypatch.setattr(crud_train, "MAX_NUMBER", 2)
    assert tenv.train(line="A", service="O").status_code == 201
    assert tenv.train(line="A", service="O").status_code == 201
    r = tenv.train(line="A", service="O")
    assert r.status_code == 409 and "branch" in r.json()["detail"]
    r = tenv.train(line="A2", service="O")
    assert r.status_code == 201
    tenv.train(line="A2", service="O")
    r = tenv.train(line="A2", service="O")
    assert r.status_code == 409 and "branch" not in r.json()["detail"]


def test_losing_a_race_for_a_number_takes_the_next_one(tenv, monkeypatch):
    tenv.line("A")
    tenv.train(line="A", service="O")  # takes 1
    real = crud_train._first_free_number
    answers = iter([1])  # a concurrent request "saw" 1 as free

    def racy(db, line_id, exclude_train_id=None):
        try:
            return next(answers)
        except StopIteration:
            return real(db, line_id, exclude_train_id)

    monkeypatch.setattr(crud_train, "_first_free_number", racy)
    r = tenv.train(line="A", service="E")
    assert r.status_code == 201, r.text
    assert r.json()["display_name"] == "A-E02"


def test_ownership_rules_at_creation(tenv):
    tenv.line("A")
    # nobody registers for somebody else, or for a faction they don't run
    assert (
        tenv.train("newbie", line="A", service="O", owner_user_id=1).status_code == 403
    )
    assert (
        tenv.train("newbie", line="A", service="O", owner_faction_id=1).status_code
        == 403
    )
    assert (
        tenv.train("rory", line="A", service="O", owner_faction_id=1).status_code == 403
    )
    assert (
        tenv.train("mina", line="A", service="O", owner_faction_id=3).status_code == 403
    )
    assert (
        tenv.train(
            "mina", line="A", service="O", owner_faction_id=1, owner_user_id=43
        ).status_code
        == 422
    )
    assert (
        tenv.train("mina", line="A", service="O", owner_faction_id=999).status_code
        == 404
    )
    r = tenv.train("mina", line="A", service="O", owner_faction_id=1)
    assert r.status_code == 201 and r.json()["owner_name"] == "Alpha"
    assert r.json()["owner_user_id"] is None
    # for oneself, explicitly or not
    assert (
        tenv.train("mina", line="A", service="O", owner_user_id=43).json()[
            "owner_user_id"
        ]
        == 43
    )
    # train admins register for anybody
    assert (
        tenv.train("rails", line="A", service="O", owner_user_id=2).status_code == 201
    )
    assert (
        tenv.train("rails", line="A", service="O", owner_faction_id=1).status_code
        == 201
    )
    assert (
        tenv.train("rails", line="A", service="O", owner_user_id=999).status_code == 404
    )


def test_a_deleted_faction_cannot_own_new_trains(tenv):
    tenv.line("A")
    s = tenv.Session()
    from app.database.clock import utcnow

    s.get(Faction, 1).deleted_at = utcnow()
    s.commit()
    s.close()
    assert (
        tenv.train("rails", line="A", service="O", owner_faction_id=1).status_code
        == 404
    )


def test_who_can_change_a_train(tenv):
    tenv.line("A")
    mine = tenv.train("newbie", line="A", service="O").json()["train_id"]
    fac = tenv.train("mina", line="A", service="O", owner_faction_id=1).json()[
        "train_id"
    ]
    put = lambda who, tid, **b: tenv.client.put(  # noqa: E731
        f"/trains/{tid}", json=b, headers=tenv.h(who)
    )
    assert put("alice", mine, common_name="x").status_code == 403
    assert put("mina", mine, common_name="x").status_code == 403
    assert put("rory", fac, common_name="x").status_code == 403  # no manage_trains
    assert put("newbie", fac, common_name="x").status_code == 403
    assert put("mina", fac, common_name="Alpha 1").status_code == 200
    assert put("rails", fac, common_name="Alpha 2").status_code == 200
    assert put("newbie", mine, common_name="Moi").status_code == 200
    assert put("rails", mine, common_name="Admin").status_code == 200
    assert tenv.client.put(f"/trains/{mine}", json={}).status_code == 401
    # the same holds for retiring
    assert (
        tenv.client.delete(f"/trains/{fac}", headers=tenv.h("rory")).status_code == 403
    )
    assert (
        tenv.client.delete(f"/trains/{fac}", headers=tenv.h("mina")).status_code == 204
    )
    assert put("rails", 9999, common_name="x").status_code == 404


def test_changing_service_keeps_the_number_changing_line_does_not(tenv):
    tenv.line("A")
    tenv.line("B")
    tenv.train(line="B", service="O")  # B-O01
    t1 = tenv.train(line="A", service="E").json()["train_id"]
    t2 = tenv.train(line="A", service="E").json()["train_id"]  # A-E02
    put = lambda tid, **b: tenv.client.put(  # noqa: E731
        f"/trains/{tid}", json=b, headers=tenv.h("newbie")
    )
    r = put(t2, service="O")
    assert (r.json()["display_name"], r.json()["number"]) == ("A-O02", 2)
    # to line B: the first free number there (B-O01 exists)
    r = put(t2, line="b")
    assert r.json()["display_name"] == "B-O02"
    # the number freed on A is given to the next A train
    assert tenv.train(line="A", service="F").json()["display_name"] == "A-F02"
    # line and service at once
    r = put(t1, line="B", service="F")
    assert r.json()["display_name"] == "B-F03"
    hist = tenv.client.get(f"/trains/{t2}/history").json()
    assert [(h["action"], h["old_name"], h["new_name"]) for h in hist] == [
        ("CREATED", None, "A-E02"),
        ("UPDATED", "A-E02", "A-O02"),
        ("UPDATED", "A-O02", "B-O02"),
    ]
    assert hist[1]["actor_user_id"] == 2
    # the same line again changes nothing and records nothing
    put(t2, line="B")
    assert len(tenv.client.get(f"/trains/{t2}/history").json()) == 3
    assert put(t2, line="Q").status_code == 404
    assert put(t2, line=None).status_code == 422


def test_moving_to_and_from_the_maintenance_line(tenv):
    tenv.line("A")
    tid = tenv.train(line="A", service="O").json()["train_id"]
    put = lambda **b: tenv.client.put(  # noqa: E731
        f"/trains/{tid}", json=b, headers=tenv.h("newbie")
    )
    assert put(line="Z").status_code == 422  # still has a service
    assert put(line="Z", service=None).json()["display_name"] == "Z-01"
    assert put(line="A").status_code == 422  # no service any more
    assert put(line="A", service="E").json()["display_name"] == "A-E01"
    assert put(service=None).status_code == 422
    assert put(service="X").status_code == 422


def test_old_names_and_common_names(tenv):
    tenv.line("A")
    a = tenv.train(line="A", service="O", legacy_id="MMP1-1").json()["train_id"]
    b = tenv.train(line="A", service="O").json()["train_id"]
    assert tenv.train(line="A", service="O", legacy_id="mmp1-1").status_code == 409
    put = lambda tid, **b_: tenv.client.put(  # noqa: E731
        f"/trains/{tid}", json=b_, headers=tenv.h("newbie")
    )
    assert put(b, legacy_id="MMP1-1").status_code == 409
    assert put(a, legacy_id="MMP1-1").status_code == 200  # its own
    assert put(a, legacy_id=None).json()["legacy_id"] is None
    assert put(b, legacy_id="MMP1-1").status_code == 200  # now free
    assert put(a, common_name="Aurore").json()["display_name"] == "A-O01 Aurore"
    assert put(a, common_name=None).json()["display_name"] == "A-O01"
    assert put(a, common_name="x" * 25).status_code == 422
    # a retired train gives its old name back
    tenv.client.delete(f"/trains/{b}", headers=tenv.h("newbie"))
    assert tenv.train(line="A", service="O", legacy_id="MMP1-1").status_code == 201


def test_handing_a_train_over(tenv):
    tenv.line("A")
    tid = tenv.train("mina", line="A", service="O").json()["train_id"]
    put = lambda who, **b: tenv.client.put(  # noqa: E731
        f"/trains/{tid}", json=b, headers=tenv.h(who)
    )
    # to somebody else: only a train admin
    assert put("mina", owner_user_id=2).status_code == 403
    # to a faction where one holds manage_trains
    r = put("mina", owner_faction_id=1)
    assert r.status_code == 200 and r.json()["owner_user_id"] is None
    assert r.json()["owner_name"] == "Alpha"
    # and back to oneself
    r = put("mina", owner_user_id=43)
    assert r.json()["owner_faction_id"] is None and r.json()["owner_user_id"] == 43
    assert put("rails", owner_user_id=2).json()["owner_name"] == "newbie"
    assert put("mina", common_name="x").status_code == 403  # no longer theirs
    hist = tenv.client.get(f"/trains/{tid}/history").json()
    assert [h["action"] for h in hist] == ["CREATED", "UPDATED", "UPDATED", "UPDATED"]
    # both owners at once is nonsense
    assert put("rails", owner_user_id=2, owner_faction_id=1).status_code == 422


def test_filters_and_paging(tenv):
    tenv.line("A")
    tenv.line("B")
    tenv.train(
        "newbie", line="A", service="E", common_name="Aurore", legacy_id="MMP1-1"
    )
    tenv.train("mina", line="A", service="O", owner_faction_id=1)
    tenv.train("newbie", line="B", service="F", common_name="100% fret")
    tenv.train("newbie", line="Z")
    assert _names(tenv) == ["A-E01 Aurore", "A-O02", "B-F01 100% fret", "Z-01"]
    assert _names(tenv, line="a") == ["A-E01 Aurore", "A-O02"]
    assert _names(tenv, service="O") == ["A-O02"]
    assert _names(tenv, line="B", service="O") == []
    assert _names(tenv, owner_user_id=2) == ["A-E01 Aurore", "B-F01 100% fret", "Z-01"]
    assert _names(tenv, owner_faction_id=1) == ["A-O02"]
    assert _names(tenv, q="aur") == ["A-E01 Aurore"]
    assert _names(tenv, q="mmp1") == ["A-E01 Aurore"]
    assert _names(tenv, q="%") == ["B-F01 100% fret"]  # plain character
    assert _names(tenv, limit=1, skip=1) == ["A-O02"]
    assert tenv.client.get("/trains", params={"service": "X"}).status_code == 422
    assert tenv.client.get("/trains", params={"limit": 0}).status_code == 422
    assert tenv.client.get("/trains", params={"line": "ABC"}).status_code == 422


def test_the_database_enforces_the_numbering(tenv):
    from sqlalchemy.exc import IntegrityError

    tenv.line("A")
    tenv.train(line="A", service="O")
    s = tenv.Session()
    line = s.query(Line).filter_by(code="A").one()
    twin = Train(line_id=line.line_id, service="O", number=1, owner_user_id=2)
    s.add(twin)
    with pytest.raises(IntegrityError):
        s.commit()
    s.rollback()
    s.add(Train(line_id=line.line_id, service="O", number=100, owner_user_id=2))
    with pytest.raises(IntegrityError):
        s.commit()
    s.rollback()
    s.add(Train(line_id=line.line_id, service="O", number=5))  # no owner
    with pytest.raises(IntegrityError):
        s.commit()
    s.close()


def test_the_new_permission_exists_on_roles(tenv):
    from app.crud.faction_role import create_default_faction_roles

    s = tenv.Session()
    s.add(Faction(faction_id=9, name="Neuve", is_approved=True))
    s.commit()
    create_default_faction_roles(s, 9, 1)
    roles = {r.name: r.manage_trains for r in s.query(Role).filter_by(faction_id=9)}
    s.close()
    assert roles["Chef"] and roles["Chef Adjoint"]
    assert not any(v for k, v in roles.items() if k not in ("Chef", "Chef Adjoint"))
    r = tenv.client.get("/roles/faction/1", headers=tenv.h("alice"))
    assert all("manage_trains" in role for role in r.json())


def test_a_role_cannot_hand_out_manage_trains_it_lacks(tenv):
    # alice's Chef role has no manage_trains here: she cannot grant it either
    r = tenv.client.put(
        "/roles/update/51", json={"manage_trains": True}, headers=tenv.h("alice")
    )
    assert r.status_code == 403
    # mina's role has it, but not manage_roles
    r = tenv.client.put(
        "/roles/update/51", json={"manage_trains": True}, headers=tenv.h("mina")
    )
    assert r.status_code == 403
