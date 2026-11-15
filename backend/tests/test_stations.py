"""Stations and platforms: anybody registers, creator / train admin edits."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import global_roles, stations
from app.crud import station as crud_station
from app.database import Platform, Station, User

PARIS = {"name": "Paris", "x": 100, "z": -250}


def _mount(env):  # noqa: F811
    env.client.app.include_router(stations.router)
    env.client.app.include_router(global_roles.router)
    s = env.Session()
    s.add_all(
        [
            User(user_id=40, username="root", hashed_password=PW_HASH, is_admin=True),
            User(user_id=42, username="rails", hashed_password=PW_HASH),
        ]
    )
    s.commit()
    s.close()
    r = env.client.put("/global-roles/42/train_admin", headers=env.h("root"))
    assert r.status_code == 200, r.text


def _create(env, who="alice", **over):  # noqa: F811
    return env.client.post("/stations", json={**PARIS, **over}, headers=env.h(who))


def test_anybody_registers_a_station_and_everybody_reads_it(env):  # noqa: F811
    _mount(env)
    r = _create(env, "newbie", y=64, description="Hub central", dimension="nether")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["created_by_user_id"] == 2
    assert (body["x"], body["y"], body["z"], body["dimension"]) == (
        100,
        64,
        -250,
        "nether",
    )
    sid = body["station_id"]
    # no login needed to read
    assert env.client.get(f"/stations/{sid}").json()["name"] == "Paris"
    assert [s["name"] for s in env.client.get("/stations").json()] == ["Paris"]
    assert env.client.get("/stations/999").status_code == 404


def test_coordinates_are_required_and_bounded(env):  # noqa: F811
    _mount(env)
    h = env.h("alice")
    assert (
        env.client.post("/stations", json={"name": "X"}, headers=h).status_code == 422
    )
    assert (
        env.client.post("/stations", json={"name": "X", "x": 1}, headers=h).status_code
        == 422
    )
    assert _create(env, x=30_000_001).status_code == 422
    assert _create(env, z=-30_000_001).status_code == 422
    assert _create(env, y=99999).status_code == 422
    assert _create(env, dimension="mars").status_code == 422
    assert _create(env, x="12.5").status_code == 422
    assert _create(env, name="   ").status_code == 422
    assert _create(env, name="x" * 61).status_code == 422
    assert _create(env, x=-30_000_000, z=30_000_000).status_code == 201


def test_login_is_needed_to_register(env):  # noqa: F811
    _mount(env)
    assert env.client.post("/stations", json=PARIS).status_code == 401


def test_names_are_unique_whatever_the_case(env):  # noqa: F811
    _mount(env)
    assert _create(env).status_code == 201
    assert _create(env, who="newbie", name="paris").status_code == 409
    assert _create(env, who="newbie", name="  PARIS ").status_code == 409
    assert _create(env, who="newbie", name="Lyon").status_code == 201


def test_a_station_can_come_with_platforms(env):  # noqa: F811
    _mount(env)
    r = _create(
        env,
        platforms=[
            {"name": "1", "description": "Vers le nord, de plain-pied"},
            {"name": "A"},
        ],
    )
    assert r.status_code == 201, r.text
    assert [(p["name"], p["description"]) for p in r.json()["platforms"]] == [
        ("1", "Vers le nord, de plain-pied"),
        ("A", None),
    ]
    dup = _create(env, name="Lyon", platforms=[{"name": "a"}, {"name": "A"}])
    assert dup.status_code == 422
    too_many = _create(
        env, name="Metz", platforms=[{"name": str(i)} for i in range(31)]
    )
    assert too_many.status_code == 422


def test_only_creator_or_train_admin_can_change_or_delete(env):  # noqa: F811
    _mount(env)
    sid = _create(env, "alice").json()["station_id"]
    url = f"/stations/{sid}"
    put = lambda who: env.client.put(
        url, json={"x": 5}, headers=env.h(who)
    )  # noqa: E731
    assert put("newbie").status_code == 403
    assert put("root").status_code == 403  # global admin is not a train admin
    assert env.client.put(url, json={"x": 5}).status_code == 401
    assert put("alice").json()["x"] == 5
    assert put("rails").status_code == 200  # train admin changes anything
    assert env.client.delete(url, headers=env.h("newbie")).status_code == 403
    assert env.client.delete(url, headers=env.h("rails")).status_code == 204
    assert env.client.get(url).status_code == 404


def test_partial_update_and_nulls(env):  # noqa: F811
    _mount(env)
    sid = _create(env, y=70, description="d").json()["station_id"]
    url, h = f"/stations/{sid}", env.h("alice")
    r = env.client.put(url, json={"y": None, "description": None}, headers=h)
    assert r.status_code == 200 and r.json()["y"] is None
    assert r.json()["description"] is None
    for field in ("name", "x", "z", "dimension"):
        assert env.client.put(url, json={field: None}, headers=h).status_code == 422
    r = env.client.put(url, json={"dimension": "end", "name": "Paris Nord"}, headers=h)
    assert (r.json()["dimension"], r.json()["name"]) == ("end", "Paris Nord")
    _create(env, who="newbie", name="Lyon")
    assert env.client.put(url, json={"name": "LYON"}, headers=h).status_code == 409
    # renaming to the same name in another case is the same station: allowed
    assert (
        env.client.put(url, json={"name": "paris nord"}, headers=h).status_code == 200
    )


def test_platform_management(env):  # noqa: F811
    _mount(env)
    sid = _create(env, "alice").json()["station_id"]
    base = f"/stations/{sid}/platforms"
    r = env.client.post(base, json={"name": "1"}, headers=env.h("alice"))
    assert r.status_code == 201, r.text
    pid = r.json()["platform_id"]
    assert (
        env.client.post(base, json={"name": "1"}, headers=env.h("alice")).status_code
        == 409
    )
    assert (
        env.client.post(base, json={"name": "2"}, headers=env.h("newbie")).status_code
        == 403
    )
    r = env.client.put(
        f"{base}/{pid}", json={"description": "escalator"}, headers=env.h("rails")
    )
    assert r.json()["description"] == "escalator"
    env.client.post(base, json={"name": "B"}, headers=env.h("alice"))
    assert (
        env.client.put(
            f"{base}/{pid}", json={"name": "b"}, headers=env.h("alice")
        ).status_code
        == 409
    )
    assert (
        env.client.put(
            f"{base}/{pid}", json={"name": None}, headers=env.h("alice")
        ).status_code
        == 422
    )
    assert (
        env.client.put(
            f"{base}/999", json={"name": "Z"}, headers=env.h("alice")
        ).status_code
        == 404
    )
    assert (
        env.client.delete(f"{base}/{pid}", headers=env.h("newbie")).status_code == 403
    )
    assert env.client.delete(f"{base}/{pid}", headers=env.h("alice")).status_code == 204
    names = [p["name"] for p in env.client.get(f"/stations/{sid}").json()["platforms"]]
    assert names == ["B"]


def test_a_platform_of_another_station_is_not_reachable(env):  # noqa: F811
    _mount(env)
    a = _create(env, "alice").json()["station_id"]
    b = _create(env, "newbie", name="Lyon").json()["station_id"]
    pid = env.client.post(
        f"/stations/{b}/platforms", json={"name": "1"}, headers=env.h("newbie")
    ).json()["platform_id"]
    # alice owns station a, but platform pid belongs to b
    r = env.client.delete(f"/stations/{a}/platforms/{pid}", headers=env.h("alice"))
    assert r.status_code == 404
    r = env.client.put(
        f"/stations/{a}/platforms/{pid}", json={"name": "9"}, headers=env.h("alice")
    )
    assert r.status_code == 404


def test_platform_cap(env, monkeypatch):  # noqa: F811
    _mount(env)
    monkeypatch.setattr(crud_station, "MAX_PLATFORMS_PER_STATION", 2)
    sid = _create(env, platforms=[{"name": "1"}, {"name": "2"}]).json()["station_id"]
    r = env.client.post(
        f"/stations/{sid}/platforms", json={"name": "3"}, headers=env.h("alice")
    )
    assert r.status_code == 409


def test_search_filter_and_paging(env):  # noqa: F811
    _mount(env)
    for name, dim in [("Alpha_1", "overworld"), ("Alpha%2", "nether"), ("Beta", "end")]:
        assert _create(env, name=name, dimension=dim).status_code == 201
    names = lambda **p: [
        s["name"] for s in env.client.get("/stations", params=p).json()
    ]  # noqa: E731
    assert names() == ["Alpha%2", "Alpha_1", "Beta"]
    assert names(q="alpha") == ["Alpha%2", "Alpha_1"]
    assert names(q="%") == ["Alpha%2"]  # wildcards are plain characters
    assert names(q="_") == ["Alpha_1"]
    assert names(dimension="end") == ["Beta"]
    assert names(limit=1, skip=1) == ["Alpha_1"]
    assert env.client.get("/stations", params={"limit": 0}).status_code == 422
    assert env.client.get("/stations", params={"dimension": "x"}).status_code == 422


def test_per_user_cap_spares_train_admins(env, monkeypatch):  # noqa: F811
    _mount(env)
    monkeypatch.setattr(crud_station, "MAX_STATIONS_PER_USER", 2)
    assert _create(env, name="A1").status_code == 201
    assert _create(env, name="A2").status_code == 201
    assert _create(env, name="A3").status_code == 409
    assert _create(env, who="newbie", name="N1").status_code == 201
    for i in range(3):
        assert _create(env, who="rails", name=f"R{i}").status_code == 201


def test_deleting_the_creator_keeps_the_station(env):  # noqa: F811
    _mount(env)
    sid = _create(env, who="rails").json()["station_id"]
    s = env.Session()
    s.execute(Station.__table__.update().values(created_by_user_id=None))
    s.commit()
    assert s.get(Station, sid).created_by_user_id is None
    s.close()
    # nobody owns it any more: only train admins can change it
    assert (
        env.client.put(
            f"/stations/{sid}", json={"x": 1}, headers=env.h("alice")
        ).status_code
        == 403
    )
    assert (
        env.client.put(
            f"/stations/{sid}", json={"x": 1}, headers=env.h("rails")
        ).status_code
        == 200
    )


def test_deleting_a_station_deletes_its_platforms(env):  # noqa: F811
    _mount(env)
    sid = _create(env, platforms=[{"name": "1"}]).json()["station_id"]
    assert (
        env.client.delete(f"/stations/{sid}", headers=env.h("alice")).status_code == 204
    )
    s = env.Session()
    assert s.query(Platform).count() == 0
    s.close()
