from fastapi import FastAPI, Depends, HTTPException, Query, Body
from sqlmodel import Session, select, or_
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

from models import FileRecord, FileSearchResponse
from database import create_db_and_tables, get_session

app = FastAPI(title="File Sync API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    """
    Initialize database on startup
    """
    create_db_and_tables()


@app.get("/")
def read_root():
    """
    Health check endpoint
    """
    return {"status": "File Sync API is running"}


@app.get("/files/search", response_model=List[FileSearchResponse])
def search_files(
    query: str = Query(..., description="Search query for file name (supports * wildcard)"),
    session: Session = Depends(get_session)
):
    """
    GET endpoint: Fuzzy search for files by name with wildcard support
    
    Returns ONLY metadata - no actual files are stored on the Pi.
    Files will be retrieved via SCP from source devices when user confirms download.
    
    Parameters:
    - query: The search term (supports * wildcard for fuzzy matching)
             Examples: "*.txt", "report*", "*2024*", "document.pdf"
    
    Returns:
    - List of matching file metadata records
    """
    # Convert wildcard pattern to SQL LIKE pattern
    # * becomes % in SQL LIKE syntax
    like_pattern = query.replace("*", "%")
    
    # Fuzzy search on file_name (case-insensitive with LIKE)
    statement = select(FileRecord).where(FileRecord.file_name.like(f"%{like_pattern}%"))
    
    results = session.exec(statement).all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No files found matching '{query}'")
    
    return results


@app.get("/files/{file_id}", response_model=FileSearchResponse)
def get_file_metadata(file_id: int, session: Session = Depends(get_session)):
    """
    Get metadata for a specific file by its ID
    
    This returns the file location info so the CLI can initiate SCP transfer.
    
    Parameters:
    - file_id: The database ID of the file
    
    Returns:
    - File metadata including device IP and path for SCP retrieval
    """
    statement = select(FileRecord).where(FileRecord.id == file_id)
    file_record = session.exec(statement).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
    
    return file_record


class FileMetadata(BaseModel):
    """Request body for registering file metadata"""
    file_name: str
    absolute_path: str
    device: str
    device_ip: str
    device_user: str
    last_modified_time: datetime
    size: int
    file_type: str


@app.post("/files/register")
def register_file(
    file_metadata: FileMetadata,
    session: Session = Depends(get_session)
):
    """
    POST endpoint: Register file metadata (NO FILE UPLOAD)
    
    The Pi does NOT receive the actual file. It only stores metadata about where
    the file exists on the network. When a user wants to download, the CLI will
    use SCP to retrieve it from the source device.
    
    If a file with the same absolute_path and device already exists, it will be
    updated (only latest version is kept).
    
    Parameters:
    - file_metadata: JSON body containing all file metadata
    
    Returns:
    - Success message with file ID
    """
    try:
        # Check if file already exists (same absolute_path + device)
        statement = select(FileRecord).where(
            FileRecord.absolute_path == file_metadata.absolute_path,
            FileRecord.device == file_metadata.device
        )
        existing_file = session.exec(statement).first()
        
        if existing_file:
            # Update existing record (keep only latest version)
            existing_file.file_name = file_metadata.file_name
            existing_file.device_ip = file_metadata.device_ip
            existing_file.device_user = file_metadata.device_user
            existing_file.last_modified_time = file_metadata.last_modified_time
            existing_file.size = file_metadata.size
            existing_file.file_type = file_metadata.file_type
            existing_file.created_time = datetime.utcnow()  # Update timestamp
            
            session.add(existing_file)
            session.commit()
            session.refresh(existing_file)
            
            return {
                "message": "File metadata updated successfully",
                "file_id": existing_file.id,
                "file_name": existing_file.file_name,
                "action": "updated"
            }
        else:
            # Create new record
            file_record = FileRecord(
                file_name=file_metadata.file_name,
                absolute_path=file_metadata.absolute_path,
                device=file_metadata.device,
                device_ip=file_metadata.device_ip,
                device_user=file_metadata.device_user,
                last_modified_time=file_metadata.last_modified_time,
                size=file_metadata.size,
                file_type=file_metadata.file_type
            )
            
            session.add(file_record)
            session.commit()
            session.refresh(file_record)
            
            return {
                "message": "File metadata registered successfully",
                "file_id": file_record.id,
                "file_name": file_record.file_name,
                "action": "created"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering file metadata: {str(e)}")


@app.delete("/files/{file_id}")
def delete_file_metadata(file_id: int, session: Session = Depends(get_session)):
    """
    DELETE endpoint: Delete file metadata record
    
    This only removes the metadata from the Pi's database.
    The actual file remains on the source device.
    
    Parameters:
    - file_id: The database ID of the file metadata to delete
    
    Returns:
    - Success message
    """
    statement = select(FileRecord).where(FileRecord.id == file_id)
    file_record = session.exec(statement).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
    
    # Delete only the database record (no actual file to delete on Pi)
    session.delete(file_record)
    session.commit()
    
    return {
        "message": "File metadata deleted successfully",
        "file_id": file_id,
        "file_name": file_record.file_name,
        "device": file_record.device
    }
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, create_engine, Session
from models import FileEntry

DATABASE_URL = "sqlite:///./file_entries.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SQLModel.metadata.create_all(engine)

app = FastAPI()


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/files")
def get_files():
    pass


@app.post("/files")
def create_file(file_entry: FileEntry, session: Session = Depends(get_session)):
    session.add(file_entry)
    session.commit()
    session.refresh(file_entry)
    return file_entry


@app.put("/files/{file_id}")
def update_file(file_id: int, file_entry: FileEntry, session: Session = Depends(get_session)):
    db_entry = session.get(FileEntry, file_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="File entry not found")
    
    db_entry.file_name = file_entry.file_name
    db_entry.device = file_entry.device
    db_entry.last_modified = file_entry.last_modified
    db_entry.creation_time = file_entry.creation_time
    db_entry.size = file_entry.size
    db_entry.file_type = file_entry.file_type
    
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry


@app.delete("/files/{file_id}")
def delete_file(file_id: int, session: Session = Depends(get_session)):
    file_entry = session.get(FileEntry, file_id)
    if not file_entry:
        raise HTTPException(status_code=404, detail="File entry not found")
    
    session.delete(file_entry)
    session.commit()
    return {"message": "File entry deleted"}
