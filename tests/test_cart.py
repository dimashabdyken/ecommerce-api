"""Comprehensive tests for cart endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestGetCart:
    """Test GET /cart/ endpoint."""

    def test_get_cart_empty(self, client: TestClient, auth_headers):
        """Test getting empty cart - should auto-create."""
        response = client.get("/cart/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0
        assert "id" in data

    def test_get_cart_unauthorized(self, client: TestClient):
        """Test getting cart without authentication."""
        response = client.get("/cart/")

        assert response.status_code == 401


class TestAddCartItem:
    """Test POST /cart/items endpoint."""

    def test_add_item_success(
        self, client: TestClient, auth_headers, test_product, db_session: Session
    ):
        """Test adding item to cart."""
        item_data = {"product_id": test_product.id, "quantity": 2}

        response = client.post("/cart/items", headers=auth_headers, json=item_data)

        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == test_product.id
        assert data["items"][0]["quantity"] == 2

    def test_add_item_increment_existing(
        self, client: TestClient, auth_headers, test_product
    ):
        """Test adding same item twice increments quantity."""
        item_data = {"product_id": test_product.id, "quantity": 2}

        # Add first time
        response1 = client.post("/cart/items", headers=auth_headers, json=item_data)
        assert response1.status_code == 201

        # Add again
        response2 = client.post("/cart/items", headers=auth_headers, json=item_data)
        assert response2.status_code == 201

        data = response2.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 4  # 2 + 2

    def test_add_item_nonexistent_product(self, client: TestClient, auth_headers):
        """Test adding non-existent product."""
        item_data = {"product_id": 99999, "quantity": 1}

        response = client.post("/cart/items", headers=auth_headers, json=item_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_add_item_invalid_quantity_zero(
        self, client: TestClient, auth_headers, test_product
    ):
        """Test adding item with zero quantity."""
        item_data = {"product_id": test_product.id, "quantity": 0}

        response = client.post("/cart/items", headers=auth_headers, json=item_data)

        assert response.status_code == 400
        assert "at least 1" in response.json()["detail"].lower()

    def test_add_item_invalid_quantity_negative(
        self, client: TestClient, auth_headers, test_product
    ):
        """Test adding item with negative quantity."""
        item_data = {"product_id": test_product.id, "quantity": -5}

        response = client.post("/cart/items", headers=auth_headers, json=item_data)

        assert response.status_code == 400

    def test_add_item_missing_fields(self, client: TestClient, auth_headers):
        """Test adding item with missing fields."""
        # Missing quantity - should still work with default
        response = client.post(
            "/cart/items", headers=auth_headers, json={"product_id": 999}
        )
        # Could be 404 (product not found) or 422 (validation error)
        assert response.status_code in [404, 422]

        # Missing product_id
        response = client.post(
            "/cart/items", headers=auth_headers, json={"quantity": 1}
        )
        assert response.status_code == 422

    def test_add_item_unauthorized(self, client: TestClient, test_product):
        """Test adding item without authentication."""
        item_data = {"product_id": test_product.id, "quantity": 1}

        response = client.post("/cart/items", json=item_data)

        assert response.status_code == 401


class TestUpdateCartItem:
    """Test PUT /cart/items/{item_id} endpoint."""

    def test_update_item_quantity(self, client: TestClient, auth_headers, test_product):
        """Test updating cart item quantity."""
        # Add item first
        add_response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        item_id = add_response.json()["items"][0]["id"]

        # Update quantity
        response = client.put(
            f"/cart/items/{item_id}", headers=auth_headers, json={"quantity": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["quantity"] == 5

    def test_update_item_invalid_quantity(
        self, client: TestClient, auth_headers, test_product
    ):
        """Test updating with invalid quantity."""
        # Add item first
        add_response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        item_id = add_response.json()["items"][0]["id"]

        # Try to update to 0
        response = client.put(
            f"/cart/items/{item_id}", headers=auth_headers, json={"quantity": 0}
        )

        assert response.status_code == 400
        assert "at least 1" in response.json()["detail"].lower()

    def test_update_nonexistent_item(self, client: TestClient, auth_headers):
        """Test updating non-existent item."""
        response = client.put(
            "/cart/items/99999", headers=auth_headers, json={"quantity": 5}
        )

        assert response.status_code == 404

    def test_update_item_unauthorized(self, client: TestClient):
        """Test updating item without authentication."""
        response = client.put("/cart/items/1", json={"quantity": 5})

        assert response.status_code == 401


class TestDeleteCartItem:
    """Test DELETE /cart/items/{item_id} endpoint."""

    def test_delete_item_success(self, client: TestClient, auth_headers, test_product):
        """Test removing item from cart."""
        # Add item first
        add_response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        item_id = add_response.json()["items"][0]["id"]

        # Delete item
        response = client.delete(f"/cart/items/{item_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    def test_delete_nonexistent_item(self, client: TestClient, auth_headers):
        """Test deleting non-existent item."""
        response = client.delete("/cart/items/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_item_unauthorized(self, client: TestClient):
        """Test deleting item without authentication."""
        response = client.delete("/cart/items/1")

        assert response.status_code == 401


class TestClearCart:
    """Test DELETE /cart/ endpoint."""

    def test_clear_cart_success(
        self, client: TestClient, auth_headers, test_product, db_session: Session
    ):
        """Test clearing entire cart."""
        # Add multiple items
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        # Create another product and add it
        from app.models.product import Product

        product2 = Product(
            name="Product 2",
            description="Another product",
            price=19.99,
            stock_quantity=50,
            category="Category",
            is_active=True,
        )
        db_session.add(product2)
        db_session.commit()
        db_session.refresh(product2)

        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": product2.id, "quantity": 1},
        )

        # Verify cart has items
        cart_response = client.get("/cart/", headers=auth_headers)
        assert len(cart_response.json()["items"]) == 2

        # Clear cart
        response = client.delete("/cart/", headers=auth_headers)

        assert response.status_code == 204

        # Verify cart is gone (will be recreated empty on next get)
        new_cart_response = client.get("/cart/", headers=auth_headers)
        assert len(new_cart_response.json()["items"]) == 0

    def test_clear_empty_cart(self, client: TestClient, auth_headers):
        """Test clearing cart that doesn't exist yet."""
        response = client.delete("/cart/", headers=auth_headers)

        assert response.status_code == 404

    def test_clear_cart_unauthorized(self, client: TestClient):
        """Test clearing cart without authentication."""
        response = client.delete("/cart/")

        assert response.status_code == 401


