
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Argon2id securely hashes passwords using a unique salt.
password_hasher = PasswordHasher()


# Pre-generate a dummy Argon2id hash at startup for constant-time defense
DUMMY_HASH = password_hasher.hash("NestackDummyPasswordForTimingDefense123!")


def hash_password(password: str) -> str:
    """Hash a password before storing it in the database."""
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a password against its stored Argon2id hash."""
    try:
        return password_hasher.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def verify_dummy_password(password: str) -> None:
    """Execute dummy verification to equalize execution time for non-existent users."""
    try:
        password_hasher.verify(DUMMY_HASH, password)
    except (VerifyMismatchError, VerificationError):
        pass

