import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database configuration
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "nestack.db")))

# Session configuration
SESSION_DURATION_SECONDS = int(os.getenv("SESSION_DURATION_SECONDS", "3600"))  # 1 hour

# Brute-force & Lockout configuration
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_SECONDS = int(os.getenv("LOCKOUT_DURATION_SECONDS", "300"))  # 5 minutes

# Credential constraints
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
MAX_PASSWORD_LENGTH = int(os.getenv("MAX_PASSWORD_LENGTH", "128"))
