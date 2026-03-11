"""Comprehensive tests for user profile and address endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestUserProfile:
    """Test GET/PUT /users/me endpoints."""

    def test_get_profile_success(self, client: TestClient, test_user, auth_headers):
        """Test getting user profile."""
        response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
        assert "phone_number" in data
        assert "is_admin" in data

    def test_get_profile_unauthorized(self, client: TestClient):
        """Test getting profile without authentication."""
        response = client.get("/users/me")

        assert response.status_code == 401

    def test_update_profile_email(
        self, client: TestClient, test_user, auth_headers, db_session: Session
    ):
        """Test updating user email."""
        new_email = "newemail@example.com"
        response = client.put(
            "/users/me", headers=auth_headers, json={"email": new_email}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email

    def test_update_profile_phone(
        self, client: TestClient, test_user, auth_headers, db_session: Session
    ):
        """Test updating phone number."""
        new_phone = "+1234567890"
        response = client.put(
            "/users/me", headers=auth_headers, json={"phone_number": new_phone}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == new_phone

    def test_update_profile_duplicate_email(
        self, client: TestClient, test_user, admin_user, auth_headers
    ):
        """Test updating email to one that's already taken."""
        response = client.put(
            "/users/me", headers=auth_headers, json={"email": admin_user.email}
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_update_profile_invalid_email(self, client: TestClient, auth_headers):
        """Test updating with invalid email format."""
        response = client.put(
            "/users/me", headers=auth_headers, json={"email": "not-an-email"}
        )

        assert response.status_code == 422


class TestPasswordChange:
    """Test PUT /users/me/password endpoint."""

    def test_change_password_success(self, client: TestClient, test_user, auth_headers):
        """Test successful password change."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newsecurepass456",
        }

        response = client.put(
            "/users/me/password", headers=auth_headers, json=password_data
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

        # Verify can login with new password
        login_response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "newsecurepass456"},
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test password change with incorrect current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newsecurepass456",
        }

        response = client.put(
            "/users/me/password", headers=auth_headers, json=password_data
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_unauthorized(self, client: TestClient):
        """Test password change without authentication."""
        password_data = {
            "current_password": "any",
            "new_password": "newsecure123",
        }

        response = client.put("/users/me/password", json=password_data)

        assert response.status_code == 401

    def test_change_password_short_password(self, client: TestClient, auth_headers):
        """Test password change with too short new password."""
        password_data = {"current_password": "testpassword123", "new_password": "short"}

        response = client.put(
            "/users/me/password", headers=auth_headers, json=password_data
        )

        assert response.status_code == 422  # Validation error


class TestAddressEndpoints:
    """Test address CRUD operations."""

    def test_create_address_success(self, client: TestClient, auth_headers):
        """Test POST /users/me/addresses - create new address."""
        address_data = {
            "full_name": "John Doe",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "phone_number": "+1234567890",
            "is_default": True,
        }

        response = client.post(
            "/users/me/addresses", headers=auth_headers, json=address_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["street_address"] == address_data["street_address"]
        assert data["city"] == address_data["city"]
        assert data["is_default"] is True
        assert "id" in data

    def test_get_addresses_empty(self, client: TestClient, auth_headers):
        """Test GET /users/me/addresses - empty list."""
        response = client.get("/users/me/addresses", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_addresses_with_data(self, client: TestClient, auth_headers):
        """Test GET /users/me/addresses - with existing addresses."""
        # Create two addresses
        address1 = {
            "full_name": "John Doe",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "phone_number": "+1234567890",
            "is_default": True,
        }
        address2 = {
            "full_name": "Jane Smith",
            "street_address": "456 Oak Ave",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02101",
            "country": "USA",
            "phone_number": "+1987654321",
            "is_default": False,
        }

        client.post("/users/me/addresses", headers=auth_headers, json=address1)
        client.post("/users/me/addresses", headers=auth_headers, json=address2)

        response = client.get("/users/me/addresses", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert isinstance(data, list)

    def test_get_single_address(self, client: TestClient, auth_headers):
        """Test GET /users/me/addresses/{id} - get specific address."""
        # Create address first
        address_data = {
            "full_name": "John Doe",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "phone_number": "+1234567890",
            "is_default": False,
        }
        create_response = client.post(
            "/users/me/addresses", headers=auth_headers, json=address_data
        )
        address_id = create_response.json()["id"]

        response = client.get(f"/users/me/addresses/{address_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == address_id
        assert data["street_address"] == address_data["street_address"]

    def test_get_nonexistent_address(self, client: TestClient, auth_headers):
        """Test getting non-existent address."""
        response = client.get("/users/me/addresses/99999", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_address_success(self, client: TestClient, auth_headers):
        """Test PUT /users/me/addresses/{id} - update address."""
        # Create address
        address_data = {
            "full_name": "John Doe",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "phone_number": "+1234567890",
            "is_default": False,
        }
        create_response = client.post(
            "/users/me/addresses", headers=auth_headers, json=address_data
        )
        address_id = create_response.json()["id"]

        # Update address
        update_data = {"street_address": "456 Updated St", "city": "Boston"}
        response = client.put(
            f"/users/me/addresses/{address_id}", headers=auth_headers, json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["street_address"] == "456 Updated St"
        assert data["city"] == "Boston"
        assert data["state"] == "NY"  # Unchanged fields remain

    def test_update_nonexistent_address(self, client: TestClient, auth_headers):
        """Test updating non-existent address."""
        update_data = {"street_address": "New Street"}
        response = client.put(
            "/users/me/addresses/99999", headers=auth_headers, json=update_data
        )

        assert response.status_code == 404

    def test_delete_address_success(self, client: TestClient, auth_headers):
        """Test DELETE /users/me/addresses/{id} - delete address."""
        # Create address
        address_data = {
            "full_name": "John Doe",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "phone_number": "+1234567890",
            "is_default": False,
        }
        create_response = client.post(
            "/users/me/addresses", headers=auth_headers, json=address_data
        )
        address_id = create_response.json()["id"]

        # Delete address
        response = client.delete(
            f"/users/me/addresses/{address_id}", headers=auth_headers
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/users/me/addresses/{address_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_address(self, client: TestClient, auth_headers):
        """Test deleting non-existent address."""
        response = client.delete("/users/me/addresses/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_addresses_unauthorized(self, client: TestClient):
        """Test address endpoints require authentication."""
        # GET list
        assert client.get("/users/me/addresses").status_code == 401

        # POST create
        assert (
            client.post(
                "/users/me/addresses", json={"street_address": "test", "city": "test"}
            ).status_code
            == 401
        )

        # PUT update
        assert (
            client.put(
                "/users/me/addresses/1", json={"street_address": "test"}
            ).status_code
            == 401
        )

        # DELETE
        assert client.delete("/users/me/addresses/1").status_code == 401


class TestResponseFormats:
    """Test response format consistency for user endpoints."""

    def test_profile_response_format(self, client: TestClient, auth_headers):
        """Verify profile response has correct format."""
        response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["email"], str)
        assert isinstance(data["is_admin"], bool)
        assert data["phone_number"] is None or isinstance(data["phone_number"], str)

    def test_address_response_format(self, client: TestClient, auth_headers):
        """Verify address response has correct format."""
        address_data = {
            "full_name": "John Doe",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "phone_number": "+1234567890",
            "is_default": True,
        }

        response = client.post(
            "/users/me/addresses", headers=auth_headers, json=address_data
        )

        assert response.status_code == 201
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["street_address"], str)
        assert isinstance(data["city"], str)
        assert isinstance(data["is_default"], bool)
