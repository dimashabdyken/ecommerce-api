"""Comprehensive tests for payment and order endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestCheckout:
    """Test POST /payments/checkout endpoint."""

    @patch("stripe.PaymentIntent.create")
    def test_checkout_success(
        self,
        mock_stripe,
        client: TestClient,
        auth_headers,
        test_product,
        db_session: Session,
    ):
        """Test successful checkout with items in cart."""
        # Mock Stripe response
        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        # Add item to cart
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        # Checkout
        checkout_data = {}
        response = client.post(
            "/payments/checkout", headers=auth_headers, json=checkout_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "client_secret" in data
        assert "order_id" in data
        assert data["client_secret"] == "secret_test123"

    def test_checkout_empty_cart(self, client: TestClient, auth_headers):
        """Test checkout with empty cart."""
        checkout_data = {}
        response = client.post(
            "/payments/checkout", headers=auth_headers, json=checkout_data
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @patch("stripe.PaymentIntent.create")
    def test_checkout_insufficient_stock(
        self, mock_stripe, client: TestClient, auth_headers, db_session: Session
    ):
        """Test checkout when product has insufficient stock."""
        from app.models.product import Product

        # Create product with limited stock
        product = Product(
            name="Limited Stock",
            price=10.00,
            stock_quantity=2,  # Only 2 in stock
            category="Test",
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Try to add 5 to cart and checkout
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": product.id, "quantity": 5},
        )

        checkout_data = {}
        response = client.post(
            "/payments/checkout", headers=auth_headers, json=checkout_data
        )

        assert response.status_code == 400
        assert "insufficient stock" in response.json()["detail"].lower()

    @patch("stripe.PaymentIntent.create")
    def test_checkout_stripe_error(
        self, mock_stripe, client: TestClient, auth_headers, test_product
    ):
        """Test checkout when Stripe throws an error."""
        import stripe

        mock_stripe.side_effect = stripe.error.StripeError("Payment failed")

        # Add item to cart
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 1},
        )

        checkout_data = {}
        response = client.post(
            "/payments/checkout", headers=auth_headers, json=checkout_data
        )

        assert response.status_code == 400
        assert "stripe error" in response.json()["detail"].lower()

    def test_checkout_unauthorized(self, client: TestClient):
        """Test checkout without authentication."""
        checkout_data = {}
        response = client.post("/payments/checkout", json=checkout_data)

        assert response.status_code == 401


class TestGetOrders:
    """Test GET /payments/orders endpoint."""

    @patch("stripe.PaymentIntent.create")
    def test_get_orders_empty(self, mock_stripe, client: TestClient, auth_headers):
        """Test getting orders when user has none."""
        response = client.get("/payments/orders", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    @patch("stripe.PaymentIntent.create")
    def test_get_orders_with_data(
        self, mock_stripe, client: TestClient, auth_headers, test_product
    ):
        """Test getting orders after creating one."""
        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        # Add item to cart and checkout
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 1},
        )
        checkout_response = client.post(
            "/payments/checkout", headers=auth_headers, json={}
        )
        assert checkout_response.status_code == 200

        # Get orders
        response = client.get("/payments/orders", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert isinstance(data, list)

    def test_get_orders_unauthorized(self, client: TestClient):
        """Test getting orders without authentication."""
        response = client.get("/payments/orders")

        assert response.status_code == 401

    @patch("stripe.PaymentIntent.create")
    def test_orders_isolation_between_users(
        self,
        mock_stripe,
        client: TestClient,
        auth_headers,
        admin_auth_headers,
        test_product,
    ):
        """Test that users only see their own orders."""
        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        # User 1 creates order
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 1},
        )
        client.post("/payments/checkout", headers=auth_headers, json={})

        # User 2 should have no orders
        admin_orders = client.get("/payments/orders", headers=admin_auth_headers)
        assert len(admin_orders.json()) == 0

        # User 1 should have their order
        user_orders = client.get("/payments/orders", headers=auth_headers)
        assert len(user_orders.json()) == 1


class TestGetOrder:
    """Test GET /payments/orders/{order_id} endpoint."""

    @patch("stripe.PaymentIntent.create")
    def test_get_order_success(
        self, mock_stripe, client: TestClient, auth_headers, test_product
    ):
        """Test getting a specific order."""
        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        # Create order
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        checkout_response = client.post(
            "/payments/checkout", headers=auth_headers, json={}
        )
        order_id = checkout_response.json()["order_id"]

        # Get specific order
        response = client.get(f"/payments/orders/{order_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert "total_amount" in data
        assert "status" in data
        assert "items" in data

    def test_get_order_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent order."""
        response = client.get("/payments/orders/99999", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("stripe.PaymentIntent.create")
    def test_get_order_wrong_user(
        self,
        mock_stripe,
        client: TestClient,
        auth_headers,
        admin_auth_headers,
        test_product,
    ):
        """Test that users can't access other users' orders."""
        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        # User 1 creates order
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 1},
        )
        checkout_response = client.post(
            "/payments/checkout", headers=auth_headers, json={}
        )
        order_id = checkout_response.json()["order_id"]

        # User 2 tries to access it
        response = client.get(
            f"/payments/orders/{order_id}", headers=admin_auth_headers
        )

        assert response.status_code == 404

    def test_get_order_unauthorized(self, client: TestClient):
        """Test getting order without authentication."""
        response = client.get("/payments/orders/1")

        assert response.status_code == 401


