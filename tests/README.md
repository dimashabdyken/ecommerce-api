# API Testing Suite

## 🔍 Test Coverage Overview

This comprehensive test suite validates all FastAPI endpoints for:
- ✅ **GET/POST/PUT/DELETE operations**
- ✅ **Error handling and edge cases**
- ✅ **Response format validation**
- ✅ **Authentication and authorization**
- ✅ **Data isolation between users**

## 📋 Test Files

### `test_auth.py` (17 tests)
**Authentication endpoints testing**
- User registration (POST /auth/register)
- User login (POST /auth/login)
- Get current user (GET /auth/me)
- Error handling: duplicate emails, invalid credentials, missing fields
- Response format validation

### `test_users.py` (24 tests)
**User profile and address management**
- Get/update user profile (GET/PUT /users/me)
- Password changes (PUT /users/me/password)
- Address CRUD operations (GET/POST/PUT/DELETE /users/me/addresses)
- Error handling: duplicate emails, invalid passwords, non-existent addresses
- Authorization checks

### `test_cart.py` (23 tests)
**Shopping cart operations**
- Get cart (GET /cart/)
- Add items (POST /cart/items)
- Update quantities (PUT /cart/items/{id})
- Remove items (DELETE /cart/items/{id})
- Clear cart (DELETE /cart/)
- Edge cases: invalid quantities, non-existent products, user isolation

### `test_products.py` (34 tests)
**Product catalog management**
- List products with filters (GET /products/)
  - Search, category filtering
  - Price range filtering
  - Stock availability
  - Sorting and pagination
- Get single product (GET /products/{id})
- Create product (POST /products/) - Admin only
- Update product (PUT /products/{id}) - Admin only
- Delete product (DELETE /products/{id}) - Admin only
- Error handling: not found, unauthorized access
- Response format validation

### `test_payments.py` (19 tests)
**Payment and order processing**
- Checkout (POST /payments/checkout)
- Get orders (GET /payments/orders)
- Get order by ID (GET /payments/orders/{id})
- Stripe webhook handling (POST /payments/webhook)
- Error handling: empty cart, insufficient stock, Stripe errors
- Order isolation between users

## 🎯 Total Test Count: **117 comprehensive tests**

## 🚀 Running Tests

### Run all tests:
```bash
pytest
```

### Run with verbose output:
```bash
pytest -v
```

### Run specific test file:
```bash
pytest tests/test_auth.py -v
```

### Run with coverage report:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test class:
```bash
pytest tests/test_products.py::TestListProducts -v
```

### Run specific test:
```bash
pytest tests/test_auth.py::TestAuthRegister::test_register_success -v
```

## 📊 Test Categories

### ✅ HTTP Methods Covered
- **GET**: List resources, retrieve single items
- **POST**: Create resources, authentication, checkout
- **PUT**: Update resources, profile changes
- **DELETE**: Remove resources, clear cart

### ✅ Error Handling Tested
- **400 Bad Request**: Invalid input, validation errors
- **401 Unauthorized**: Missing/invalid authentication
- **403 Forbidden**: Insufficient permissions (non-admin)
- **404 Not Found**: Non-existent resources
- **422 Unprocessable Entity**: Schema validation failures

### ✅ Response Format Validation
- JSON content-type headers
- Required fields presence
- Correct data types (int, string, bool, list)
- Sensitive data exclusion (passwords)
- Decimal handling (prices)

## 🔒 Security Tests
- Authentication required for protected endpoints
- Admin authorization for product management
- User data isolation (orders, carts, addresses)
- Password hashing verification
- Token validation

## 🎨 Test Structure

Each test file follows this pattern:
```python
class TestEndpointName:
    """Test specific endpoint functionality."""
    
    def test_success_case(self, client, fixtures):
        """Test successful operation."""
        # Arrange, Act, Assert
        
    def test_error_case(self, client):
        """Test error handling."""
        # Verify proper error responses
        
    def test_edge_case(self, client, fixtures):
        """Test boundary conditions."""
        # Test unusual but valid scenarios
```

## 🛠️ Fixtures Available

Defined in `conftest.py`:
- `client`: TestClient for making requests
- `db_session`: Fresh database for each test
- `test_user`: Regular user account
- `admin_user`: Admin user account
- `auth_headers`: Authentication headers for test user
- `admin_auth_headers`: Authentication headers for admin
- `test_product`: Sample product in database

## 📝 Test Naming Convention

- `test_<action>_success`: Happy path tests
- `test_<action>_<error_type>`: Error condition tests
- `test_<action>_unauthorized`: Auth/authz tests
- `test_<action>_invalid_<field>`: Validation tests
- `test_<action>_edge_case`: Boundary condition tests

## 🔄 Continuous Testing

Integrate with CI/CD:
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest --cov=app --cov-report=xml
  
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## 🎯 Test Quality Metrics

- **Coverage**: Aims for 95%+ code coverage
- **Independence**: Each test is isolated with fresh database
- **Speed**: Uses in-memory SQLite for fast execution
- **Clarity**: Descriptive test names and docstrings
- **Maintainability**: DRY principles with shared fixtures

## 🐛 Troubleshooting

### Tests fail with database errors:
- Ensure SQLAlchemy models are properly imported
- Check that all tables are created in `conftest.py`

### Authentication tests fail:
- Verify password hashing is working
- Check JWT token generation and validation

### Async tests fail:
- Products endpoint uses async, ensure proper test client usage
- May need httpx.AsyncClient for true async testing

## 📚 Further Improvements

- [ ] Add performance/load testing with locust or k6
- [ ] Add contract testing with Pact
- [ ] Add API schema validation tests
- [ ] Add integration tests with real database
- [ ] Add end-to-end tests with Playwright
- [ ] Add mutation testing with mutmut

---

**API Tester Notes**: All endpoints validated for functional correctness, error handling, and response consistency. Security boundaries enforced. Ready for production deployment after review.
