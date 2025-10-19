from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class FileRecord(SQLModel, table=True):
    """
    File metadata model for storing file information across devices.

    This table stores ONLY metadata - no actual files are stored on the Pi.
    Files are retrieved via SCP from source devices on demand.
    """
    __tablename__ = "file_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str = Field(index=True, description="Original file name")
    absolute_path: str = Field(description="Full path on source device")
    device: str = Field(index=True, description="Device hostname/name")
    device_ip: str = Field(description="IP address for SCP connection")
    device_user: str = Field(description="SSH username for SCP")
    last_modified_time: datetime = Field(description="Last modification time of file")
    created_time: datetime = Field(default_factory=datetime.utcnow, description="When record was created in DB")
    size: int = Field(description="File size in bytes")
    file_type: str = Field(description="File extension (e.g., .txt, .pdf)")


class FileSearchResponse(SQLModel):
    """
    Response model for file search results.
    Matches FileRecord but used for API responses.
    """
    id: int
    file_name: str
    absolute_path: str
    device: str
    device_ip: str
    device_user: str
    last_modified_time: datetime
    created_time: datetime
    size: int
    file_type: str


class EmbeddingRequest(BaseModel):
    """
    Request model for registering file embeddings.
    Client sends this after registering file metadata.
    """
    file_id: int
    embedding: List[float]


class SemanticSearchRequest(BaseModel):
    """
    Request model for semantic search queries.
    Client generates embedding from query text and sends it here.
    """
    query_embedding: List[float]
    k: int = 5


class SemanticSearchResult(BaseModel):
    """
    Response model for semantic search results.
    Includes similarity score along with file metadata.
    """
    file_id: int
    file_name: str
    absolute_path: str
    device: str
    device_ip: str
    device_user: str
    last_modified_time: datetime
    size: int
    file_type: str
    similarity_score: float
