import sqlite3
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict

from app.config import (
    MAX_FAILED_LOGIN_ATTEMPTS,
    LOCKOUT_DURATION_SECONDS,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
)
from app.database import get_connection
from app.auth.password import hash_password, verify_password, verify_dummy_password
from app.auth.sessions import create_session, revoke_session
from app.auth.dependencies import get_current_user, bearer_scheme

router = APIRouter()


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


@router.post("/register", status_code=201)
async def register(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    # Privilege escalation defense: explicitly refuse role specification with 403 Forbidden
    if "role" in body:
        raise HTTPException(
            status_code=403,
            detail="Privilege escalation forbidden: cannot set or modify account role"
        )

    # Validate remaining fields using Pydantic (rejects extra/missing fields with 400)
    try:
        data = RegisterRequest.model_validate(body)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing input"
        )
    username = data.username.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty"
        )

    password_hash = hash_password(data.password)

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, 'user')
                """,
                (username, password_hash)
            )
            user_id = cursor.lastrowid

        return {
            "id": user_id,
            "username": username,
            "role": "user"
        }

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


@router.post("/login")
def login(data: LoginRequest):
    username = data.username.strip()
    current_time = int(time.time())

    error_status = None
    error_detail = None
    user_id = None

    with get_connection() as conn:
        # Serialize login attempts to protect the account lockout counter against race conditions
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user is None:
            # Timing attack mitigation: run dummy Argon2id verification so latency is constant
            verify_dummy_password(data.password)
            error_status = 401
            error_detail = "Invalid username or password"

        elif user["locked_until"] and user["locked_until"] > current_time:
            error_status = 429
            error_detail = "Account temporarily locked"

        elif not verify_password(data.password, user["password_hash"]):
            attempts = user["failed_attempts"] + 1

            if attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                conn.execute(
                    """
                    UPDATE users
                    SET failed_attempts = 0, locked_until = ?
                    WHERE id = ?
                    """,
                    (current_time + LOCKOUT_DURATION_SECONDS, user["id"])
                )

                error_status = 429
                error_detail = f"Account locked for {LOCKOUT_DURATION_SECONDS // 60} minutes"

            else:
                conn.execute(
                    """
                    UPDATE users
                    SET failed_attempts = ?, locked_until = NULL
                    WHERE id = ?
                    """,
                    (attempts, user["id"])
                )

                error_status = 401
                error_detail = "Invalid username or password"

        else:
            conn.execute(
                """
                UPDATE users
                SET failed_attempts = 0, locked_until = NULL
                WHERE id = ?
                """,
                (user["id"],)
            )

            user_id = user["id"]

    # Raise errors only AFTER the transaction commits
    if error_status:
        raise HTTPException(
            status_code=error_status,
            detail=error_detail
        )

    token = create_session(user_id)

    return {
        "message": "Login successful",
        "session_token": token,
        "token_type": "Bearer"
    }


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: dict = Depends(get_current_user)
):
    """Server-side session invalidation endpoint."""
    revoke_session(credentials.credentials)
    return {"message": "Logged out successfully"}
