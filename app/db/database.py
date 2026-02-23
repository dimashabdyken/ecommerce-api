from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"),
    echo=True,
)

SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
