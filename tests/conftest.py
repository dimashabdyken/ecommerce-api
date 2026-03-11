"""Shared test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.base import Base
from app.models.product import Product
from app.models.user import User

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user in the database."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session):
    """Create an admin user in the database."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user: User):
    """Get authentication headers for test user."""
    response = client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client: TestClient, admin_user: User):
    """Get authentication headers for admin user."""
    response = client.post(
        "/auth/login",
        data={"username": admin_user.email, "password": "adminpass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_product(db_session: Session):
    """Create a test product in the database."""
    product = Product(
        name="Test Product",
        description="A test product",
        price=29.99,
        stock_quantity=100,
        category="Electronics",
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product