class TestCartResponseFormats:
    """Test response format consistency for cart endpoints."""

    def test_cart_response_format(self, client: TestClient, auth_headers):
        """Verify cart response has correct format."""
        response = client.get("/cart/", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["items"], list)
        assert "user_id" in data

    def test_cart_item_response_format(
        self, client: TestClient, auth_headers, test_product
    ):
        """Verify cart item has correct format."""
        item_data = {"product_id": test_product.id, "quantity": 2}
        response = client.post("/cart/items", headers=auth_headers, json=item_data)

        assert response.status_code == 201
        data = response.json()
        item = data["items"][0]

        assert isinstance(item["id"], int)
        assert isinstance(item["product_id"], int)
        assert isinstance(item["quantity"], int)


class TestCartEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_add_multiple_different_products(
        self, client: TestClient, auth_headers, test_product, db_session: Session
    ):
        """Test adding multiple different products to cart."""
        from app.models.product import Product

        # Create second product
        product2 = Product(
            name="Product 2",
            description="Second product",
            price=49.99,
            stock_quantity=25,
            category="Electronics",
            is_active=True,
        )
        db_session.add(product2)
        db_session.commit()
        db_session.refresh(product2)

        # Add first product
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 1},
        )

        # Add second product
        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": product2.id, "quantity": 3},
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 2

    def test_cart_isolation_between_users(
        self, client: TestClient, auth_headers, admin_auth_headers, test_product
    ):
        """Test that carts are isolated between different users."""
        # User 1 adds item
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        # User 2's cart should be empty
        admin_cart_response = client.get("/cart/", headers=admin_auth_headers)
        assert len(admin_cart_response.json()["items"]) == 0

        # User 1's cart should still have item
        user_cart_response = client.get("/cart/", headers=auth_headers)
        assert len(user_cart_response.json()["items"]) == 1
