
import pytest
import app.database as database
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
@pytest.fixture(autouse=True)
def test_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"

    monkeypatch.setattr(database, "DB_PATH", test_db)

    database.initialize_db()

def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Nestack Security API is running"
    }


def test_create_record_without_token():
    response = client.post(
        "/records",
        json={
            "title": "Unauthorized Test",
            "body": "This should not be saved"
        }
    )

    assert response.status_code == 401


def test_user_cannot_access_another_users_record():
    user_a = {
        "username": "pytest_user_a3",
        "password": "TestPasswordA123"
    }

    user_b = {
        "username": "pytest_user_b3",
        "password": "TestPasswordB123"
    }

    register_a = client.post("/register", json=user_a)
    register_b = client.post("/register", json=user_b)

    assert register_a.status_code == 201
    assert register_b.status_code == 201

    login_a = client.post("/login", json=user_a)
    login_b = client.post("/login", json=user_b)

    assert login_a.status_code == 200
    assert login_b.status_code == 200

    token_a = login_a.json()["session_token"]
    token_b = login_b.json()["session_token"]

    record = client.post(
        "/records",
        json={
            "title": "Private Record",
            "body": "User A private data"
        },
        headers={"Authorization": f"Bearer {token_a}"}
    )

    assert record.status_code == 201

    record_id = record.json()["id"]

    response = client.get(
        f"/records/{record_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )

    assert response.status_code == 403


def test_admin_can_access_another_users_record():
    user = {
        "username": "pytest_admin_user3",
        "password": "AdminPassword123"
    }

    admin = {
        "username": "pytest_admin3",
        "password": "AdminPassword456"
    }

    register_user = client.post("/register", json=user)
    register_admin = client.post("/register", json=admin)

    assert register_user.status_code == 201
    assert register_admin.status_code == 201

    user_login = client.post("/login", json=user)

    assert user_login.status_code == 200

    user_token = user_login.json()["session_token"]

    record = client.post(
        "/records",
        json={
            "title": "User Private Record",
            "body": "Private information"
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert record.status_code == 201

    record_id = record.json()["id"]

    # Promote the account through trusted database provisioning.
    with database.get_connection() as conn:
        conn.execute(
            "UPDATE users SET role = 'admin' WHERE username = ?",
            ("pytest_admin3",)
        )

    admin_login = client.post("/login", json=admin)

    assert admin_login.status_code == 200

    admin_token = admin_login.json()["session_token"]

    response = client.get(
        f"/records/{record_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
def test_account_lockout_after_five_failed_attempts():
    user = {
        "username": "pytest_lockout",
        "password": "CorrectPassword123"
    }

    registration = client.post("/register", json=user)
    assert registration.status_code == 201

    for attempt in range(5):
        response = client.post(
            "/login",
            json={
                "username": "pytest_lockout",
                "password": "WrongPassword123"
            }
        )

    assert response.status_code == 429
def test_registration_cannot_assign_admin_role():
    response = client.post(
        "/register",
        json={
            "username": "pytest_role_test",
            "password": "SecurePassword123",
            "role": "admin"
        }
    )

    assert response.status_code == 400
def test_registration_rejects_short_password():
    response = client.post(
        "/register",
        json={
            "username": "shortpass",
            "password": "123"
        }
    )
    assert response.status_code == 400
def test_record_rejects_oversized_title():
    user = {
        "username": "pytest_long_title",
        "password": "SecurePassword123"
    }

    client.post("/register", json=user)
    login = client.post("/login", json=user)
    token = login.json()["session_token"]

    response = client.post(
        "/records",
        json={
            "title": "A" * 101,
            "body": "Test body"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400