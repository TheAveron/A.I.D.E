"""Territories and markers drawn over the maps."""

import pytest
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import admin
from app.api import faction as faction_api
from app.api import map_overlay
from app.database import AuditLog, MapMarker, MapTerritory, Role, User

SQUARE = [[0, 0], [100, 0], [100, 100], [0, 100]]
MAP = "OAOS_zoom"


@pytest.fixture
def menv(env):  # noqa: F811
    """alice holds manage_territory in Alpha; bob is an Alpha member without it;
    root is an admin."""
    for module in (map_overlay, admin):
        env.client.app.include_router(module.router)
    s = env.Session()
    s.get(Role, 1).manage_territory = True
    s.add(Role(role_id=30, name="Membre", faction_id=1))
    s.commit()
    s.add_all(
        [
            User(
                user_id=3,
                username="bob",
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=30,
            ),
            User(user_id=40, username="root", hashed_password=PW_HASH, is_admin=True),
        ]
    )
    s.commit()
    s.close()
    return env


def _territory(env, who="alice", **extra):  # noqa: F811
    body = {
        "map_name": MAP,
        "faction_id": 1,
        "name": "Capitale",
        "points": SQUARE,
        **extra,
    }
    return env.client.post("/map/territories", json=body, headers=env.h(who))


def _marker(env, who="alice", **extra):  # noqa: F811
    body = {"map_name": MAP, "label": "Mine", "kind": "village", "x": 10, "z": -20}
    body.update(extra)
    return env.client.post("/map/markers", json=body, headers=env.h(who))


def _audit(env):  # noqa: F811
    s = env.Session()
    rows = [(a.actor_name, a.action, a.target_name) for a in s.query(AuditLog)]
    s.close()
    return rows


# ── territories ───────────────────────────────────────────────────────────


def test_a_territory_is_drawn_and_read_by_anybody(menv):
    r = _territory(menv, color="#FF8800", description="Le cœur")
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["faction_name"], body["color"], body["points"]) == (
        "Alpha",
        "#ff8800",
        SQUARE,
    )
    listed = menv.client.get(f"/map/{MAP}/territories").json()  # no login needed
    assert [t["name"] for t in listed] == ["Capitale"]
    assert menv.client.get("/map/OTHER/territories").json() == []


def test_drawing_needs_manage_territory_in_that_faction(menv):
    assert _territory(menv, "bob").status_code == 403  # a member without it
    assert _territory(menv, "newbie").status_code == 403  # in another faction
    assert (
        menv.client.post(
            "/map/territories",
            json={"map_name": MAP, "faction_id": 1, "name": "x", "points": SQUARE},
        ).status_code
        == 401
    )
    assert _territory(menv, "alice", faction_id=99).status_code == 404


@pytest.mark.parametrize(
    "points",
    [
        [[0, 0], [1, 1]],  # two points
        [[0, 0], [1, 1], [2, 2]],  # one line: no area
        [[0, 0], [5, 5], [0, 0]],  # three points, two different
        [[0, 0], [1, 0], [40_000_000, 3]],  # beyond the world
        [[0, 0], [1, 0, 3], [1, 1]],  # a point is [x, z]
        [[i, i * i] for i in range(201)],  # too many
    ],
)
def test_bad_polygons_are_refused(menv, points):
    assert _territory(menv, points=points).status_code == 422


def test_a_closed_ring_is_stored_open(menv):
    r = _territory(menv, points=SQUARE + [SQUARE[0]])
    assert r.json()["points"] == SQUARE


@pytest.mark.parametrize("bad", ["red", "#12345", "#gggggg"])
def test_bad_colors_and_map_names_are_refused(menv, bad):
    assert _territory(menv, color=bad).status_code == 422
    assert _territory(menv, map_name="../etc").status_code == 422
    assert menv.client.get("/map/a b/territories").status_code == 404


def test_a_name_is_unique_for_a_faction_on_a_map(menv):
    assert _territory(menv).status_code == 201
    assert _territory(menv).status_code == 409
    assert _territory(menv, map_name="Other").status_code == 201


def test_territories_are_limited_per_faction(menv):
    for i in range(20):
        assert _territory(menv, name=f"T{i}").status_code == 201
    assert _territory(menv, name="one too many").status_code == 409


