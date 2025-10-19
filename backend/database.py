"""
Database module for distributed file transfer system.
Handles file metadata storage using SQLModel ORM with SQLite.
"""

from sqlmodel import SQLModel, create_engine, Session
from datetime import datetime
import os
from models import File

DATABASE_PATH = 'files.db'
engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)


def init_db():
    """Initialize the database, creating all tables."""
    SQLModel.metadata.create_all(engine)
    print(f"Database initialized at {DATABASE_PATH}")


def get_session():
    """Get a database session for FastAPI dependency injection."""
    with Session(engine) as session:
        yield session


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
    session = Session(engine)
    try:
        existing_file = session.query(File).filter_by(path=path).first()
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
    session = Session(engine)
    try:
        file = session.query(File).filter_by(filename=filename).first()
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
    session = Session(engine)
    try:
        file = session.query(File).filter_by(id=file_id).first()
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
    session = Session(engine)
    try:
        files = session.query(File).all()
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
    session = Session(engine)
    try:
        files = session.query(File).filter_by(alias=alias).all()
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
    session = Session(engine)
    try:
        files = session.query(File).filter_by(device=device).all()
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
    session = Session(engine)
    try:
        file = session.query(File).filter_by(filename=filename).first()
        if not file:
            print(f"File '{filename}' not found.")
            return None
        
        allowed_fields = ['device', 'path', 'alias', 'size', 'file_type']
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(file, key):
                setattr(file, key, value)
        
        file.modified_at = datetime.utcnow()
        
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
    session = Session(engine)
    try:
        file = session.query(File).filter_by(filename=filename).first()
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
    session = Session(engine)
    try:
        count = session.query(File).delete()
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
    from sqlalchemy import func
    session = Session(engine)
    try:
        total_files = session.query(File).count()
        total_size = session.query(func.sum(File.size)).scalar() or 0
        
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
