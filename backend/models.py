from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class FileEntry(SQLModel, table=True):
    """
    Database model for tracking file metadata across devices.
    The Pi does NOT store actual files, only metadata.
    Files are retrieved via SCP from source devices on-demand.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str = Field(index=True)  # Original file name (for searching)
    absolute_path: str  # Full absolute path on the source device
    device: str = Field(index=True)  # Device/computer name (hostname)
    device_ip: str  # IP address of the device for SCP retrieval
    last_modified_time: datetime  # Last modification time of the file
    created_time: datetime  # When record was created in DB
    size: int  # File size in bytes
    file_type: str  # File extension or MIME type
      
      
    class Config:
        from_attributes = True

class FileSearchResponse(SQLModel):
    """
    Response model for file search results
    """
    id: int
    file_name: str
    absolute_path: str
    device: str
    device_ip: str
    last_modified_time: datetime
    created_time: datetime
    size: int
    file_type: str