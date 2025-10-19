from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Database file location
DB_FILE = "file_sync.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """
    Create database tables
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependency to get database session
    """
    with Session(engine) as session:
        yield session
