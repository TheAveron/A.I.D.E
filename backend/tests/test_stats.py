"""Public figures of the home page, and the admin panel's overview."""

import pytest
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import admin, stats
from app.database import Faction, MapMarker, User


@pytest.fixture
def stenv(env):  # noqa: F811
    for module in (stats, admin):
        env.client.app.include_router(module.router)
    s = env.Session()
    s.add_all(
        [
            User(user_id=40, username="root", hashed_password=PW_HASH, is_admin=True),
            Faction(faction_id=7, name="Beta", is_approved=False),
            MapMarker(map_name="OAOS", label="Port", kind="city", x=0, z=0, faction_id=1),
            MapMarker(map_name="OAOS", label="Mine", kind="city", x=5, z=5, faction_id=1),
            MapMarker(map_name="OAOS", label="Gare", kind="station", x=9, z=9, faction_id=1),
        ]
    )
    s.commit()
    s.close()
    return env


def test_public_figures_leave_the_admins_out(stenv):
    r = stenv.client.get("/stats")  # no account needed
    assert r.status_code == 200, r.text
    # alice and newbie; root is an admin
    assert r.json() == {"members": 2, "projects": 2, "factions": 1}


def test_the_overview_is_for_the_staff(stenv):
    assert stenv.client.get("/admin/overview").status_code == 401
    assert stenv.client.get("/admin/overview", headers=stenv.h("alice")).status_code == 403

    r = stenv.client.get("/admin/overview", headers=stenv.h("root"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["users"] == 3
    assert body["staff"] == 1
    # Alpha is approved; Beta waits; "Sans Faction" is not a faction here
    assert (body["factions"], body["factions_pending"]) == (1, 1)
    assert body["schematics"] == 0
