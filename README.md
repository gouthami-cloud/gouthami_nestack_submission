# Nestack Cybersecurity API Submission

## About me
- I am Gouthami. I am a certified Google Cloud Security Engineer.
- **LinkedIn:** [linkedin.com/in/gouthami-gcp](https://www.linkedin.com/in/gouthami-gcp/)

## Certifications

- **Professional Cloud Security Engineer Certification** — Google
  - **Issued:** Mar 2025 · **Expires:** Mar 2027
  - **Skills:** Python (Programming Language)
  - **Credential:** [Show Credential](https://www.credly.com/badges/6ce3d22a-55e5-4209-a656-2d5a7d30328a)

- **Associate Cloud Engineer Certification** — Google
  - **Issued:** Jan 2025 · **Expires:** Jan 2028
  - **Skills:** Vulnerability Assessment and Penetration Testing (VAPT), Python (Programming Language)
  - **Credential:** [Show Credential](https://www.credly.com/badges/24271424-18c5-4a3f-a0ac-67dd7ffcc120)

- **Cloud Digital Leader Certification** — Google
  - **Issued:** Dec 2024 · **Expires:** Dec 2027
  - **Credential:** [Show Credential](https://www.credly.com/badges/aca95c45-ce24-44e8-8d10-157bd3300e9d)

- **Certified Cloud Security Professional (CCSP)** — Google
  - **Issued:** Oct 2024
  - **Credential ID:** 12370362
  - **Credential:** [Show Credential](https://www.cloudskillsboost.google/public_profiles/f5b3d251-bd7b-4820-8c3c-5ab1b1c9b755/badges/12370362)

## About this project

- I built this project as part of my cybersecurity internship technical assessment at Nestack Technologies.
- The main goal was to understand how authentication, session management, and access control work in a real API.
- While building it, I focused on common security problems like weak password storage, unauthorized access, brute-force login attempts, and users trying to access other users' data.
- I used Python and FastAPI with SQLite for this project.

## Technologies used

- Python
- FastAPI
- SQLite
- Argon2id for password hashing
- Pytest for testing
- Git and GitHub

## Features I implemented

- User registration and login
- Secure password hashing using Argon2id
- Random session tokens for authentication
- Session expiration and server-side verification
- Record creation for authenticated users
- Users can access only their own records
- Admin users can access all records
- Account lockout after 5 incorrect login attempts
- Input validation for API requests
- Parameterized SQL queries to prevent SQL injection

## How to run the project

- First, clone the repository and open the project folder.
- Install the dependencies:

```bash
pip install -r requirements.txt
```

### Start the API:

```bash
python -m uvicorn app.main:app --reload
```

Open this address in your browser to test the API:

`http://127.0.0.1:8000/docs`

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /register | Create a new account |
| POST | /login | Login and receive a session token |
| POST | /records | Create a record |
| GET | /records/{id} | Read a record with access control |

## Security decisions

- **Password security:** I used Argon2id instead of storing plain-text passwords. Each password is hashed before it is saved in the database.
- **Session security:** The API generates random session tokens. Only the token hash is stored in the database. Sessions expire after one hour, and the server verifies the session on authenticated requests.
- **Access control:** I checked record ownership before returning private records. Admin users can access all records, but normal users cannot access another user's records.
- **Admin protection:** Users cannot assign themselves an admin role during registration. The registration endpoint rejects unexpected fields such as `role`.
- **Brute-force protection:** After five incorrect login attempts, the account is locked temporarily.
- **SQL injection protection:** I used parameterized SQL queries instead of directly joining user input into SQL statements.

## Threat model

I considered these possible attacks while building the API:

- Password database leak: Passwords are stored as Argon2id hashes, not plain text. Attackers could still attempt offline password cracking.
- Session theft: A stolen session token could allow unauthorized access until it expires or is revoked. Storing only its hash helps protect tokens if the database leaks.
- Unauthorized record access: Every record request checks whether the user owns the record or has the admin role.
- Admin privilege escalation: The public registration endpoint always creates normal users and rejects extra fields.
- Brute-force attacks: Failed login attempts are tracked per account, with a temporary lockout after five failures.

## Testing

I used Pytest and FastAPI TestClient to test the API.

The tests cover authentication, unauthorized access, record ownership, admin access, account lockout, and input validation.

Run the tests using:

```bash
python -m pytest tests/ -v
```
