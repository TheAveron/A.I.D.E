"""A password change signs out every other session of the account."""

from test_change_password import _change  # noqa: F401
from test_hardening import env  # noqa: F401  (pytest fixture)

from app.api import admin, auth
from app.core import create_user_token
from app.database import User


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def _me(env, token):  # noqa: F811
    return env.client.get("/users/me", headers=_bearer(token)).status_code


def _token(env, name="alice"):  # noqa: F811
    s = env.Session()
    try:
        return create_user_token(s.query(User).filter_by(username=name).one())
    finally:
        s.close()


def test_a_password_change_revokes_the_older_tokens(env):  # noqa: F811
    auth.login_limiter.reset("password|1")
    old = _token(env)
    assert _me(env, old) == 200

    fresh = _change(env, "pw", "a-better-one").json()["access_token"]

    assert _me(env, old) == 401
    assert _me(env, fresh) == 200  # the session that changed it stays open
    r = env.client.post(
        "/auth/login", json={"username": "alice", "password": "a-better-one"}
    )
    assert _me(env, r.json()["access_token"]) == 200


def test_a_failed_change_revokes_nothing(env):  # noqa: F811
    old = _token(env)
    assert _change(env, "wrong", "a-better-one").status_code == 400
    assert _me(env, old) == 200


def test_an_admin_reset_revokes_the_tokens_of_the_account(env):  # noqa: F811
    env.client.app.include_router(admin.router)
    victim = _token(env, "newbie")
    assert _me(env, victim) == 200
    s = env.Session()
    root = s.query(User).filter_by(username="alice").one()
    root.is_admin = True
    s.commit()
    s.close()
    r = env.client.post(
        "/admin/users/%d/password" % _uid(env, "newbie"),
        json={"new_password": "temporary"},
        headers=env.h("alice"),
    )
    assert r.status_code == 204, r.text
    assert _me(env, victim) == 401
    assert (
        env.client.post(
            "/auth/login", json={"username": "newbie", "password": "temporary"}
        ).status_code
        == 202
    )


def _uid(env, name):  # noqa: F811
    s = env.Session()
    try:
        return s.query(User).filter_by(username=name).one().user_id
    finally:
        s.close()


def test_tokens_without_a_version_still_work_until_the_first_change(env):  # noqa: F811
    # Tokens issued before the column existed carry no "tv" claim
    assert _me(env, env.h("alice")["Authorization"].split()[1]) == 200
