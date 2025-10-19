from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timezone
from pydantic import BaseModel
from contextlib import asynccontextmanager

from models import File
from database import init_db, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize database on startup
    """
    init_db()
    yield


app = FastAPI(title="File Sync API", version="1.0.0", lifespan=lifespan)


@app.get("/")
def read_root():
    """
    Health check endpoint
    """
    return {"status": "File Sync API is running"}


@app.get("/files/search", response_model=List[File])
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
    like_pattern = query.replace("*", "%")
    statement = select(File).where(File.filename.ilike(f"%{like_pattern}%"))
    results = session.exec(statement).all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No files found matching '{query}'")
    
    return results


@app.get("/files/{file_id}", response_model=File)
def get_file_metadata(file_id: int, session: Session = Depends(get_session)):
    """
    Get metadata for a specific file by its ID
    
    This returns the file location info so the CLI can initiate SCP transfer.
    
    Parameters:
    - file_id: The database ID of the file
    
    Returns:
    - File metadata including device and path for SCP retrieval
    """
    statement = select(File).where(File.id == file_id)
    file_record = session.exec(statement).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
    
    return file_record


class FileMetadata(BaseModel):
    """Request body for registering file metadata"""
    filename: str
    path: str
    device: str
    alias: str
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
    
    If a file with the same path and device already exists, it will be
    updated (only latest version is kept).
    
    Parameters:
    - file_metadata: JSON body containing all file metadata
    
    Returns:
    - Success message with file ID
    """
    try:
        statement = select(File).where(
            File.path == file_metadata.path,
            File.device == file_metadata.device
        )
        existing_file = session.exec(statement).first()
        
        if existing_file:
            existing_file.filename = file_metadata.filename
            existing_file.alias = file_metadata.alias
            existing_file.size = file_metadata.size
            existing_file.file_type = file_metadata.file_type
            existing_file.modified_at = datetime.now(timezone.utc)
            
            session.add(existing_file)
            session.commit()
            session.refresh(existing_file)
            
            return {
                "message": "File metadata updated successfully",
                "file_id": existing_file.id,
                "filename": existing_file.filename,
                "action": "updated"
            }
        else:
            new_file = File(
                filename=file_metadata.filename,
                path=file_metadata.path,
                device=file_metadata.device,
                alias=file_metadata.alias,
                size=file_metadata.size,
                file_type=file_metadata.file_type
            )
            
            session.add(new_file)
            session.commit()
            session.refresh(new_file)
            
            return {
                "message": "File metadata registered successfully",
                "file_id": new_file.id,
                "filename": new_file.filename,
                "action": "created"
            }
    
    except Exception as e:
        session.rollback()
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
    statement = select(File).where(File.id == file_id)
    file_record = session.exec(statement).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
    
    session.delete(file_record)
    session.commit()
    
    return {
        "message": "File metadata deleted successfully",
        "file_id": file_id,
        "filename": file_record.filename,
        "device": file_record.device
    }
