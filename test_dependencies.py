

import pytest
from fastapi.security import HTTPAuthorizationCredentials

import app.database as database
from app.database import initialize_db
from app.auth.sessions import create_session
from app.auth.dependencies import get_current_user
from fastapi import HTTPException


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    initialize_db()

    with database.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            ("dependency_test", "test_hash", "user")
        )
        user_id = cursor.lastrowid

    return user_id


def test_valid_session_is_accepted(test_database):
    token = create_session(test_database)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    user = get_current_user(credentials)

    assert user["id"] == test_database
    assert user["username"] == "dependency_test"


def test_invalid_session_is_rejected():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid_token"
    )

    with pytest.raises(HTTPException) as error:
        get_current_user(credentials)

    assert error.value.status_code == 401


def test_missing_credentials_are_rejected():
    with pytest.raises(HTTPException) as error:
        get_current_user(None)

    assert error.value.status_code == 401
