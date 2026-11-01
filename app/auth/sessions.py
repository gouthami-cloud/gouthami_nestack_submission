
import hashlib
import secrets
import time

from app.config import SESSION_DURATION_SECONDS
from app.database import get_connection

SESSION_DURATION = SESSION_DURATION_SECONDS


def create_session(user_id: int) -> str:
    """Create a random session token and store only its hash."""

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = int(time.time()) + SESSION_DURATION

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, user_id, expires_at)
        )

    return token


def verify_session(token: str):
    """Verify a session token and return its user information."""

    if not token:
        return None

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    current_time = int(time.time())

    with get_connection() as conn:
        session = conn.execute(
            """
            SELECT users.id, users.username, users.role
            FROM sessions
            JOIN users ON sessions.user_id = users.id
            WHERE sessions.token_hash = ?
              AND sessions.expires_at > ?
              AND sessions.revoked_at IS NULL
            """,
            (token_hash, current_time)
        ).fetchone()

    return dict(session) if session else None


def revoke_session(token: str) -> None:
    """Invalidate a session token."""

    if not token:
        return

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET revoked_at = ?
            WHERE token_hash = ?
              AND revoked_at IS NULL
            """,
            (int(time.time()), token_hash)
        )
