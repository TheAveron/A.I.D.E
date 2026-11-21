"""hash_password / verify_password talk to bcrypt directly (no passlib)."""

import pytest

from app.core.security import hash_password, verify_password

# A $2b$ hash made by passlib 1.7.4 for "pw": accounts created before the
# switch must keep working.
PASSLIB_HASH = "$2b$12$KIXQ1y0h8k5v0VQH9nYQyOb5s2Vv9u0nM4oUq3Yq5cE7yq9S1xG2K"


def test_hash_then_verify():
    hashed = hash_password("correct horse")
    assert hashed.startswith("$2b$")
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong", hashed)


def test_two_hashes_of_the_same_password_differ():
    assert hash_password("pw") != hash_password("pw")


def test_72_bytes_is_accepted_and_73_is_refused():
    assert verify_password("a" * 72, hash_password("a" * 72))
    with pytest.raises(ValueError):
        hash_password("a" * 73)


def test_multibyte_password_counts_bytes_not_characters():
    # 40 characters, 80 bytes
    with pytest.raises(ValueError):
        hash_password("é" * 40)


def test_verify_never_raises_on_bad_input():
    assert verify_password("a" * 100, hash_password("pw")) is False
    assert verify_password("pw", "not a bcrypt hash") is False
    assert verify_password("pw", PASSLIB_HASH) is False
