"""
Database module for distributed file transfer system.
Handles file metadata storage using SQLModel ORM with SQLite.
"""

from sqlmodel import SQLModel, create_engine, Session, select
from datetime import datetime, timezone
import os
from contextvars import ContextVar
from models import File

DATABASE_PATH = 'files.db'
engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)

_test_engine: ContextVar = ContextVar('_test_engine', default=None)


def init_db():
    """Initialize the database, creating all tables."""
    current_engine = _get_engine()
    SQLModel.metadata.create_all(current_engine)
    if current_engine == engine:
        print(f"Database initialized at {DATABASE_PATH}")


def get_session():
    """Get a database session for FastAPI dependency injection."""
    current_engine = _get_engine()
    with Session(current_engine) as session:
        yield session


def _get_engine():
    """Get the current engine (test or production)."""
    test_engine = _test_engine.get()
    return test_engine if test_engine is not None else engine


def add_file(filename, device, path, alias, size, file_type=None):
    """
    Add a new file to the database.
    
    Args:
        filename: Name of the file
        device: Device identifier
        path: Storage path
        alias: Owner identifier
        size: File size in bytes
        file_type: File type/extension (optional)
    
    Returns:
        File object if successful, None if file already exists
    
    Raises:
        Exception: If database operation fails
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File).where(File.path == path)
        existing_file = session.exec(statement).first()
        if existing_file:
            print(f"File with path '{path}' already exists in database.")
            return None
        
        if file_type is None and '.' in filename:
            file_type = filename.rsplit('.', 1)[1].lower()
        
        new_file = File(
            filename=filename,
            device=device,
            path=path,
            alias=alias,
            size=size,
            file_type=file_type
        )
        
        session.add(new_file)
        session.commit()
        session.refresh(new_file)
        print(f"File '{filename}' added successfully (ID: {new_file.id})")
        return new_file
    
    except Exception as e:
        session.rollback()
        print(f"Error adding file: {e}")
        raise
    finally:
        session.close()


def get_file(filename):
    """
    Retrieve a file by filename.
    
    Args:
        filename: Name of the file to retrieve
    
    Returns:
        File object if found, None otherwise
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File).where(File.filename == filename)
        file = session.exec(statement).first()
        if file:
            session.expunge(file)
        return file
    finally:
        session.close()


def get_file_by_id(file_id):
    """
    Retrieve a file by ID.
    
    Args:
        file_id: ID of the file to retrieve
    
    Returns:
        File object if found, None otherwise
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File).where(File.id == file_id)
        file = session.exec(statement).first()
        if file:
            session.expunge(file)
        return file
    finally:
        session.close()


def get_all_files():
    """
    Retrieve all files from the database.
    
    Returns:
        List of File objects
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File)
        files = session.exec(statement).all()
        for file in files:
            session.expunge(file)
        return files
    finally:
        session.close()


def get_files_by_owner(alias):
    """
    Retrieve all files belonging to a specific alias.
    
    Args:
        alias: Owner identifier
    
    Returns:
        List of File objects
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File).where(File.alias == alias)
        files = session.exec(statement).all()
        for file in files:
            session.expunge(file)
        return files
    finally:
        session.close()


def get_files_by_device(device):
    """
    Retrieve all files from a specific device.
    
    Args:
        device: Device identifier
    
    Returns:
        List of File objects
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File).where(File.device == device)
        files = session.exec(statement).all()
        for file in files:
            session.expunge(file)
        return files
    finally:
        session.close()


def update_file(filename, **kwargs):
    """
    Update file metadata.
    
    Args:
        filename: Name of the file to update
        **kwargs: Fields to update (device, path, alias, size, file_type)
    
    Returns:
        Updated File object if successful, None if file not found
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File).where(File.filename == filename)
        file = session.exec(statement).first()
        if not file:
            print(f"File '{filename}' not found.")
            return None
        
        allowed_fields = ['device', 'path', 'alias', 'size', 'file_type']
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(file, key):
                setattr(file, key, value)
        
        file.modified_at = datetime.now(timezone.utc)
        
        session.commit()
        session.refresh(file)
        session.expunge(file)
        print(f"File '{filename}' updated successfully.")
        return file
    
    except Exception as e:
        session.rollback()
        print(f"Error updating file: {e}")
        raise
    finally:
        session.close()


def delete_file(filename):
    """
    Delete a file from the database.
    
    Args:
        filename: Name of the file to delete
    
    Returns:
        True if file was deleted, False if file not found
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File).where(File.filename == filename)
        file = session.exec(statement).first()
        if not file:
            print(f"File '{filename}' not found.")
            return False
        
        session.delete(file)
        session.commit()
        print(f"File '{filename}' deleted successfully.")
        return True
    
    except Exception as e:
        session.rollback()
        print(f"Error deleting file: {e}")
        raise
    finally:
        session.close()


def delete_all_files():
    """
    Delete all files from the database (use with caution).
    
    Returns:
        Number of files deleted
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File)
        files = session.exec(statement).all()
        count = len(files)
        for file in files:
            session.delete(file)
        session.commit()
        print(f"Deleted {count} files from database.")
        return count
    except Exception as e:
        session.rollback()
        print(f"Error deleting files: {e}")
        raise
    finally:
        session.close()


def get_database_stats():
    """
    Get database statistics.
    
    Returns:
        Dictionary with stats (total_files, total_size, etc.)
    """
    current_engine = _get_engine()
    session = Session(current_engine)
    try:
        statement = select(File)
        files = session.exec(statement).all()
        total_files = len(files)
        total_size = sum(file.size for file in files)
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    finally:
        session.close()


if __name__ != "__main__":
    if not os.path.exists(DATABASE_PATH):
        init_db()
