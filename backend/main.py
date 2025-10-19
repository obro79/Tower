from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, or_
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

import subprocess
import tempfile
import shutil

from models import FileRecord, FileSearchResponse
from database import create_db_and_tables, get_session

app = FastAPI(title="File Sync API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/files/{file_id}")
def get_file_metadata(file_id: int, device_ip: str = Query(..., description="IP of the device to download to"), destination_path: str = Query(..., description="Path on the device to download the file to"), device_user: str = Query(..., description="User on the destination device"), session: Session = Depends(get_session)):
    """
    Download a file by its ID to the specified device and path
    
    This performs SCP transfer from the source device to a temp folder, then to the destination.
    
    Parameters:
    - file_id: The database ID of the file
    - device_ip: IP of the destination device
    - destination_path: Path on the destination device to download to
    - device_user: User on the destination device
    
    Returns:
    - Success message
    """
    statement = select(FileRecord).where(FileRecord.id == file_id)
    file_record = session.exec(statement).first()

    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")

    # Create temp directory
    temp_dir = tempfile.mkdtemp()

    try:
        # SCP from source to temp
        source = f"{file_record.device_user}@{file_record.device_ip}:{file_record.absolute_path}"
        temp_file = f"{temp_dir}/{file_record.file_name}"
        subprocess.run(['scp', source, temp_file], check=True)

        # SCP from temp to destination
        dest = f"{device_user}@{device_ip}:{destination_path}"
        subprocess.run(['scp', temp_file, dest], check=True)

        return {"message": f"File {file_record.file_name} downloaded successfully to {dest}"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"SCP failed: {str(e)}")
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)


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