def test_a_territory_is_changed_and_deleted_by_its_faction(menv):
    tid = _territory(menv).json()["territory_id"]
    r = menv.client.put(
        f"/map/territories/{tid}",
        json={"name": "Nouvelle capitale", "points": [[0, 0], [10, 0], [0, 10]]},
        headers=menv.h("alice"),
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Nouvelle capitale"
    assert r.json()["description"] is None
    assert (
        menv.client.put(
            f"/map/territories/{tid}", json={"name": None}, headers=menv.h("alice")
        ).status_code
        == 422
    )
    assert (
        menv.client.put(
            f"/map/territories/{tid}", json={"name": "x"}, headers=menv.h("bob")
        ).status_code
        == 403
    )
    assert (
        menv.client.delete(f"/map/territories/{tid}", headers=menv.h("bob")).status_code
        == 403
    )
    assert (
        menv.client.delete(
            f"/map/territories/{tid}", headers=menv.h("alice")
        ).status_code
        == 204
    )
    assert (
        menv.client.delete(
            f"/map/territories/{tid}", headers=menv.h("alice")
        ).status_code
        == 404
    )
    assert _audit(menv) == []  # the faction's own business is not audited


def test_an_admin_changes_any_territory_and_it_is_audited(menv):
    tid = _territory(menv).json()["territory_id"]
    h = menv.h("root")
    assert (
        menv.client.put(
            f"/map/territories/{tid}", json={"color": "#00ff00"}, headers=h
        ).status_code
        == 200
    )
    assert _territory(menv, "root", name="Fait par l'admin").status_code == 201
    assert menv.client.delete(f"/map/territories/{tid}", headers=h).status_code == 204
    assert [(a[1], a[2]) for a in _audit(menv)] == [
        ("territory_changed", "Capitale"),
        ("territory_changed", "Fait par l'admin"),
        ("territory_deleted", "Capitale"),
    ]


def test_deleting_a_faction_removes_what_it_drew(menv):
    menv.client.app.include_router(faction_api.router)
    _territory(menv)
    _marker(menv, faction_id=1)
    _marker(menv)  # alice's own, stays
    assert (
        menv.client.delete("/factions/delete/1", headers=menv.h("alice")).status_code
        == 204
    )
    s = menv.Session()
    assert s.query(MapTerritory).count() == 0
    assert [m.label for m in s.query(MapMarker)] == ["Mine"]
    assert s.query(MapMarker).one().user_id == 1
    s.close()
    assert menv.client.get(f"/map/{MAP}/territories").json() == []


# ── markers ───────────────────────────────────────────────────────────────


def test_anybody_places_their_own_marker(menv):
    r = _marker(menv, "newbie", label="Ma cabane", kind="city")
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["owner_name"], body["user_id"], body["faction_id"]) == (
        "newbie",
        2,
        None,
    )
    listed = menv.client.get(f"/map/{MAP}/markers").json()  # public
    assert [m["label"] for m in listed] == ["Ma cabane"]


def test_a_marker_is_for_one_owner_and_a_valid_kind(menv):
    assert _marker(menv, kind="castle").status_code == 422
    assert _marker(menv, x=40_000_000).status_code == 422
    assert _marker(menv, label="  ").status_code == 422
    both = _marker(menv, faction_id=1, user_id=1)
    assert both.status_code == 422
    # somebody else's name is not yours to use
    assert _marker(menv, "newbie", user_id=1).status_code == 403


def test_a_faction_marker_needs_manage_territory(menv):
    assert _marker(menv, "bob", faction_id=1).status_code == 403
    assert _marker(menv, "newbie", faction_id=1).status_code == 403
    r = _marker(menv, "alice", faction_id=1, label="Base")
    assert r.status_code == 201
    assert (r.json()["owner_name"], r.json()["user_id"]) == ("Alpha", None)
    assert _marker(menv, "alice", faction_id=99).status_code == 404


