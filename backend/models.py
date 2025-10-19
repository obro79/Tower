from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class File(SQLModel, table=True):
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
    __tablename__ = "files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    device: str
    path: str = Field(unique=True)
    alias: str = Field(index=True)
    size: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    file_type: Optional[str] = None
    
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
            'uploaded_at': self.uploaded_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'file_type': self.file_type
        }
