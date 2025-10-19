import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient

from models import File
from main import app
from database import get_session, _test_engine


@pytest.fixture
def in_memory_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(autouse=True)
def setup_test_engine(in_memory_engine):
    """Automatically set up test engine for all tests."""
    token = _test_engine.set(in_memory_engine)
    SQLModel.metadata.create_all(in_memory_engine)
    yield
    _test_engine.reset(token)


@pytest.fixture
def in_memory_session(in_memory_engine):
    """Provide a fresh database session for each test."""
    with Session(in_memory_engine) as session:
        yield session


@pytest.fixture
def test_client(in_memory_engine, setup_test_engine):
    """FastAPI TestClient with dependency override."""    
    def override_get_session():
        with Session(in_memory_engine) as session:
            yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_file():
    """Single File object for testing."""
    return File(
        filename="test_document.pdf",
        device="device_a",
        path="/home/user/documents/test_document.pdf",
        alias="user_alice",
        size=1024000,
        file_type="pdf"
    )


@pytest.fixture
def multiple_files():
    """List of 5 different File objects with varying attributes."""
    now = datetime.now(timezone.utc)
    return [
        File(
            filename="report_2024.pdf",
            device="laptop_1",
            path="/docs/report_2024.pdf",
            alias="alice",
            size=2048000,
            file_type="pdf",
            uploaded_at=now - timedelta(days=5),
            modified_at=now - timedelta(days=5)
        ),
        File(
            filename="data.csv",
            device="laptop_1",
            path="/data/metrics.csv",
            alias="alice",
            size=512000,
            file_type="csv",
            uploaded_at=now - timedelta(days=3),
            modified_at=now - timedelta(days=1)
        ),
        File(
            filename="image_001.jpg",
            device="phone_1",
            path="/photos/image_001.jpg",
            alias="bob",
            size=4096000,
            file_type="jpg",
            uploaded_at=now - timedelta(days=10),
            modified_at=now - timedelta(days=10)
        ),
        File(
            filename="notes.txt",
            device="laptop_2",
            path="/workspace/notes.txt",
            alias="charlie",
            size=256000,
            file_type="txt",
            uploaded_at=now - timedelta(days=2),
            modified_at=now - timedelta(days=2)
        ),
        File(
            filename="archive.zip",
            device="server",
            path="/backups/archive.zip",
            alias="alice",
            size=10485760,
            file_type="zip",
            uploaded_at=now - timedelta(days=1),
            modified_at=now - timedelta(days=1)
        ),
    ]


@pytest.fixture
def populated_db(in_memory_session, multiple_files):
    """Pre-populated database session with sample files."""
    for file in multiple_files:
        in_memory_session.add(file)
    in_memory_session.commit()
    yield in_memory_session
    in_memory_session.rollback()
