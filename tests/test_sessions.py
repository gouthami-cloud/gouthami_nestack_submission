
import uuid

from app.database import get_connection
from app.auth.sessions import create_session, verify_session, revoke_session

# Create a temporary test user
username = "session_test_" + uuid.uuid4().hex[:8]

with get_connection() as conn:
    cursor = conn.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?, ?)
        """,
        (username, "test_hash")
    )
    user_id = cursor.lastrowid

# Test session creation
token = create_session(user_id)
print("Session created:", bool(token))

# Test session verification
user = verify_session(token)
print("Session verified:", user is not None)
print("Correct user:", user["username"] == username if user else False)

# Test session revocation
revoke_session(token)
print("Revoked session rejected:", verify_session(token) is None)

# Clean up temporary test user
with get_connection() as conn:
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
