import pytest
from app.auth.password import (
    hash_password,
    verify_password,
    verify_dummy_password,
    DUMMY_HASH,
)


def test_hash_password_produces_argon2id_format():
    password = "TestPassword123!"
    hashed = hash_password(password)

    # Must be Argon2id format
    assert hashed.startswith("$argon2id$")
    assert "m=" in hashed
    assert "t=" in hashed
    assert "p=" in hashed


def test_unique_salts_for_identical_passwords():
    password = "SamePassword123!"
    hash_1 = hash_password(password)
    hash_2 = hash_password(password)

    # Per-user salt guarantees unique hashes
    assert hash_1 != hash_2
    assert verify_password(password, hash_1) is True
    assert verify_password(password, hash_2) is True


def test_verify_password_correct():
    password = "CorrectSecretPassword!9"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    password = "CorrectSecretPassword!9"
    hashed = hash_password(password)

    assert verify_password("WrongSecretPassword!9", hashed) is False
    assert verify_password("", hashed) is False


def test_verify_dummy_password_timing_defense():
    # Should execute cleanly without throwing exceptions
    verify_dummy_password("AnyPasswordAttempt123!")
    assert DUMMY_HASH.startswith("$argon2id$")
