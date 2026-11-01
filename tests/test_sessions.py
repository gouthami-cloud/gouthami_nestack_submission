import hashlib
import time
import pytest

import app.database as database
from app.auth.sessions import create_session, verify_session, revoke_session


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_sessions.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.initialize_db()

    # Create a test user
    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            ("session_user", "mock_argon2_hash", "user")
        )
        user_id = cursor.lastrowid

    return user_id


def test_session_creation_and_verification(setup_test_db):
    user_id = setup_test_db
    token = create_session(user_id)

    assert isinstance(token, str)
    assert len(token) > 20

    user = verify_session(token)
    assert user is not None
    assert user["id"] == user_id
    assert user["username"] == "session_user"
    assert user["role"] == "user"


def test_raw_token_never_stored_in_database(setup_test_db):
    user_id = setup_test_db
    token = create_session(user_id)

    # Check sessions table directly: only SHA-256 hash should be stored
    expected_hash = hashlib.sha256(token.encode()).hexdigest()

    with database.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE token_hash = ?",
            (expected_hash,)
        ).fetchone()

        assert row is not None
        assert row["user_id"] == user_id
        # Ensure the raw token is nowhere in the table
        raw_row = conn.execute(
            "SELECT * FROM sessions WHERE token_hash = ?",
            (token,)
        ).fetchone()
        assert raw_row is None


def test_session_revocation(setup_test_db):
    user_id = setup_test_db
    token = create_session(user_id)

    # Verify session is valid before revocation
    assert verify_session(token) is not None

    # Revoke session
    revoke_session(token)

    # Verify session is rejected after revocation
    assert verify_session(token) is None


def test_session_expiration(setup_test_db):
    user_id = setup_test_db
    token = create_session(user_id)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Manually expire the session in the test DB
    with database.get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET expires_at = ? WHERE token_hash = ?",
            (int(time.time()) - 10, token_hash)
        )

    # Expired session must return None
    assert verify_session(token) is None


def test_invalid_and_empty_token(setup_test_db):
    assert verify_session("invalid_nonexistent_token") is None
    assert verify_session("") is None
    assert verify_session(None) is None
