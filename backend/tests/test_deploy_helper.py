"""The deployment helper: where the database must go before changing tag."""

import subprocess

import pytest

from scripts.deploy_helper import (downgrade_target, migrations_of,
                                   parse_migration)

CHAIN = {"a1": set(), "0001": {"a1"}, "0002": {"0001"}, "0003": {"0002"}}


def test_a_migration_file_gives_its_revision_and_parents():
    source = '''
revision: str = "0019"
down_revision: Union[str, Sequence[str], None] = "0018"
'''
    assert parse_migration(source) == ("0019", {"0018"})
    assert parse_migration('revision = "a1"\ndown_revision = None\n') == ("a1", set())
    merge = 'revision = "m"\ndown_revision = ("x", "y")\n'
    assert parse_migration(merge) == ("m", {"x", "y"})


def test_going_up_or_staying_needs_no_downgrade():
    assert downgrade_target({"0002"}, CHAIN) is None  # upgrade to 0003
    assert downgrade_target({"0003"}, CHAIN) is None  # same version
    assert downgrade_target(set(), CHAIN) is None  # new database


def test_going_back_names_the_targets_last_revision():
    older = {k: v for k, v in CHAIN.items() if k != "0003"}
    assert downgrade_target({"0003"}, older) == "0002"


def test_a_target_with_two_heads_or_none_is_refused():
    with pytest.raises(ValueError):
        downgrade_target({"0009"}, {**CHAIN, "0003b": {"0002"}})
    with pytest.raises(ValueError):
        downgrade_target({"0001"}, {})


def _has_tag(tag):
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"],
            capture_output=True,
        ).returncode
        == 0
    )


@pytest.mark.skipif(not _has_tag("v1.3.0"), reason="needs the git tags")
def test_the_migrations_of_a_tag_are_read_from_git():
    migrations = migrations_of("v1.3.0")
    assert migrations["0017"] == {"0016"}
    assert "0019" not in migrations
    # Back from 0020 (v1.3.2) to v1.3.0: down to its last migration first
    assert downgrade_target({"0020"}, migrations) == "0017"
