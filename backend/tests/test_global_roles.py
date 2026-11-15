"""Server-wide roles: stored in their own table, handed out by admins only."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import global_roles
from app.database import GlobalRole, User


def _users(env):  # noqa: F811
    env.client.app.include_router(global_roles.router)
    s = env.Session()
    s.add_all(
        [
            User(user_id=40, username="root", hashed_password=PW_HASH, is_admin=True),
            User(user_id=41, username="boss", hashed_password=PW_HASH, is_admin=True),
            User(user_id=42, username="rails", hashed_password=PW_HASH),
        ]
    )
    s.commit()
    s.close()


def _put(env, who, user_id, role):  # noqa: F811
    return env.client.put(f"/global-roles/{user_id}/{role}", headers=env.h(who))


def _delete(env, who, user_id, role):  # noqa: F811
    return env.client.delete(f"/global-roles/{user_id}/{role}", headers=env.h(who))


def test_is_admin_is_backed_by_the_table(env):  # noqa: F811
    _users(env)
    s = env.Session()
    root = s.get(User, 40)
    assert root.is_admin is True
    assert [(g.user_id, g.role) for g in s.query(GlobalRole).all()] == [
        (40, "admin"),
        (41, "admin"),
    ]
    assert s.get(User, 1).is_admin is False
    # the property is also writable
    s.get(User, 42).is_admin = True
    s.commit()
    assert s.query(GlobalRole).filter_by(user_id=42).count() == 1
    s.get(User, 42).is_admin = False
    s.commit()
    assert s.query(GlobalRole).filter_by(user_id=42).count() == 0
    s.close()


def test_me_shows_the_roles_and_the_old_flag(env):  # noqa: F811
    _users(env)
    me = env.client.get("/users/me", headers=env.h("root")).json()
    assert me["is_admin"] is True
    assert me["global_roles"] == ["admin"]
    assert (
        env.client.get("/users/me", headers=env.h("alice")).json()["global_roles"] == []
    )


def test_an_admin_grants_and_revokes_a_role(env):  # noqa: F811
    _users(env)
    r = _put(env, "root", 42, "train_admin")
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "train_admin" and r.json()["username"] == "rails"
    # granting twice changes nothing
    assert _put(env, "root", 42, "train_admin").status_code == 200
    s = env.Session()
    assert s.query(GlobalRole).filter_by(user_id=42).count() == 1
    s.close()
    listed = env.client.get("/global-roles", headers=env.h("root")).json()
    assert [(g["username"], g["role"]) for g in listed] == [
        ("boss", "admin"),
        ("rails", "train_admin"),
        ("root", "admin"),
    ]
    assert _delete(env, "root", 42, "train_admin").status_code == 204
    # revoking what isn't held is harmless
    assert _delete(env, "root", 42, "train_admin").status_code == 204
    assert (
        env.client.get("/users/me", headers=env.h("rails")).json()["global_roles"] == []
    )


def test_nobody_else_can_hand_roles_out(env):  # noqa: F811
    _users(env)
    _put(env, "root", 42, "train_admin")
    # a train admin is not an admin: roles are independent
    assert _put(env, "rails", 42, "admin").status_code == 403
    assert _put(env, "alice", 1, "admin").status_code == 403
    assert _delete(env, "alice", 40, "admin").status_code == 403
    assert env.client.get("/global-roles", headers=env.h("alice")).status_code == 403
    assert env.client.put("/global-roles/42/admin").status_code == 401
    s = env.Session()
    assert not s.get(User, 42).is_admin
    s.close()


def test_unknown_role_or_user(env):  # noqa: F811
    _users(env)
    assert _put(env, "root", 42, "emperor").status_code == 422
    assert _put(env, "root", 9999, "train_admin").status_code == 404
    assert _delete(env, "root", 9999, "train_admin").status_code == 404


def test_the_last_admin_cannot_be_removed(env):  # noqa: F811
    _users(env)
    assert _delete(env, "root", 41, "admin").status_code == 204
    r = _delete(env, "root", 40, "admin")
    assert r.status_code == 409
    s = env.Session()
    assert s.get(User, 40).is_admin
    s.close()


def test_deleting_a_user_drops_their_roles(env):  # noqa: F811
    _users(env)
    _put(env, "root", 42, "train_admin")
    s = env.Session()
    s.delete(s.get(User, 42))
    s.commit()
    assert s.query(GlobalRole).filter_by(user_id=42).count() == 0
    s.close()
