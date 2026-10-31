
from fastapi import HTTPException

from app.database import get_connection
from app.auth.sessions import create_session, revoke_session
from app.auth.dependencies import get_current_user

# Create a temporary test user
with get_connection() as conn:
    cursor = conn.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?, ?)
        """,
        ("dependency_test_user", "test_hash")
    )
    user_id = cursor.lastrowid

try:
    token = create_session(user_id)

    # Test valid token
    user = get_current_user("Bearer " + token)
    print("Valid token accepted:", user["id"] == user_id)

    # Test invalid token
    try:
        get_current_user("Bearer invalid_token")
    except HTTPException as error:
        print("Invalid token rejected:", error.status_code == 401)

    # Test missing token
    try:
        get_current_user(None)
    except HTTPException as error:
        print("Missing token rejected:", error.status_code == 401)

    # Test revoked token
    revoke_session(token)

    try:
        get_current_user("Bearer " + token)
    except HTTPException as error:
        print("Revoked token rejected:", error.status_code == 401)

finally:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
