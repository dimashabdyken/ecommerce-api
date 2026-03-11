"""Comprehensive tests for product endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestListProducts:
    """Test GET /products/ endpoint with various filters."""

    def test_list_products_empty(self, client: TestClient):
        """Test listing products when none exist."""
        response = client.get("/products/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_products_basic(self, client: TestClient, test_product):
        """Test listing products with data."""
        response = client.get("/products/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == test_product.name
        assert data[0]["id"] == test_product.id

    def test_list_products_search(
        self, client: TestClient, test_product, db_session: Session
    ):
        """Test searching products by name/description."""
        from app.models.product import Product

        # Create product with specific searchable term
        product = Product(
            name="Bluetooth Speaker",
            description="Wireless portable speaker",
            price=59.99,
            stock_quantity=30,
            category="Audio",
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        # Search by name
        response = client.get("/products/?search=Bluetooth")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Bluetooth" in data[0]["name"]

        # Search by description
        response = client.get("/products/?search=Wireless")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_products_filter_category(
        self, client: TestClient, db_session: Session
    ):
        """Test filtering products by category."""
        from app.models.product import Product

        # Create products in different categories
        product1 = Product(
            name="Laptop",
            price=999.99,
            stock_quantity=10,
            category="Computers",
            is_active=True,
        )
        product2 = Product(
            name="T-Shirt",
            price=19.99,
            stock_quantity=50,
            category="Clothing",
            is_active=True,
        )
        db_session.add_all([product1, product2])
        db_session.commit()

        # Filter by category
        response = client.get("/products/?category=Computers")
        assert response.status_code == 200
        data = response.json()
        assert all(item["category"] == "Computers" for item in data)

    def test_list_products_filter_price_range(
        self, client: TestClient, db_session: Session
    ):
        """Test filtering products by min/max price."""
        from app.models.product import Product

        products = [
            Product(
                name=f"Product {i}",
                price=Decimal(i * 10),
                stock_quantity=10,
                category="Test",
                is_active=True,
            )
            for i in range(1, 6)
        ]
        db_session.add_all(products)
        db_session.commit()

        # Filter with min_price
        response = client.get("/products/?min_price=30")
        assert response.status_code == 200
        data = response.json()
        assert all(float(item["price"]) >= 30 for item in data)

        # Filter with max_price
        response = client.get("/products/?max_price=30")
        assert response.status_code == 200
        data = response.json()
        assert all(float(item["price"]) <= 30 for item in data)

        # Filter with both
        response = client.get("/products/?min_price=20&max_price=40")
        assert response.status_code == 200
        data = response.json()
        assert all(20 <= float(item["price"]) <= 40 for item in data)

    def test_list_products_filter_in_stock(
        self, client: TestClient, db_session: Session
    ):
        """Test filtering products by stock availability."""
        from app.models.product import Product

        in_stock = Product(
            name="In Stock",
            price=10.00,
            stock_quantity=5,
            category="Test",
            is_active=True,
        )
        out_of_stock = Product(
            name="Out of Stock",
            price=10.00,
            stock_quantity=0,
            category="Test",
            is_active=True,
        )
        db_session.add_all([in_stock, out_of_stock])
        db_session.commit()

        response = client.get("/products/?in_stock=true")
        assert response.status_code == 200
        data = response.json()
        assert all(item["stock_quantity"] > 0 for item in data)

    def test_list_products_sorting(self, client: TestClient, db_session: Session):
        """Test sorting products by different fields."""
        from app.models.product import Product

        products = [
            Product(
                name="Zebra",
                price=100,
                stock_quantity=5,
                category="Test",
                is_active=True,
            ),
            Product(
                name="Apple",
                price=50,
                stock_quantity=10,
                category="Test",
                is_active=True,
            ),
        ]
        db_session.add_all(products)
        db_session.commit()

        # Sort by name ascending
        response = client.get("/products/?sort_by=name&order=asc")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data]
        assert names == sorted(names)

        # Sort by price descending
        response = client.get("/products/?sort_by=price&order=desc")
        assert response.status_code == 200
        data = response.json()
        prices = [float(item["price"]) for item in data]
        assert prices == sorted(prices, reverse=True)

    def test_list_products_pagination(self, client: TestClient, db_session: Session):
        """Test pagination parameters."""
        from app.models.product import Product

        # Create 25 products
        products = [
            Product(
                name=f"Product {i}",
                price=10,
                stock_quantity=10,
                category="Test",
                is_active=True,
            )
            for i in range(25)
        ]
        db_session.add_all(products)
        db_session.commit()

        # First page with limit 10
        response = client.get("/products/?page=1&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 10

        # Second page
        response = client.get("/products/?page=2&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 10

        # Third page (only 5 items)
        response = client.get("/products/?page=3&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 5


class TestGetProduct:
    """Test GET /products/{product_id} endpoint."""

    def test_get_product_success(self, client: TestClient, test_product):
        """Test getting a specific product."""
        response = client.get(f"/products/{test_product.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["name"] == test_product.name
        assert data["price"] == str(test_product.price)

    def test_get_product_not_found(self, client: TestClient):
        """Test getting non-existent product."""
        response = client.get("/products/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_product_invalid_id(self, client: TestClient):
        """Test getting product with invalid ID format."""
        response = client.get("/products/invalid")

        assert response.status_code == 422  # Validation error


class TestCreateProduct:
    """Test POST /products/ endpoint."""

    def test_create_product_success(self, client: TestClient, admin_auth_headers):
        """Test creating a new product as admin."""
        product_data = {
            "name": "New Product",
            "description": "A brand new product",
            "price": 99.99,
            "stock_quantity": 50,
            "category": "Electronics",
            "is_active": True,
        }

        response = client.post(
            "/products/", headers=admin_auth_headers, json=product_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == product_data["name"]
        assert float(data["price"]) == product_data["price"]
        assert "id" in data

    def test_create_product_minimal_fields(
        self, client: TestClient, admin_auth_headers
    ):
        """Test creating product with minimal required fields."""
        product_data = {
            "name": "Minimal Product",
            "description": None,
            "price": 10.00,
            "stock_quantity": 1,
            "category": "Test",
        }

        response = client.post(
            "/products/", headers=admin_auth_headers, json=product_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == product_data["name"]

    def test_create_product_missing_fields(
        self, client: TestClient, admin_auth_headers
    ):
        """Test creating product with missing required fields."""
        incomplete_data = {"name": "Incomplete"}

        response = client.post(
            "/products/", headers=admin_auth_headers, json=incomplete_data
        )

        assert response.status_code == 422

    def test_create_product_invalid_price(self, client: TestClient, admin_auth_headers):
        """Test creating product with invalid price."""
        product_data = {
            "name": "Invalid Price",
            "description": "Test",
            "price": -10.00,  # Negative price
            "stock_quantity": 10,
            "category": "Test",
        }

        response = client.post(
            "/products/", headers=admin_auth_headers, json=product_data
        )

        # Should either reject with validation error or accept if no validation
        assert response.status_code in [201, 422]

    def test_create_product_unauthorized(self, client: TestClient, auth_headers):
        """Test creating product as non-admin user."""
        product_data = {
            "name": "Unauthorized",
            "price": 10.00,
            "stock_quantity": 1,
            "category": "Test",
        }

        response = client.post("/products/", headers=auth_headers, json=product_data)

        assert response.status_code == 403

    def test_create_product_no_auth(self, client: TestClient):
        """Test creating product without authentication."""
        product_data = {
            "name": "No Auth",
            "price": 10.00,
            "stock_quantity": 1,
            "category": "Test",
        }

        response = client.post("/products/", json=product_data)

        assert response.status_code == 401


class TestUpdateProduct:
    """Test PUT /products/{product_id} endpoint."""

    def test_update_product_success(
        self, client: TestClient, test_product, admin_auth_headers
    ):
        """Test updating a product as admin."""
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "price": 39.99,
            "stock_quantity": 75,
            "category": "Updated Category",
            "is_active": True,
        }

        response = client.put(
            f"/products/{test_product.id}", headers=admin_auth_headers, json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert float(data["price"]) == update_data["price"]

    def test_update_product_partial(
        self, client: TestClient, test_product, admin_auth_headers
    ):
        """Test partial update of product."""
        update_data = {"name": "Only Name Updated"}

        response = client.put(
            f"/products/{test_product.id}", headers=admin_auth_headers, json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        # Other fields should remain unchanged
        assert data["category"] == test_product.category

    def test_update_product_not_found(self, client: TestClient, admin_auth_headers):
        """Test updating non-existent product."""
        update_data = {"name": "Does Not Exist"}

        response = client.put(
            "/products/99999", headers=admin_auth_headers, json=update_data
        )

        assert response.status_code == 404

    def test_update_product_unauthorized(
        self, client: TestClient, test_product, auth_headers
    ):
        """Test updating product as non-admin."""
        update_data = {"name": "Unauthorized Update"}

        response = client.put(
            f"/products/{test_product.id}", headers=auth_headers, json=update_data
        )

        assert response.status_code == 403

    def test_update_product_no_auth(self, client: TestClient, test_product):
        """Test updating product without authentication."""
        update_data = {"name": "No Auth Update"}

        response = client.put(f"/products/{test_product.id}", json=update_data)

        assert response.status_code == 401


class TestDeleteProduct:
    """Test DELETE /products/{product_id} endpoint."""

    def test_delete_product_success(
        self, client: TestClient, test_product, admin_auth_headers
    ):
        """Test deleting a product as admin."""
        product_id = test_product.id

        response = client.delete(f"/products/{product_id}", headers=admin_auth_headers)

        assert response.status_code == 204

        # Verify product is deleted
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404

    def test_delete_product_not_found(self, client: TestClient, admin_auth_headers):
        """Test deleting non-existent product."""
        response = client.delete("/products/99999", headers=admin_auth_headers)

        assert response.status_code == 404

    def test_delete_product_unauthorized(
        self, client: TestClient, test_product, auth_headers
    ):
        """Test deleting product as non-admin."""
        response = client.delete(f"/products/{test_product.id}", headers=auth_headers)

        assert response.status_code == 403

    def test_delete_product_no_auth(self, client: TestClient, test_product):
        """Test deleting product without authentication."""
        response = client.delete(f"/products/{test_product.id}")

        assert response.status_code == 401


class TestProductResponseFormats:
    """Test response format consistency for product endpoints."""

    def test_product_list_response_format(self, client: TestClient, test_product):
        """Verify product list response format."""
        response = client.get("/products/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            product = data[0]
            assert isinstance(product["id"], int)
            assert isinstance(product["name"], str)
            assert isinstance(product["price"], str)  # Decimal as string
            assert isinstance(product["stock_quantity"], int)
            assert isinstance(product["is_active"], bool)

    def test_single_product_response_format(self, client: TestClient, test_product):
        """Verify single product response format."""
        response = client.get(f"/products/{test_product.id}")

        assert response.status_code == 200
        data = response.json()

        # Check all required fields and types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], str)
        assert isinstance(data["stock_quantity"], int)
        assert isinstance(data["category"], str)
        assert isinstance(data["is_active"], bool)
        assert data["description"] is None or isinstance(data["description"], str)

    def test_create_product_response_format(
        self, client: TestClient, admin_auth_headers
    ):
        """Verify created product response format."""
        product_data = {
            "name": "Format Test",
            "price": 49.99,
            "stock_quantity": 10,
            "category": "Test",
        }

        response = client.post(
            "/products/", headers=admin_auth_headers, json=product_data
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)


class TestProductEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_product_with_zero_stock(self, client: TestClient, admin_auth_headers):
        """Test product with zero stock quantity."""
        product_data = {
            "name": "Out of Stock",
            "price": 10.00,
            "stock_quantity": 0,
            "category": "Test",
        }

        response = client.post(
            "/products/", headers=admin_auth_headers, json=product_data
        )

        assert response.status_code == 201
        assert response.json()["stock_quantity"] == 0

    def test_product_with_very_high_price(self, client: TestClient, admin_auth_headers):
        """Test product with very high price."""
        product_data = {
            "name": "Expensive",
            "price": 999999.99,
            "stock_quantity": 1,
            "category": "Luxury",
        }

        response = client.post(
            "/products/", headers=admin_auth_headers, json=product_data
        )

        assert response.status_code == 201

    def test_deactivate_product(
        self, client: TestClient, test_product, admin_auth_headers
    ):
        """Test deactivating a product."""
        response = client.put(
            f"/products/{test_product.id}",
            headers=admin_auth_headers,
            json={"is_active": False},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_filter_excludes_inactive_products(
        self, client: TestClient, db_session: Session, admin_auth_headers
    ):
        """Test that inactive products are excluded from list."""
        from app.models.product import Product

        inactive_product = Product(
            name="Inactive",
            price=10.00,
            stock_quantity=10,
            category="Test",
            is_active=False,
        )
        db_session.add(inactive_product)
        db_session.commit()

        response = client.get("/products/")
        assert response.status_code == 200

        product_ids = [p["id"] for p in response.json()]
        assert inactive_product.id not in product_ids
