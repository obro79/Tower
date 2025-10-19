"""
Database module for file sync system.
Handles file metadata storage using SQLModel with SQLite.
"""

from sqlmodel import SQLModel, create_engine, Session
from models import FileRecord
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./file_records.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """
    Initialize the database, creating all tables.
    """
    SQLModel.metadata.create_all(engine)
    logger.info(f"Database initialized at {DATABASE_URL}")


def get_session():
    """
    Dependency to get database session.
    Used by FastAPI endpoints.
    """
    with Session(engine) as session:
        yield session
