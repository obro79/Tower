from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class FileEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str = Field(index=True)
    device: str
    last_modified: datetime
    creation_time: datetime
    size: int
    file_type: str
