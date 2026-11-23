"""The schematics gallery: the .nbt reader, uploads, versions, tags, badge."""

import gzip
import struct

import pytest
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import admin, global_roles, schematics
from app.core import nbt
from app.crud import schematic as crud
from app.database import AuditLog, User

# ------------------------------------------------------------ NBT writer


def _s(text: str) -> bytes:
    raw = text.encode()
    return struct.pack(">H", len(raw)) + raw


def _int(name, value):
    return b"\x03" + _s(name) + struct.pack(">i", value)


def _string(name, value):
    return b"\x08" + _s(name) + _s(value)


def _list(name, item_type, payloads):
    return (
        b"\x09"
        + _s(name)
        + bytes([item_type])
        + struct.pack(">i", len(payloads))
        + b"".join(payloads)
    )


def _compound_payload(*entries):
    return b"".join(entries) + b"\x00"


def structure(
    size=(3, 2, 5),
    palette=("minecraft:air", "minecraft:stone"),
    states=(0, 1, 1),
    extra=b"",
    compress=True,
):
    """A structure file as Create / the structure block saves it."""
    blocks = [
        _compound_payload(
            _int("state", s),
            _list("pos", nbt.INT, [struct.pack(">i", 0)] * 3),
            # block entity data, to be skipped
            b"\x0a" + _s("nbt") + _compound_payload(_string("id", "create:track")),
        )
        for s in states
    ]
    body = _compound_payload(
        _int("DataVersion", 3955),
        _list("size", nbt.INT, [struct.pack(">i", v) for v in size]),
        _list(
            "palette",
            nbt.COMPOUND,
            [
                _compound_payload(
                    _string("Name", n), b"\x0a" + _s("Properties") + _compound_payload()
                )
                for n in palette
            ],
        ),
        _list("blocks", nbt.COMPOUND, blocks),
        _list("entities", nbt.COMPOUND, []),
        extra,
    )
    raw = b"\x0a" + _s("") + body
    return gzip.compress(raw, mtime=0) if compress else raw


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


# ------------------------------------------------------------ the reader


def test_reads_size_and_counts_blocks_that_are_not_air():
    info = nbt.read_structure(structure(states=(0, 1, 1, 0, 1)))
    assert (info.size_x, info.size_y, info.size_z) == (3, 2, 5)
    assert info.block_count == 3
    assert info.data_version == 3955


def test_uncompressed_files_are_read_too():
    assert nbt.read_structure(structure(compress=False)).block_count == 2


def test_several_palettes_use_the_first():
    body = _compound_payload(
        _list("size", nbt.INT, [struct.pack(">i", 1)] * 3),
        b"\x09"
        + _s("palettes")
        + bytes([nbt.LIST])
        + struct.pack(">i", 2)
        + bytes([nbt.COMPOUND])
        + struct.pack(">i", 1)
        + _compound_payload(_string("Name", "minecraft:stone"))
        + bytes([nbt.COMPOUND])
        + struct.pack(">i", 1)
        + _compound_payload(_string("Name", "minecraft:air")),
        _list("blocks", nbt.COMPOUND, [_compound_payload(_int("state", 0))]),
    )
    info = nbt.read_structure(gzip.compress(b"\x0a" + _s("") + body))
    assert info.block_count == 1


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"not an nbt file at all",
        gzip.compress(b"\x0a" + _s("") + _compound_payload(_int("x", 1))),  # no size
        structure()[:-12],  # truncated gzip
        gzip.compress(
            b"\x0a" + _s("") + b"\x09" + _s("size") + b"\x03" + struct.pack(">i", -5)
        ),
        structure(size=(0, 1, 1)),
        structure(size=(1, 1, 99999)),
    ],
)
def test_unreadable_files_are_refused(raw):
    with pytest.raises(nbt.NbtError):
        nbt.read_structure(raw)


