"""
Database module for distributed file transfer system.
Handles file metadata storage using SQLAlchemy ORM with SQLite.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sqlalchemy

# Database setup
DATABASE_PATH = 'files.db'
engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class File(Base):
    """
    File metadata model.
    
    Attributes:
        id: Primary key
        filename: Unique filename
        device: Device identifier (e.g., 'client_a', 'client_b')
        path: File path on the storage system
        owner: Owner/uploader identifier
        size: File size in bytes
        uploaded_at: Timestamp when file was uploaded
        modified_at: Last modification timestamp
        file_type: File extension/type (e.g., 'txt', 'pdf', 'jpg')
    """
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, unique=True, nullable=False, index=True)
    device = Column(String, nullable=False)
    path = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    file_type = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}', owner='{self.owner}', size={self.size})>"
    
    def to_dict(self):
        """Convert file object to dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'device': self.device,
            'path': self.path,
            'owner': self.owner,
            'size': self.size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'file_type': self.file_type
        }


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(engine)
    print(f"Database initialized at {DATABASE_PATH}")


def add_file(filename, device, path, owner, size, file_type=None):
    """
    Add a new file to the database.
    
    Args:
        filename: Name of the file
        device: Device identifier
        path: Storage path
        owner: Owner identifier
        size: File size in bytes
        file_type: File type/extension (optional)
    
    Returns:
        File object if successful, None if file already exists
    
    Raises:
        Exception: If database operation fails
    """
    session = Session()
    try:
        # Check if file already exists
        existing_file = session.query(File).filter_by(filename=filename).first()
        if existing_file:
            print(f"File '{filename}' already exists in database.")
            return None
        
        # Extract file type if not provided
        if file_type is None and '.' in filename:
            file_type = filename.rsplit('.', 1)[1].lower()
        
        # Create new file entry
        new_file = File(
            filename=filename,
            device=device,
            path=path,
            owner=owner,
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
    session = Session()
    try:
        file = session.query(File).filter_by(filename=filename).first()
        if file:
            # Detach from session to use outside
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
    session = Session()
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
    session = Session()
    try:
        files = session.query(File).all()
        # Detach all from session
        for file in files:
            session.expunge(file)
        return files
    finally:
        session.close()


def get_files_by_owner(owner):
    """
    Retrieve all files belonging to a specific owner.
    
    Args:
        owner: Owner identifier
    
    Returns:
        List of File objects
    """
    session = Session()
    try:
        files = session.query(File).filter_by(owner=owner).all()
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
    session = Session()
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
        **kwargs: Fields to update (device, path, owner, size, file_type)
    
    Returns:
        Updated File object if successful, None if file not found
    """
    session = Session()
    try:
        file = session.query(File).filter_by(filename=filename).first()
        if not file:
            print(f"File '{filename}' not found.")
            return None
        
        # Update allowed fields
        allowed_fields = ['device', 'path', 'owner', 'size', 'file_type']
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(file, key):
                setattr(file, key, value)
        
        # Update modified_at timestamp
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
    session = Session()
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
    session = Session()
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
    session = Session()
    try:
        total_files = session.query(File).count()
        total_size = session.query(File).with_entities(
            sqlalchemy.func.sum(File.size)
        ).scalar() or 0
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    finally:
        session.close()


# Initialize database on module import
if __name__ != "__main__":
    if not os.path.exists(DATABASE_PATH):
        init_db()
