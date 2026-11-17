"""The leader hands the faction over to another member."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.database import Role, User


def _members(env):  # noqa: F811
    """Alpha: adele is its deputy ("Chef Adjoint"), rory a plain recruit."""
    s = env.Session()
    s.add_all(
        [
            Role(role_id=30, name="Chef Adjoint", faction_id=1, handle_members=True),
            Role(role_id=31, name="Recrue", faction_id=1),
        ]
    )
    s.commit()
    s.add_all(
        [
            User(
                user_id=10,
                username="adele",
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=30,
            ),
            User(
                user_id=11,
                username="rory",
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=31,
            ),
        ]
    )
    s.commit()
    s.close()


def _role_of(env, user_id):  # noqa: F811
    s = env.Session()
    name = s.get(User, user_id).role.name
    s.close()
    return name


def _transfer(env, who, user_id, faction_id=1):  # noqa: F811
    return env.client.post(
        f"/factions/transfer/{faction_id}",
        json={"user_id": user_id},
        headers=env.h(who),
    )


def test_the_leader_hands_over_and_becomes_deputy(env):  # noqa: F811
    _members(env)
    r = _transfer(env, "alice", 11)
    assert r.status_code == 200
    assert _role_of(env, 11) == "Chef"
    assert _role_of(env, 1) == "Chef Adjoint"


def test_the_new_leader_now_has_the_powers_and_the_old_one_lost_them(env):  # noqa: F811
    _members(env)
    _transfer(env, "alice", 11)
    assert _transfer(env, "alice", 10).status_code == 403
    assert _transfer(env, "rory", 10).status_code == 200
    assert _role_of(env, 10) == "Chef"


def test_exactly_one_leader_remains(env):  # noqa: F811
    _members(env)
    _transfer(env, "alice", 10)
    s = env.Session()
    leaders = [
        u for u in s.query(User).filter_by(faction_id=1) if u.role.name == "Chef"
    ]
    s.close()
    assert [u.username for u in leaders] == ["adele"]


def test_only_the_leader_can_hand_over(env):  # noqa: F811
    _members(env)
    assert _transfer(env, "adele", 11).status_code == 403
    assert _transfer(env, "newbie", 11).status_code == 403
    assert (
        env.client.post("/factions/transfer/1", json={"user_id": 11}).status_code == 401
    )
    assert _role_of(env, 1) == "Chef"


def test_the_successor_must_belong_to_the_faction(env):  # noqa: F811
    _members(env)
    assert _transfer(env, "alice", 2).status_code == 404  # newbie, no faction
    assert _transfer(env, "alice", 999).status_code == 404
    assert _transfer(env, "alice", 1).status_code == 400  # oneself
    assert _transfer(env, "alice", 11, faction_id=999).status_code == 404


def test_without_a_deputy_role_the_strongest_other_role_is_used(env):  # noqa: F811
    _members(env)
    s = env.Session()
    s.query(User).filter_by(user_id=10).update({"role_id": 31})
    s.delete(s.get(Role, 30))
    s.commit()
    s.close()
    assert _transfer(env, "alice", 11).status_code == 200
    assert _role_of(env, 1) == "Recrue"
