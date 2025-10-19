from fastapi import FastAPI, Depends, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, or_
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from difflib import SequenceMatcher
import time
import json

import subprocess
import tempfile
import shutil

from models import FileRecord, FileSearchResponse
from database import create_db_and_tables, get_session
from logging_config import log_request_details, log_response_details, log_error_details, request_logger
from ssh_key_manager import ssh_key_manager

app = FastAPI(title="File Sync API", version="1.0.0")

def format_scp_path(path: str) -> str:
    """
    Format a file path for SCP compatibility.
    Converts Windows paths (C:\...) to Cygwin format (/C/...).
    """
    path = path.replace('\\', '/')
    
    if len(path) >= 2 and path[1] == ':':
        drive_letter = path[0].upper()
        rest = path[2:].lstrip('/')
        path = f"/{drive_letter}/{rest}"
    
    return path

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = str(request.url.path)
        query_params = dict(request.query_params)
        headers = dict(request.headers)
        
        body = None
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = json.loads(body_bytes.decode())
                    
                    async def receive():
                        return {"type": "http.request", "body": body_bytes}
                    
                    request._receive = receive
            except Exception as e:
                request_logger.warning(f"Could not parse request body: {e}")
        
        log_request_details(
            method=method,
            path=path,
            client_ip=client_ip,
            headers=headers,
            query_params=query_params,
            body=body
        )
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            log_response_details(
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error_details(
                method=method,
                path=path,
                error=str(e)
            )
            raise

app.add_middleware(RequestLoggingMiddleware)

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
    Initialize database and SSH keys on startup
    """
    create_db_and_tables()
    
    try:
        private_key, public_key = ssh_key_manager.generate_keypair()
        request_logger.info(f"SSH backend key ready: {private_key}")
        request_logger.info(f"Public key: {public_key[:50]}...")
    except Exception as e:
        request_logger.error(f"Failed to generate SSH keys: {e}")
        raise


@app.get("/")
def read_root():
    """
    Health check endpoint
    """
    return {"status": "File Sync API is running"}


@app.get("/client-info")
def get_client_info(request: Request):
    """
    GET endpoint: Return client's IP address as seen by the backend
    
    Clients call this during 'tower init' to discover their network-facing IP address.
    This is more reliable than client-side detection (which can return loopback/IPv6).
    
    Returns:
    - ip: Client's IP address from backend's perspective
    - hostname: Client's hostname if available
    """
    client_ip = request.client.host if request.client else "unknown"
    
    request_logger.info(f"ENDPOINT /client-info | Client IP: {client_ip}")
    
    return {
        "ip": client_ip,
        "hostname": None
    }


@app.get("/ssh/public-key")
def get_ssh_public_key():
    """
    GET endpoint: Retrieve backend's SSH public key
    
    Clients call this during 'tower init' to get the public key
    and add it to their ~/.ssh/authorized_keys for passwordless SCP.
    
    Returns:
    - public_key: SSH public key string
    - key_type: Key algorithm (e.g., 'ssh-ed25519')
    - comment: Key comment
    - fingerprint: Key fingerprint for verification
    """
    request_logger.info("ENDPOINT /ssh/public-key | Public key requested")
    
    try:
        public_key = ssh_key_manager.get_public_key()
        
        parts = public_key.split()
        key_type = parts[0] if len(parts) > 0 else "unknown"
        key_data = parts[1] if len(parts) > 1 else ""
        comment = parts[2] if len(parts) > 2 else "tower_backend"
        
        result = subprocess.run(
            ['ssh-keygen', '-lf', str(ssh_key_manager.public_key_path)],
            capture_output=True,
            text=True,
            check=True
        )
        fingerprint = result.stdout.strip().split()[1] if result.stdout else "unknown"
        
        response = {
            "public_key": public_key,
            "key_type": key_type,
            "comment": comment,
            "fingerprint": fingerprint
        }
        
        request_logger.info(f"ENDPOINT /ssh/public-key | Returned key with fingerprint: {fingerprint}")
        return response
        
    except Exception as e:
        request_logger.error(f"ENDPOINT /ssh/public-key | Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SSH public key: {str(e)}")


@app.get("/files/search", response_model=List[FileSearchResponse])
def search_files(
    query: str = Query(..., description="Search query for file name (supports * wildcard)"),
    fuzzy: bool = Query(False, description="Enable fuzzy search (typo tolerance, case-insensitive)"),
    session: Session = Depends(get_session)
):
    """
    GET endpoint: Fuzzy search for files by name with wildcard support

    Returns ONLY metadata - no actual files are stored on the Pi.
    Files will be retrieved via SCP from source devices when user confirms download.

    Parameters:
    - query: The search term (supports * wildcard for fuzzy matching)
             Examples: "*.txt", "report*", "*2024*", "document.pdf"
    - fuzzy: Enable fuzzy matching (case-insensitive, typo-tolerant)

    Returns:
    - List of matching file metadata records
    """
    request_logger.info(f"ENDPOINT /files/search | query: {query}, fuzzy: {fuzzy}")

    if fuzzy:
        # Fuzzy search: fetch all files and use similarity matching
        statement = select(FileRecord)
        all_files = session.exec(statement).all()

        query_lower = query.lower().replace("*", "")

        # Calculate similarity scores
        scored_results = []
        for file in all_files:
            filename_lower = file.file_name.lower()
            similarity = SequenceMatcher(None, query_lower, filename_lower).ratio()

            # Include if similarity > 0.4 (40% match)
            if similarity > 0.4:
                scored_results.append((similarity, file))

        # Sort by similarity score (highest first)
        scored_results.sort(reverse=True, key=lambda x: x[0])
        results = [file for score, file in scored_results]

    else:
        # Standard wildcard search
        like_pattern = query.replace("*", "%")
        statement = select(FileRecord).where(FileRecord.file_name.like(f"%{like_pattern}%"))
        results = session.exec(statement).all()

    if not results:
        request_logger.warning(f"ENDPOINT /files/search | No files found for query: {query}")
        raise HTTPException(status_code=404, detail=f"No files found matching '{query}'")

    request_logger.info(f"ENDPOINT /files/search | Found {len(results)} files for query: {query}")
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
    request_logger.info(f"ENDPOINT /files/{file_id} | file_id: {file_id}, device_ip: {device_ip}, destination_path: {destination_path}, device_user: {device_user}")
    
    statement = select(FileRecord).where(FileRecord.id == file_id)
    file_record = session.exec(statement).first()

    if not file_record:
        request_logger.warning(f"ENDPOINT /files/{file_id} | File not found: {file_id}")
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")

    temp_dir = tempfile.mkdtemp()

    try:
        ssh_key = ssh_key_manager.get_private_key_path()
        
        source_path = format_scp_path(file_record.absolute_path)
        source = f"{file_record.device_user}@{file_record.device_ip}:{source_path}"
        temp_file = f"{temp_dir}/{file_record.file_name}"
        
        request_logger.info(f"ENDPOINT /files/{file_id} | SCP from source: {source} to temp: {temp_file}")
        subprocess.run(['scp', '-i', ssh_key, '-o', 'StrictHostKeyChecking=no', source, temp_file], check=True)

        dest_path = format_scp_path(destination_path)
        dest = f"{device_user}@{device_ip}:{dest_path}"
        request_logger.info(f"ENDPOINT /files/{file_id} | SCP from temp to destination: {dest}")
        subprocess.run(['scp', '-i', ssh_key, '-o', 'StrictHostKeyChecking=no', temp_file, dest], check=True)

        request_logger.info(f"ENDPOINT /files/{file_id} | Successfully transferred file: {file_record.file_name}")
        return {"message": f"File {file_record.file_name} downloaded successfully to {dest}"}

    except subprocess.CalledProcessError as e:
        request_logger.error(f"ENDPOINT /files/{file_id} | SCP failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SCP failed: {str(e)}")
    finally:
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
    request_logger.info(f"ENDPOINT /files/register | Payload: {file_metadata.dict()}")
    
    try:
        statement = select(FileRecord).where(
            FileRecord.absolute_path == file_metadata.absolute_path,
            FileRecord.device == file_metadata.device
        )
        existing_file = session.exec(statement).first()
        
        if existing_file:
            request_logger.info(f"ENDPOINT /files/register | Updating existing file: {existing_file.id}")
            
            existing_file.file_name = file_metadata.file_name
            existing_file.device_ip = file_metadata.device_ip
            existing_file.device_user = file_metadata.device_user
            existing_file.last_modified_time = file_metadata.last_modified_time
            existing_file.size = file_metadata.size
            existing_file.file_type = file_metadata.file_type
            existing_file.created_time = datetime.utcnow()
            
            session.add(existing_file)
            session.commit()
            session.refresh(existing_file)
            
            request_logger.info(f"ENDPOINT /files/register | Updated file ID: {existing_file.id}")
            
            return {
                "message": "File metadata updated successfully",
                "file_id": existing_file.id,
                "file_name": existing_file.file_name,
                "action": "updated"
            }
        else:
            request_logger.info(f"ENDPOINT /files/register | Creating new file record")
            
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
            
            request_logger.info(f"ENDPOINT /files/register | Created new file ID: {file_record.id}")
            
            return {
                "message": "File metadata registered successfully",
                "file_id": file_record.id,
                "file_name": file_record.file_name,
                "action": "created"
            }
    
    except Exception as e:
        request_logger.error(f"ENDPOINT /files/register | Error: {str(e)}")
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
    request_logger.info(f"ENDPOINT /files/{file_id} DELETE | file_id: {file_id}")
    
    statement = select(FileRecord).where(FileRecord.id == file_id)
    file_record = session.exec(statement).first()
    
    if not file_record:
        request_logger.warning(f"ENDPOINT /files/{file_id} DELETE | File not found: {file_id}")
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
    
    session.delete(file_record)
    session.commit()
    
    request_logger.info(f"ENDPOINT /files/{file_id} DELETE | Deleted file: {file_record.file_name} from device: {file_record.device}")
    
    return {
        "message": "File metadata deleted successfully",
        "file_id": file_id,
        "file_name": file_record.file_name,
        "device": file_record.device
    }
