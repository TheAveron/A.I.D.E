"""Leaving one's faction, and removing a member from it."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.database import Role, User


def _add_members(env):  # noqa: F811
    """Alpha gets an officer (handle_members), a treasurer and a plain member."""
    s = env.Session()
    s.add_all(
        [
            Role(role_id=30, name="Officier", faction_id=1, handle_members=True),
            Role(role_id=31, name="Trésorier", faction_id=1, manage_funds=True),
            Role(role_id=32, name="Recrue", faction_id=1),
            Role(
                role_id=33,
                name="Chef Adjoint",
                faction_id=1,
                handle_members=True,
                manage_funds=True,
            ),
        ]
    )
    s.commit()
    for user_id, name, role_id in (
        (10, "oscar", 30),
        (11, "tina", 31),
        (12, "rory", 32),
        (13, "adele", 33),
    ):
        s.add(
            User(
                user_id=user_id,
                username=name,
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=role_id,
            )
        )
    s.commit()
    s.close()


def _where(env, user_id):  # noqa: F811
    s = env.Session()
    user = s.get(User, user_id)
    result = (user.faction.name, user.role.name)
    s.close()
    return result


def test_a_member_can_leave_their_faction(env):  # noqa: F811
    _add_members(env)
    r = env.client.post("/users/leave", headers=env.h("rory"))
    assert r.status_code == 200
    assert _where(env, 12) == ("Sans Faction", "Membre")


def test_the_leader_cannot_leave(env):  # noqa: F811
    r = env.client.post("/users/leave", headers=env.h("alice"))
    assert r.status_code == 403
    assert _where(env, 1) == ("Alpha", "Chef")


def test_someone_without_a_faction_cannot_leave(env):  # noqa: F811
    r = env.client.post("/users/leave", headers=env.h("newbie"))
    assert r.status_code == 400


def test_leaving_needs_a_login(env):  # noqa: F811
    assert env.client.post("/users/leave").status_code == 401


def test_an_officer_removes_a_plain_member(env):  # noqa: F811
    _add_members(env)
    r = env.client.post("/users/12/kick", headers=env.h("oscar"))
    assert r.status_code == 200
    assert _where(env, 12) == ("Sans Faction", "Membre")


def test_the_leader_removes_anybody_but_themselves(env):  # noqa: F811
    _add_members(env)
    assert env.client.post("/users/13/kick", headers=env.h("alice")).status_code == 200
    assert _where(env, 13)[0] == "Sans Faction"
    assert env.client.post("/users/1/kick", headers=env.h("alice")).status_code == 400


def test_the_leader_cannot_be_removed(env):  # noqa: F811
    _add_members(env)
    r = env.client.post("/users/1/kick", headers=env.h("adele"))
    assert r.status_code == 403
    assert _where(env, 1) == ("Alpha", "Chef")


def test_nobody_removes_a_member_with_powers_they_lack(env):  # noqa: F811
    _add_members(env)
    # The officer has no manage_funds, the treasurer holds it
    r = env.client.post("/users/11/kick", headers=env.h("oscar"))
    assert r.status_code == 403
    assert _where(env, 11) == ("Alpha", "Trésorier")


def test_a_member_without_handle_members_cannot_remove(env):  # noqa: F811
    _add_members(env)
    r = env.client.post("/users/12/kick", headers=env.h("tina"))
    assert r.status_code == 403
    assert _where(env, 12)[0] == "Alpha"


def test_only_members_of_the_same_faction_can_be_removed(env):  # noqa: F811
    _add_members(env)
    r = env.client.post("/users/2/kick", headers=env.h("alice"))
    assert r.status_code == 404
    assert env.client.post("/users/999/kick", headers=env.h("alice")).status_code == 404
