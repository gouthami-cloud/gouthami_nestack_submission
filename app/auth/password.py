
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Argon2id securely hashes passwords using a unique salt.
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password before storing it in the database."""
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a password against its stored Argon2id hash."""
    try:
        return password_hasher.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False