def test_only_the_owner_changes_a_marker(menv):
    mine = _marker(menv, "newbie").json()["marker_id"]
    faction = _marker(menv, "alice", faction_id=1).json()["marker_id"]
    put = lambda mid, who, **b: menv.client.put(  # noqa: E731
        f"/map/markers/{mid}", json=b, headers=menv.h(who)
    )
    assert put(mine, "newbie", label="Renommé", x=5).status_code == 200
    assert put(mine, "alice", label="vol").status_code == 403
    assert put(faction, "bob", label="vol").status_code == 403
    assert put(faction, "alice", kind="stronghold").json()["kind"] == "stronghold"
    assert put(mine, "newbie", x=None).status_code == 422
    assert (
        menv.client.delete(f"/map/markers/{faction}", headers=menv.h("bob")).status_code
        == 403
    )
    assert (
        menv.client.delete(f"/map/markers/{mine}", headers=menv.h("newbie")).status_code
        == 204
    )
    assert (
        menv.client.delete(f"/map/markers/{mine}", headers=menv.h("newbie")).status_code
        == 404
    )
    assert _audit(menv) == []


def test_an_admin_moves_other_peoples_markers_with_an_audit(menv):
    mine = _marker(menv, "newbie").json()["marker_id"]
    h = menv.h("root")
    assert (
        menv.client.put(
            f"/map/markers/{mine}", json={"label": "Modéré"}, headers=h
        ).status_code
        == 200
    )
    assert _marker(menv, "root", user_id=2, label="Pour newbie").status_code == 201
    assert _marker(menv, "root", user_id=999).status_code == 404
    assert menv.client.delete(f"/map/markers/{mine}", headers=h).status_code == 204
    assert [(a[1], a[2]) for a in _audit(menv)] == [
        ("marker_changed", "Mine"),
        ("marker_changed", "Pour newbie"),
        ("marker_deleted", "Modéré"),
    ]
    # an admin's own marker is nobody's business
    own = _marker(menv, "root", label="À moi").json()["marker_id"]
    menv.client.delete(f"/map/markers/{own}", headers=h)
    assert len(_audit(menv)) == 3


def test_markers_are_limited_per_player(menv):
    for i in range(50):
        assert _marker(menv, "newbie", label=f"M{i}", x=i).status_code == 201
    assert _marker(menv, "newbie", label="de trop").status_code == 409
    assert _marker(menv, "alice").status_code == 201  # others are not affected


# ── the permission on roles ───────────────────────────────────────────────


def test_roles_carry_the_permission(menv):
    from app.api import role

    menv.client.app.include_router(role.router)
    roles = menv.client.get("/roles/faction/1", headers=menv.h("alice")).json()
    chef = next(r for r in roles if r["name"] == "Chef")
    assert chef["manage_territory"] is True


def test_every_listed_kind_is_accepted_and_the_old_ones_are_not(menv):
    kinds = [
        "city",
        "trial_chamber",
        "village",
        "ocean_monument",
        "ancient_city",
        "stronghold",
        "nether_bastion",
        "nether_fortress",
        "end_city",
        "generic",
    ]
    for kind in kinds:
        r = _marker(menv, "newbie", label=f"p-{kind}", kind=kind)
        assert r.status_code == 201, (kind, r.text)
        assert r.json()["kind"] == kind
    for old in ("base", "resource", "portal", "landmark", "other"):
        assert _marker(menv, "newbie", label="x", kind=old).status_code == 422


def _spawn(env, who="root", **extra):  # noqa: F811
    return _marker(env, who, label="Spawn", kind="spawn", x=0, z=0, **extra)


def test_only_an_admin_places_the_spawn(menv):
    assert _spawn(menv, "newbie").status_code == 403
    assert _spawn(menv, "alice").status_code == 403  # nor a faction leader
    r = _spawn(menv, "root")
    assert r.status_code == 201 and r.json()["kind"] == "spawn"
    assert ("root", "marker_changed", "Spawn") in _audit(menv)


def test_the_spawn_is_unique_per_map(menv):
    assert _spawn(menv).status_code == 201
    assert _spawn(menv).status_code == 409
    # another map has its own
    other = _marker(menv, "root", map_name="NAOS_zoom", kind="spawn", label="S")
    assert other.status_code == 201
    # nobody can make a second one by changing a marker's kind
    mine = _marker(menv, "root", label="x").json()["marker_id"]
    r = menv.client.put(
        f"/map/markers/{mine}", json={"kind": "spawn"}, headers=menv.h("root")
    )
    assert r.status_code == 409


