
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from app.database import get_connection
from app.auth.password import hash_password

router = APIRouter()

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

@router.post("/register", status_code=201)
def register(data: RegisterRequest):
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
import time

from app.auth.password import verify_password
from app.auth.sessions import create_session

class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)



@router.post("/login")
def login(data: LoginRequest):
    username = data.username.strip()
    current_time = int(time.time())

    error_status = None
    error_detail = None
    user_id = None

    with get_connection() as conn:
        # Serialize login attempts to protect the account lockout counter.
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user is None:
            error_status = 401
            error_detail = "Invalid username or password"

        elif user["locked_until"] and user["locked_until"] > current_time:
            error_status = 429
            error_detail = "Account temporarily locked"

        elif not verify_password(data.password, user["password_hash"]):
            attempts = user["failed_attempts"] + 1

            if attempts >= 5:
                conn.execute(
                    """
                    UPDATE users
                    SET failed_attempts = 0, locked_until = ?
                    WHERE id = ?
                    """,
                    (current_time + 300, user["id"])
                )

                error_status = 429
                error_detail = "Account locked for 5 minutes"

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

    # Raise errors only AFTER the transaction commits.
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