def test_truncated_data_inside_is_refused():
    raw = gzip.decompress(structure())
    with pytest.raises(nbt.NbtError):
        nbt.read_structure(gzip.compress(raw[: len(raw) // 2]))


def test_deep_nesting_is_refused():
    deep = b""
    for _ in range(200):
        deep = b"\x0a" + _s("a") + deep + b"\x00"
    with pytest.raises(nbt.NbtError, match="nested"):
        nbt.read_structure(structure(extra=deep))


def test_a_decompression_bomb_is_refused(monkeypatch):
    monkeypatch.setattr(nbt, "MAX_DECOMPRESSED_BYTES", 10_000)
    bomb = gzip.compress(
        b"\x0a"
        + _s("")
        + b"\x07"
        + _s("x")
        + struct.pack(">i", 50_000)
        + b"\x00" * 50_000
    )
    assert len(bomb) < 1_000
    with pytest.raises(nbt.NbtError, match="too large"):
        nbt.read_structure(bomb)


def test_a_huge_declared_length_does_not_allocate():
    raw = b"\x0a" + _s("") + b"\x07" + _s("x") + struct.pack(">i", 2**31 - 1)
    with pytest.raises(nbt.NbtError, match="truncated"):
        nbt.read_structure(raw)


# ------------------------------------------------------------ the API


@pytest.fixture
def senv(env, tmp_path, monkeypatch):  # noqa: F811
    """env + the schematics routes, files in a temporary folder, an admin
    ("root") and a train admin ("rails")."""
    monkeypatch.setattr(crud, "STORAGE_DIR", tmp_path / "files")
    for module in (global_roles, schematics, admin):
        env.client.app.include_router(module.router)
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
    env.files = tmp_path / "files"

    def upload(
        who="alice",
        title="Gare de passage",
        data=None,
        name="gare.nbt",
        tags="Gare, train",
        preview=None,
        **form,
    ):
        files = {
            "file": (
                name,
                data if data is not None else structure(),
                "application/octet-stream",
            )
        }
        if preview is not None:
            files["preview"] = ("apercu.png", preview, "image/png")
        return env.client.post(
            "/schematics",
            data={"title": title, "tags": tags, **form},
            files=files,
            headers=env.h(who),
        )

    env.upload = upload
    return env


def _audit(env, action):
    s = env.Session()
    try:
        return [a.detail for a in s.query(AuditLog).filter_by(action=action)]
    finally:
        s.close()


def test_everything_needs_an_account(senv):
    sid = senv.upload().json()["schematic_id"]
    for url in (
        "/schematics",
        "/schematics/tags",
        f"/schematics/{sid}",
        f"/schematics/{sid}/versions/1/download",
    ):
        assert senv.client.get(url).status_code == 401, url
    r = senv.client.post(
        "/schematics", data={"title": "x"}, files={"file": ("a.nbt", structure())}
    )
    assert r.status_code == 401


def test_an_upload_reads_the_file_and_stores_it_under_a_random_name(senv):
    r = senv.upload(description="  Quai à droite  ")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["author_name"] == "alice"
    assert body["description"] == "Quai à droite"
    assert body["tags"] == ["gare", "train"]
    assert body["version_count"] == 1
    v = body["current"]
    assert (v["size_x"], v["size_y"], v["size_z"], v["block_count"]) == (3, 2, 5, 2)
    assert v["original_name"] == "gare.nbt"
    assert v["compliant"] is False
    stored = [p.name for p in senv.files.iterdir()]
    assert len(stored) == 1 and stored[0].endswith(".nbt") and stored[0] != "gare.nbt"

    r = senv.client.get(
        f"/schematics/{body['schematic_id']}/versions/1/download",
        headers=senv.h("newbie"),
    )
    assert r.status_code == 200
    assert r.content == structure()
    assert "Gare_de_passage-v1.nbt" in r.headers["content-disposition"]


@pytest.mark.parametrize(
    "kwargs, code",
    [
        ({"name": "gare.schem"}, 400),  # wrong extension
        ({"name": "gare.nbt", "data": b"PK\x03\x04 a zip"}, 400),  # not NBT
        ({"title": "   "}, 422),
        ({"tags": "ok, pas_de_soulignés"}, 422),
        ({"tags": ",".join(f"t{i}" for i in range(11))}, 422),
        ({"preview": b"GIF89a not accepted"}, 400),
    ],
)
def test_bad_uploads_are_refused_and_leave_no_file(senv, kwargs, code):
    r = senv.upload(**kwargs)
    assert r.status_code == code, r.text
    assert not senv.files.exists() or not any(senv.files.iterdir())


def test_a_file_too_large_is_refused(senv, monkeypatch):
    monkeypatch.setattr(crud, "MAX_NBT_BYTES", 100)
    r = senv.upload(data=structure(states=tuple(range(2)) * 50))
    assert r.status_code == 413


def test_the_preview_is_served_to_accounts(senv):
    sid = senv.upload(preview=PNG).json()["schematic_id"]
    r = senv.client.get(f"/schematics/{sid}/preview", headers=senv.h("newbie"))
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.headers["x-content-type-options"] == "nosniff"

    # replaced, then removed: the old files go
    jpg = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    r = senv.client.put(
        f"/schematics/{sid}/preview",
        files={"preview": ("a.jpg", jpg)},
        headers=senv.h("alice"),
    )
    assert r.status_code == 200, r.text
    assert sorted(p.suffix for p in senv.files.iterdir()) == [".jpg", ".nbt"]
    r = senv.client.delete(f"/schematics/{sid}/preview", headers=senv.h("alice"))
    assert r.json()["has_preview"] is False
    assert [p.suffix for p in senv.files.iterdir()] == [".nbt"]
    assert (
        senv.client.get(
            f"/schematics/{sid}/preview", headers=senv.h("alice")
        ).status_code
        == 404
    )


def test_tags_filter_the_gallery_and_are_suggested(senv):
    senv.upload(title="Gare", tags="gare, train")
    senv.upload(title="Wagon citerne", tags="Train, fluides")
    senv.upload(title="Maison", tags="décor")

    def titles(**params):
        r = senv.client.get("/schematics", params=params, headers=senv.h("newbie"))
        assert r.status_code == 200, r.text
        return sorted(s["title"] for s in r.json())

    assert titles(tag="train") == ["Gare", "Wagon citerne"]
    assert titles(tag=["train", "fluides"]) == ["Wagon citerne"]
    assert titles(tag="DÉCOR") == ["Maison"]
    assert titles(q="wagon") == ["Wagon citerne"]
    assert titles(q="%") == []  # not a wildcard

    r = senv.client.get("/schematics/tags", headers=senv.h("newbie"))
    assert r.json()[0] == {"tag": "train", "count": 2}


def test_only_the_author_or_an_admin_changes_it(senv):
    sid = senv.upload().json()["schematic_id"]
    url = f"/schematics/{sid}"
    r = senv.client.put(url, json={"title": "Volé"}, headers=senv.h("newbie"))
    assert r.status_code == 403
    r = senv.client.put(url, json={"title": "Volé"}, headers=senv.h("rails"))
    assert r.status_code == 403

    r = senv.client.put(
        url,
        json={"title": "Gare v2", "tags": ["Fret"], "description": None},
        headers=senv.h("alice"),
    )
    assert r.status_code == 200, r.text
    assert (r.json()["title"], r.json()["tags"]) == ("Gare v2", ["fret"])
    r = senv.client.put(url, json={"title": None}, headers=senv.h("alice"))
    assert r.status_code == 422

    r = senv.client.put(
        url, json={"title": "Renommé par l'admin"}, headers=senv.h("root")
    )
    assert r.status_code == 200
    assert len(_audit(senv, "schematic_changed")) == 1


def test_versions_keep_the_history_and_reset_the_badge(senv):
    sid = senv.upload().json()["schematic_id"]
    r = senv.client.put(
        f"/schematics/{sid}/versions/1/compliance",
        json={"compliant": True},
        headers=senv.h("rails"),
    )
    assert r.status_code == 200, r.text
    assert r.json()["current"]["compliant"] is True

    v2 = structure(size=(4, 4, 4), states=(1, 1, 1, 1))
    r = senv.client.post(
        f"/schematics/{sid}/versions",
        data={"comment": "Quai allongé"},
        files={"file": ("gare_v2.nbt", v2)},
        headers=senv.h("newbie"),
    )
    assert r.status_code == 403
    r = senv.client.post(
        f"/schematics/{sid}/versions",
        data={"comment": "Quai allongé"},
        files={"file": ("gare_v2.nbt", v2)},
        headers=senv.h("alice"),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["version_count"] == 2
    assert body["current"]["number"] == 2
    assert body["current"]["compliant"] is False  # the new file isn't checked
    assert body["current"]["block_count"] == 4
    assert [v["number"] for v in body["versions"]] == [2, 1]  # newest first
    assert body["versions"][1]["compliant"] is True

    one = senv.client.get(
        f"/schematics/{sid}/versions/1/download", headers=senv.h("alice")
    )
    assert one.content == structure()
    assert (
        senv.client.get(
            f"/schematics/{sid}/versions/3/download", headers=senv.h("alice")
        ).status_code
        == 404
    )


def test_only_train_admins_and_admins_give_the_badge(senv):
    sid = senv.upload().json()["schematic_id"]
    url = f"/schematics/{sid}/versions/1/compliance"
    r = senv.client.put(url, json={"compliant": True}, headers=senv.h("alice"))
    assert r.status_code == 403
    r = senv.client.put(url, json={"compliant": True}, headers=senv.h("root"))
    assert r.status_code == 200

    def compliant_titles(flag):
        r = senv.client.get(
            "/schematics", params={"compliant": flag}, headers=senv.h("alice")
        )
        return [s["schematic_id"] for s in r.json()]

    assert compliant_titles(True) == [sid]
    assert compliant_titles(False) == []
    detail = senv.client.get(f"/schematics/{sid}", headers=senv.h("rails")).json()
    assert detail["can_review"] is True and detail["can_edit"] is False
    assert _audit(senv, "schematic_compliance") == ["v1: compliant"]


def test_deleting_removes_the_files(senv):
    sid = senv.upload(preview=PNG).json()["schematic_id"]
    other = senv.upload(who="newbie", title="Autre").json()["schematic_id"]
    assert len(list(senv.files.iterdir())) == 3

    r = senv.client.delete(f"/schematics/{sid}", headers=senv.h("newbie"))

    assert r.status_code == 403
    r = senv.client.delete(f"/schematics/{sid}", headers=senv.h("alice"))
    assert r.status_code == 204
    assert len(list(senv.files.iterdir())) == 1
    assert (
        senv.client.get(f"/schematics/{sid}", headers=senv.h("alice")).status_code
        == 404
    )

    # an admin deletes somebody else's, and it is audited
    r = senv.client.delete(f"/schematics/{other}", headers=senv.h("root"))
    assert r.status_code == 204
    assert list(senv.files.iterdir()) == []
    assert len(_audit(senv, "schematic_deleted")) == 1


def test_a_failed_commit_leaves_no_file(senv, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("database down")

    monkeypatch.setattr(
        crud, "_commit", lambda db, written: (crud._remove(written), boom())
    )
    assert senv.upload().status_code == 500
    assert not any(senv.files.iterdir())


def test_stored_names_cannot_point_elsewhere():
    for name in ("../etc/passwd", "a.nbt", "0" * 32 + ".exe", "/" + "0" * 32 + ".nbt"):
        with pytest.raises(ValueError):
            crud.stored_path(name)


def test_train_admins_only_see_the_reviews_of_schematics(senv):
    """Schematics are not part of the network: of their audit entries, a
    train admin only sees the standards reviews."""
    sid = senv.upload().json()["schematic_id"]
    url = f"/schematics/{sid}/versions/1/compliance"
    r = senv.client.put(url, json={"compliant": True}, headers=senv.h("rails"))
    assert r.status_code == 200
    r = senv.client.delete(f"/schematics/{sid}", headers=senv.h("root"))
    assert r.status_code == 204

    def actions(who):
        r = senv.client.get("/admin/audit", headers=senv.h(who))
        assert r.status_code == 200, r.text
        return {e["action"] for e in r.json() if e["target_type"] == "schematic"}

    assert actions("rails") == {"schematic_compliance"}
    assert actions("root") == {"schematic_compliance", "schematic_deleted"}
