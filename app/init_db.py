
try:
    from app.database import initialize_db
except ImportError:
    from database import initialize_db

if __name__ == "__main__":
    initialize_db()
    print("Database initialized successfully!")