def test_only_an_admin_moves_or_removes_the_spawn(menv):
    spawn = _spawn(menv).json()["marker_id"]
    url = f"/map/markers/{spawn}"
    for who in ("alice", "newbie", "bob"):
        assert (
            menv.client.put(url, json={"x": 5}, headers=menv.h(who)).status_code == 403
        )
        assert menv.client.delete(url, headers=menv.h(who)).status_code == 403
    moved = menv.client.put(url, json={"x": 5, "z": 7}, headers=menv.h("root"))
    assert moved.status_code == 200 and (moved.json()["x"], moved.json()["z"]) == (5, 7)
    assert menv.client.delete(url, headers=menv.h("root")).status_code == 204
    assert ("root", "marker_deleted", "Spawn") in _audit(menv)
    assert _spawn(menv).status_code == 201  # a new one can be placed again


def test_a_player_cannot_turn_a_marker_into_the_spawn(menv):
    mine = _marker(menv, "newbie").json()["marker_id"]
    r = menv.client.put(
        f"/map/markers/{mine}", json={"kind": "spawn"}, headers=menv.h("newbie")
    )
    assert r.status_code == 403


def test_the_spawn_has_no_owner_but_the_admin_who_sets_it(menv):
    assert _spawn(menv, faction_id=1).status_code == 400
    assert _spawn(menv, user_id=1).status_code == 400


# ── stations and explored structures ─────────────────────────────────────


def test_a_station_is_not_a_bare_marker(menv):
    # It would show on the map but not among the stations
    assert _marker(menv, "newbie", kind="station").status_code == 400
    mid = _marker(menv, "newbie").json()["marker_id"]
    r = menv.client.put(
        f"/map/markers/{mid}", json={"kind": "station"}, headers=menv.h("newbie")
    )
    assert r.status_code == 400


def _explored(env, mid, who, value=True):  # noqa: F811
    return env.client.put(
        f"/map/markers/{mid}/explored", json={"explored": value}, headers=env.h(who)
    )


def test_a_structure_is_marked_explored_by_anybody(menv):
    mid = _marker(menv, "newbie", kind="trial_chamber").json()["marker_id"]
    listed = menv.client.get(f"/map/{MAP}/markers").json()
    assert (listed[0]["explored"], listed[0]["explored_by_name"]) == (False, None)
    # bob does not own it: looting is anybody's business
    r = _explored(menv, mid, "bob")
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["explored"], body["explored_by_name"]) == (True, "bob")
    assert body["explored_at"] is not None
    # saying it again keeps the first explorer
    assert _explored(menv, mid, "alice").json()["explored_by_name"] == "bob"
    back = _explored(menv, mid, "alice", False).json()
    assert (back["explored"], back["explored_by_name"], back["explored_at"]) == (
        False,
        None,
        None,
    )
    assert _audit(menv) == []
    assert (
        menv.client.put(
            f"/map/markers/{mid}/explored", json={"explored": True}
        ).status_code
        == 401
    )
    assert _explored(menv, 999, "newbie").status_code == 404


def test_only_a_structure_can_be_explored(menv):
    city = _marker(menv, "newbie", kind="city").json()["marker_id"]
    assert _explored(menv, city, "newbie").status_code == 400


def test_leaving_the_structure_kinds_forgets_explored(menv):
    mid = _marker(menv, "newbie", kind="village").json()["marker_id"]
    _explored(menv, mid, "newbie")
    r = menv.client.put(
        f"/map/markers/{mid}", json={"kind": "city"}, headers=menv.h("newbie")
    )
    assert (r.json()["explored"], r.json()["explored_by_name"]) == (False, None)


def test_a_generic_point_has_a_colour(menv):
    r = _marker(menv, "newbie", kind="generic", color="#1A2B3C")
    assert r.status_code == 201, r.text
    assert r.json()["color"] == "#1a2b3c"
    mid = r.json()["marker_id"]
    assert _marker(menv, "newbie", label="x", color="rouge").status_code == 422
    put = lambda **b: menv.client.put(  # noqa: E731
        f"/map/markers/{mid}", json=b, headers=menv.h("newbie")
    )
    assert put(color="#00ff00").json()["color"] == "#00ff00"
    assert put(color=None).json()["color"] is None
    # the other kinds have their icon, not a colour
    assert (
        _marker(menv, "newbie", label="v", kind="village", color="#ff0000").json()[
            "color"
        ]
        is None
    )
    put(color="#00ff00")
    assert put(kind="city").json()["color"] is None
