# Testing Documentation

## Testing Framework

This project uses **pytest** as the testing framework, with the following plugins:
- `pytest-flask`: Flask application testing support
- `pytest-cov`: Code coverage reporting
- `pytest-mock`: Mock functionality
- `pytest-xdist`: Parallel test execution
- `responses`: HTTP request mocking
- `faker`: Test data generation

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── pytest.ini               # Pytest configuration file
├── unit/                    # Unit tests
│   ├── test_models.py       # Model tests
│   ├── test_auth.py         # Authentication utility tests
│   ├── test_services.py     # Service layer tests
│   └── test_utils.py        # Utility function tests
├── integration/             # Integration tests
│   ├── test_auth_api.py     # Authentication API tests
│   ├── test_invoices_api.py # Invoice API tests
│   ├── test_admin_api.py    # Admin API tests
│   ├── test_ocr_xml_api.py  # OCR/XML API tests
│   └── test_email_api.py    # Email API tests
├── fixtures/                # Test data fixtures
│   ├── users.py             # User test data
│   └── invoices.py          # Invoice test data
└── helpers/                 # Test helper functions
    └── client.py            # Flask test client utilities
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run tests with specific markers
pytest -m unit
pytest -m integration
pytest -m auth
pytest -m admin

# Exclude slow tests
pytest -m "not slow"

# Verbose output
pytest -v

# Show print output
pytest -s

# Run only failed tests
pytest --lf

# Stop after first failure
pytest -x
```

### Coverage Reports

```bash
# Generate coverage report (terminal)
pytest --cov=backend --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# View report (open in browser)
open htmlcov/index.html
```

### Parallel Execution

```bash
# Automatically detect CPU cores for parallel execution
pytest -n auto

# Specify number of parallel processes
pytest -n 4
```

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.auth` - Authentication related tests
- `@pytest.mark.admin` - Admin functionality tests
- `@pytest.mark.slow` - Slow tests (require external APIs)
- `@pytest.mark.skip_ci` - Tests to skip in CI environment

## Test Fixtures

### Application and Database
- `app` - Flask test application instance
- `db_session` - Database session (independent transaction per test)

### Authentication
- `test_user` - Test user
- `admin_user` - Admin user
- `auth_headers` - Authentication headers
- `admin_headers` - Admin authentication headers
- `auth_client` - Authenticated test client

### Test Data
- `user_factory` - User factory function
- `invoice_factory` - Invoice factory function
- `multiple_users` - Multiple test users
- `multiple_invoices` - Multiple test invoices

## Testing Best Practices

1. **Test Isolation**: Each test uses an independent transaction, automatically rolled back after test
2. **Mock External Dependencies**: Use responses library to mock external API calls
3. **Use Factory Functions**: Create test data through fixtures
4. **Descriptive Naming**: Test function names should clearly describe what is being tested
5. **AAA Pattern**: Arrange (Setup) - Act (Execute) - Assert (Verify)

## CI/CD Integration

Running tests in CI environment:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests and generate coverage report
pytest --cov=backend --cov-report=xml --cov-report=term

# Run only non-slow tests (in CI)
pytest -m "not slow"
```

## Notes

1. **Test Database**: Uses SQLite in-memory database, completely isolated from development/production databases
2. **Environment Variables**: Tests use test configuration, do not depend on .env file
3. **File Cleanup**: Temporary files created by tests are automatically cleaned up
4. **External APIs**: All external API calls are mocked, no real requests are made
