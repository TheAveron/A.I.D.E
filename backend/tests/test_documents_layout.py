"""The current server's documents folder, and the listing of all factions'."""

from test_hardening import env  # noqa: F401  (pytest fixture)

from app.api import documentation


def test_old_folders_are_moved_into_age_of_steam(tmp_path, monkeypatch):
    docs = tmp_path / "documents"
    monkeypatch.setattr(documentation, "DOCS_DIR", docs)
    (docs / "AOS" / "alpha").mkdir(parents=True)
    (docs / "AOS" / "alpha" / "regles.md").write_text("# Règles")
    (docs / "AOS" / "_archive" / "beta-2").mkdir(parents=True)
    (docs / "AgeOfSteam" / "les_boss").mkdir(parents=True)  # older, empty
    (docs / "AgeOfSteam" / "index.md").write_text("# Age of Steam")

    moved = documentation.migrate_legacy_folders()

    factions = docs / "AgeOfSteam" / "factions"
    assert (factions / "alpha" / "regles.md").read_text() == "# Règles"
    assert (factions / "_archive" / "beta-2").is_dir()
    assert not (docs / "AOS").exists()
    assert not (docs / "AgeOfSteam" / "les_boss").exists()
    assert (docs / "AgeOfSteam" / "index.md").is_file()  # pages untouched
    assert len(moved) == 3
    # Once is enough: running it again changes nothing
    again = documentation.migrate_legacy_folders()
    assert again == []


def test_nothing_is_overwritten(tmp_path, monkeypatch):
    docs = tmp_path / "documents"
    monkeypatch.setattr(documentation, "DOCS_DIR", docs)
    (docs / "AOS" / "alpha").mkdir(parents=True)
    (docs / "AOS" / "alpha" / "old.md").write_text("old")
    (docs / "AgeOfSteam" / "factions" / "alpha").mkdir(parents=True)
    (docs / "AgeOfSteam" / "factions" / "alpha" / "new.md").write_text("new")
    (docs / "AgeOfSteam" / "keep").mkdir()
    (docs / "AgeOfSteam" / "keep" / "x.md").write_text("x")

    documentation.migrate_legacy_folders()

    assert (docs / "AOS" / "alpha" / "old.md").is_file()  # left for a human
    assert not (docs / "AgeOfSteam" / "factions" / "alpha" / "old.md").exists()
    assert (docs / "AgeOfSteam" / "keep" / "x.md").is_file()  # not empty: kept


def test_the_documentation_lists_every_faction_with_documents(
    env, tmp_path, monkeypatch  # noqa: F811
):
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    assert env.client.get("/documents/factions").json() == []
    h = env.h("alice")
    for title in ("Règles du jeu", "Lois"):
        r = env.client.post(
            "/documents/create", json={"title": title, "content": "x"}, headers=h
        )
        assert r.status_code == 201, r.text
    listing = env.client.get("/documents/factions").json()  # no login needed
    assert [f["faction_name"] for f in listing] == ["Alpha"]
    assert [d["title"] for d in listing[0]["documents"]] == ["Lois", "Règles du jeu"]
