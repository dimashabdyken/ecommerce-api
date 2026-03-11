"""Comprehensive tests for authentication endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestAuthRegister:
    """Test POST /auth/register endpoint."""

    def test_register_success(self, client: TestClient, db_session: Session):
        """Test successful user registration."""
        user_data = {"email": "newuser@example.com", "password": "securepass123"}

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert data["is_admin"] is False
        assert "password" not in data  # Password should never be returned
        assert "hashed_password" not in data

    def test_register_duplicate_email(
        self, client: TestClient, test_user, db_session: Session
    ):
        """Test registration with existing email - should fail."""
        user_data = {"email": test_user.email, "password": "different123"}

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        user_data = {"email": "not-an-email", "password": "securepass123"}

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        # Missing password
        response = client.post("/auth/register", json={"email": "test@example.com"})
        assert response.status_code == 422

        # Missing email
        response = client.post("/auth/register", json={"password": "test123"})
        assert response.status_code == 422

        # Empty payload
        response = client.post("/auth/register", json={})
        assert response.status_code == 422

    def test_register_empty_values(self, client: TestClient):
        """Test registration with empty string values."""
        user_data = {"email": "", "password": ""}

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 422


class TestAuthLogin:
    """Test POST /auth/login endpoint."""

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with incorrect password."""
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        response = client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "anypassword"},
        )

        assert response.status_code == 401

    def test_login_missing_credentials(self, client: TestClient):
        """Test login with missing credentials."""
        # Missing password
        response = client.post("/auth/login", data={"username": "test@example.com"})
        assert response.status_code == 422

        # Missing username
        response = client.post("/auth/login", data={"password": "test123"})
        assert response.status_code == 422

    def test_login_empty_credentials(self, client: TestClient):
        """Test login with empty credentials."""
        response = client.post("/auth/login", data={"username": "", "password": ""})

        # Should fail validation or authentication
        assert response.status_code in [401, 422]


class TestAuthMe:
    """Test GET /auth/me endpoint."""

    def test_get_current_user_success(
        self, client: TestClient, test_user, auth_headers
    ):
        """Test getting current user information."""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_current_user_no_auth(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    def test_get_current_user_malformed_header(self, client: TestClient):
        """Test with malformed authorization header."""
        # Missing 'Bearer' prefix
        response = client.get("/auth/me", headers={"Authorization": "sometoken"})
        assert response.status_code == 401

        # Empty authorization
        response = client.get("/auth/me", headers={"Authorization": ""})
        assert response.status_code == 401


class TestAuthResponseFormats:
    """Test response format consistency for auth endpoints."""

    def test_register_response_format(self, client: TestClient):
        """Verify registration response has correct format."""
        user_data = {"email": "format@example.com", "password": "test123"}

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        # Check required fields are present
        assert isinstance(data["id"], int)
        assert isinstance(data["email"], str)
        assert isinstance(data["is_admin"], bool)

    def test_login_response_format(self, client: TestClient, test_user):
        """Verify login response has correct token format."""
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data["access_token"], str)
        assert isinstance(data["token_type"], str)
        assert data["token_type"] == "bearer"

    def test_error_response_format(self, client: TestClient):
        """Verify error responses have consistent format."""
        response = client.post(
            "/auth/login", data={"username": "fake@test.com", "password": "wrong"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
