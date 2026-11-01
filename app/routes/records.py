
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from app.database import get_connection
from app.auth.dependencies import get_current_user

router = APIRouter()


class RecordCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=5000)


@router.post("/records", status_code=201)
def create_record(
    data: RecordCreate,
    current_user: dict = Depends(get_current_user)
):
    title = data.title.strip()
    body = data.body.strip()

    if not title or not body:
        raise HTTPException(
            status_code=400,
            detail="Title and body cannot be empty"
        )

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO records (owner_id, title, body)
               VALUES (?, ?, ?)""",
            (current_user["id"], title, body)
        )
        record_id = cursor.lastrowid

    return {
        "id": record_id,
        "title": title,
        "body": body,
        "owner_id": current_user["id"]
    }

@router.get("/records/{record_id}")
def get_record(
    record_id: int,
    current_user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        record = conn.execute(
            "SELECT * FROM records WHERE id = ?",
            (record_id,)
        ).fetchone()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Record not found"
        )

    if (
        record["owner_id"] != current_user["id"]
        and current_user["role"] != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this record"
        )

    return dict(record)