class TestStripeWebhook:
    """Test POST /payments/webhook endpoint."""

    def test_webhook_missing_signature(self, client: TestClient):
        """Test webhook without signature header."""
        response = client.post("/payments/webhook", json={})

        # Should fail without proper stripe signature
        assert response.status_code in [400, 500]

    @patch("stripe.Webhook.construct_event")
    def test_webhook_invalid_signature(self, mock_webhook, client: TestClient):
        """Test webhook with invalid signature."""
        import stripe

        mock_webhook.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )

        response = client.post(
            "/payments/webhook",
            content=b"payload",
            headers={"stripe-signature": "invalid"},
        )

        assert response.status_code == 400

    @patch("stripe.Webhook.construct_event")
    def test_webhook_payment_succeeded(
        self, mock_webhook, client: TestClient, db_session: Session
    ):
        """Test webhook handling payment_intent.succeeded event."""
        from app.core.security import get_password_hash
        from app.models.order import Order, OrderStatus
        from app.models.user import User

        # Create user and order
        user = User(
            email="webhook@test.com",
            hashed_password=get_password_hash("test123"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        order = Order(
            user_id=user.id,
            total_amount=100.00,
            status=OrderStatus.PENDING,
            stripe_payment_intent_id="pi_test123",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # Mock webhook event
        mock_webhook.return_value = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "metadata": {"order_id": str(order.id), "user_id": str(user.id)}
                }
            },
        }

        response = client.post(
            "/payments/webhook",
            content=b"payload",
            headers={"stripe-signature": "valid_sig"},
        )

        # Should return 200 for successful webhook processing
        assert response.status_code == 200


class TestPaymentResponseFormats:
    """Test response format consistency for payment endpoints."""

    @patch("stripe.PaymentIntent.create")
    def test_checkout_response_format(
        self, mock_stripe, client: TestClient, auth_headers, test_product
    ):
        """Verify checkout response format."""
        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 1},
        )

        response = client.post("/payments/checkout", headers=auth_headers, json={})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data["client_secret"], str)
        assert isinstance(data["order_id"], int)

    @patch("stripe.PaymentIntent.create")
    def test_order_response_format(
        self, mock_stripe, client: TestClient, auth_headers, test_product
    ):
        """Verify order response format."""
        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        checkout_response = client.post(
            "/payments/checkout", headers=auth_headers, json={}
        )
        order_id = checkout_response.json()["order_id"]

        response = client.get(f"/payments/orders/{order_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check order fields
        assert isinstance(data["id"], int)
        assert isinstance(data["user_id"], int)
        assert isinstance(data["total_amount"], str)  # Decimal as string
        assert isinstance(data["status"], str)
        assert isinstance(data["items"], list)

        # Check order item fields
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert isinstance(item["product_id"], int)
            assert isinstance(item["quantity"], int)
            assert isinstance(item["price_at_purchase"], str)


class TestPaymentEdgeCases:
    """Test edge cases and complex scenarios."""

    @patch("stripe.PaymentIntent.create")
    def test_checkout_calculates_total_correctly(
        self, mock_stripe, client: TestClient, auth_headers, db_session: Session
    ):
        """Test that checkout calculates total amount correctly."""
        from decimal import Decimal

        from app.models.product import Product

        mock_stripe.return_value = MagicMock(
            id="pi_test123", client_secret="secret_test123"
        )

        # Create products with specific prices
        product1 = Product(
            name="Product 1",
            price=Decimal("10.50"),
            stock_quantity=10,
            category="Test",
            is_active=True,
        )
        product2 = Product(
            name="Product 2",
            price=Decimal("25.75"),
            stock_quantity=10,
            category="Test",
            is_active=True,
        )
        db_session.add_all([product1, product2])
        db_session.commit()

        # Add items to cart
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": product1.id, "quantity": 2},  # 21.00
        )
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": product2.id, "quantity": 1},  # 25.75
        )

        # Checkout
        checkout_response = client.post(
            "/payments/checkout", headers=auth_headers, json={}
        )
        order_id = checkout_response.json()["order_id"]

        # Get order and check total
        order_response = client.get(
            f"/payments/orders/{order_id}", headers=auth_headers
        )
        total = float(order_response.json()["total_amount"])

        expected_total = (10.50 * 2) + (25.75 * 1)
        assert abs(total - expected_total) < 0.01  # Allow small float precision diff

    @patch("stripe.PaymentIntent.create")
    def test_multiple_checkouts_create_separate_orders(
        self,
        mock_stripe,
        client: TestClient,
        auth_headers,
        test_product,
        db_session: Session,
    ):
        """Test that multiple checkouts create separate orders."""
        # Mock Stripe to return different payment intent IDs
        mock_stripe.side_effect = [
            MagicMock(id="pi_test_order1", client_secret="secret_order1"),
            MagicMock(id="pi_test_order2", client_secret="secret_order2"),
        ]

        # First checkout
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 1},
        )
        first_checkout = client.post(
            "/payments/checkout", headers=auth_headers, json={}
        )
        assert first_checkout.status_code == 200

        # After checkout, cart is deleted. Need to add more items for second checkout
        # Get a fresh cart (will be auto-created)
        client.get("/cart/", headers=auth_headers)

        # Add items for second order
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        # Create second order
        second_checkout = client.post(
            "/payments/checkout", headers=auth_headers, json={}
        )
        assert second_checkout.status_code == 200

        # Check we have multiple orders
        orders_response = client.get("/payments/orders", headers=auth_headers)
        orders = orders_response.json()
        assert len(orders) == 2
