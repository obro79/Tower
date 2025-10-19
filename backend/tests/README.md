# Testing Guide

This directory contains all tests for the File Sync API. Tests are built with **pytest** for comprehensive testing and validation.

## Setup

Tests require the following packages (already installed):
```bash
pip install pytest pytest-asyncio
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_models.py
```

### Run specific test class
```bash
pytest tests/test_models.py::TestFileModelCreation
```

### Run specific test function
```bash
pytest tests/test_models.py::TestFileModelCreation::test_file_creation_success
```

### Run only unit tests (fast)
```bash
pytest -m unit
```

### Run only integration tests (API endpoints)
```bash
pytest -m integration
```

### Run with coverage
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

### Run and stop on first failure
```bash
pytest -x
```

## Test Structure

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Shared fixtures and configuration
├── test_models.py           # File model validation tests
├── test_database.py         # Database CRUD operation tests
├── test_api.py              # FastAPI endpoint tests
└── README.md                # This file
```

### conftest.py
Contains reusable pytest fixtures:
- `in_memory_engine`: In-memory SQLite database engine for testing
- `in_memory_session`: Fresh database session for each test
- `test_client`: FastAPI TestClient with dependency overrides
- `sample_file`: Single File fixture
- `multiple_files`: List of 5 sample File objects
- `populated_db`: Pre-populated database session with sample data

### test_models.py
Tests for the File SQLModel:
- `TestFileModelCreation`: Model instantiation tests
- `TestFileModelValidation`: Field validation and constraints
- `TestFileModelMethods`: __repr__() and to_dict() methods
- `TestFileModelEdgeCases`: Boundary values, unicode, special characters

### test_database.py
Tests for database.py CRUD functions:
- `TestDatabaseInitialization`: Database setup
- `TestAddFile`: add_file() function
- `TestGetFile`: get_file() function
- `TestGetFileById`: get_file_by_id() function
- `TestGetAllFiles`: get_all_files() function
- `TestGetFilesByOwner`: get_files_by_owner() function
- `TestGetFilesByDevice`: get_files_by_device() function
- `TestUpdateFile`: update_file() function
- `TestDeleteFile`: delete_file() function
- `TestDeleteAllFiles`: delete_all_files() function
- `TestDatabaseStats`: get_database_stats() function
- `TestDatabaseErrors`: Error handling and session cleanup

### test_api.py
Tests for FastAPI endpoints:
- `TestHealthCheck`: GET / endpoint
- `TestSearchFiles`: GET /files/search endpoint (with wildcard patterns)
- `TestGetFileMetadata`: GET /files/{file_id} endpoint
- `TestRegisterFile`: POST /files/register endpoint
- `TestDeleteFileMetadata`: DELETE /files/{file_id} endpoint
- `TestEndpointIntegration`: Full workflow tests

## Writing New Tests

### Template: Simple Test
```python
def test_my_feature(self, client):
    response = client.get("/endpoint")
    assert response.status_code == 200
```

### Template: Test with Database
```python
def test_database_operation(self, in_memory_session):
    file = File(
        filename="test.txt",
        device="dev",
        path="/test.txt",
        alias="user",
        size=100
    )
    in_memory_session.add(file)
    in_memory_session.commit()
    
    result = in_memory_session.query(File).first()
    assert result.filename == "test.txt"
```

### Template: Test with Wildcard Search
```python
def test_search_with_wildcard(self, test_client):
    add_file("test_doc.txt", "dev", "/test_doc.txt", "user", 100)
    add_file("test_img.jpg", "dev", "/test_img.jpg", "user", 200)
    
    response = test_client.get("/files/search?query=test*")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
```

### Template: Parametrized Test
```python
@pytest.mark.parametrize("file_type", ["pdf", "txt", "jpg"])
def test_multiple_file_types(self, file_type):
    file = File(
        filename=f"test.{file_type}",
        device="dev",
        path=f"/test.{file_type}",
        alias="user",
        size=1024,
        file_type=file_type
    )
    assert file.file_type == file_type
```

## Code Style & Conventions

### Naming
- Test classes: `Test<Feature>` (e.g., `TestFileModelCreation`)
- Test functions: `test_<action>_<expected_outcome>` (e.g., `test_file_creation_success`)
- Test fixtures: descriptive lowercase (e.g., `sample_file`)

### Assertions
```python
assert response.status_code == 200
assert data["filename"] == expected_value
assert "substring" in response_text
```

### API Testing Pattern
```python
def test_endpoint(self, test_client, sample_data):
    # 1. Prepare
    payload = {...}
    
    # 2. Act
    response = test_client.post("/endpoint", json=payload)
    
    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["field"] == expected
```

## Adding a New Test Module

1. Create `tests/test_<feature>.py`
2. Import required fixtures from `conftest.py`
3. Define test classes and functions with `Test` prefix and `test_` prefix
4. Add pytest marker: `@pytest.mark.unit` or `@pytest.mark.integration`
5. Add docstrings explaining test purpose
6. Run: `pytest tests/test_<feature>.py`

Example:
```python
import pytest
from models import File

pytestmark = pytest.mark.unit

class TestNewFeature:
    """Test new functionality."""
    
    def test_something(self, test_client):
        """Test description."""
        response = test_client.get("/endpoint")
        assert response.status_code == 200
```

## Fixtures Quick Reference

| Fixture | Type | Purpose |
|---------|------|---------|
| `in_memory_engine` | Engine | In-memory SQLite database engine |
| `in_memory_session` | Session | Fresh database session for each test |
| `test_client` | TestClient | FastAPI test client with DB override |
| `sample_file` | File | Single sample File object |
| `multiple_files` | List[File] | List of 5 sample File objects |
| `populated_db` | Session | Pre-populated database session |

## Tips

- Use in-memory database for fast, isolated tests
- Each test gets a fresh DB - no state carries over
- Use fixtures for setup/teardown - much cleaner than manual setup
- Parametrized tests reduce code duplication
- Keep test functions focused on a single behavior
- Mark tests with `@pytest.mark.unit` or `@pytest.mark.integration`

## Troubleshooting

**Tests fail with import errors:**
- Make sure you're in the `.venv`: `source .venv/bin/activate`
- Check that models.py, database.py, and main.py are in the backend root

**Database issues:**
- Tests use in-memory DB, so they don't affect production data
- Each test gets a fresh DB - no state carries over
- Use `populated_db` fixture for pre-seeded tests

**Test dependencies not installed:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Coverage

Monitor test coverage with pytest-cov:
```bash
pytest --cov=. --cov-report=html
```

View HTML report in `htmlcov/index.html`

**Coverage targets:**
- `models.py`: 100% (File model)
- `database.py`: 95%+ (all CRUD functions)
- `main.py`: 90%+ (all endpoints)
- **Total: 90%+**

## Test Markers

Available markers defined in `pytest.ini`:
- `@pytest.mark.unit` - Fast, isolated tests (models, database functions)
- `@pytest.mark.integration` - API endpoint tests
- `@pytest.mark.slow` - Long-running tests (optional)

**Run specific markers:**
```bash
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests
pytest -m "unit or integration"  # Both
```

## Continuous Integration

To verify all changes:
```bash
# Run all tests
pytest -v

# With coverage
pytest --cov=. -v

# Integration tests only
pytest -m integration -v
```
