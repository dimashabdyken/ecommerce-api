from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db() -> Session:
    """Provide a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
