from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class File(Base):
    """
    File metadata model.
    
    Attributes:
        id: Primary key
        filename: Filename
        device: Device identifier (e.g., 'client_a', 'client_b')
        path: Unique file path on the storage system
        alias: Owner/uploader identifier
        size: File size in bytes
        uploaded_at: Timestamp when file was uploaded
        modified_at: Last modification timestamp
        file_type: File extension/type (e.g., 'txt', 'pdf', 'jpg')
    """
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False, index=True)
    device = Column(String, nullable=False)
    path = Column(String, unique=True, nullable=False)
    alias = Column(String, nullable=False, index=True)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    file_type = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}', alias='{self.alias}', size={self.size})>"
    
    def to_dict(self):
        """Convert file object to dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'device': self.device,
            'path': self.path,
            'alias': self.alias,
            'size': self.size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'file_type': self.file_type
        }
