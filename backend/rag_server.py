"""
RAG Server for distributed file transfer system.
Provides API endpoints for file upload, search, and retrieval using vector embeddings.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from embedding import generate_embedding
from vector_db import VectorDatabase, init_vector_db
from database import create_db_and_tables, get_session, engine
from models import FileRecord
from sqlmodel import Session, select
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="RAG File Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
vector_db: Optional[VectorDatabase] = None
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension (local model, no API key needed!)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    file_id: int
    filename: str
    path: str
    device: str
    alias: str
    size: int
    distance: float
    content_preview: Optional[str] = None

class UploadResponse(BaseModel):
    file_id: int
    filename: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize databases on startup."""
    global vector_db
    
    # Initialize file database
    create_db_and_tables()
    
    # Initialize vector database
    vector_db = init_vector_db(dimension=EMBEDDING_DIM)
    
    print("✓ RAG Server initialized successfully")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "RAG File Server",
        "version": "1.0.0"
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    device: str = Query(..., description="Device identifier"),
    device_ip: str = Query(..., description="Device IP address"),
    device_user: str = Query(..., description="Device SSH username"),
    absolute_path: str = Query(..., description="Absolute path on device")
):
    """
    Upload a file, generate embedding, and store in both databases.
    """
    tmp_path = None
    try:
        # Save uploaded file temporarily
        suffix = Path(file.filename or "file.txt").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Generate embedding from file content
        embedding = generate_embedding(tmp_path, is_file=True)
        
        # Store file metadata in database
        session = Session(engine)
        try:
            file_record = FileRecord(
                file_name=file.filename or "unknown",
                absolute_path=absolute_path,
                device=device,
                device_ip=device_ip,
                device_user=device_user,
                last_modified_time=datetime.utcnow(),
                size=len(content),
                file_type=suffix or ".txt"
            )
            session.add(file_record)
            session.commit()
            session.refresh(file_record)
            
            # Store embedding in vector database
            success = vector_db.insert(embedding, file_record.id)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to store embedding")
            
            return UploadResponse(
                file_id=file_record.id,
                filename=file.filename or "unknown",
                message="File uploaded and indexed successfully"
            )
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/search", response_model=List[SearchResult])
async def search_files(request: QueryRequest):
    """
    Search for similar files using semantic search.
    """
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(request.query, is_file=False)
        
        # Search vector database
        results = vector_db.get_file(query_embedding, k=request.top_k)
        
        # Retrieve file metadata
        search_results = []
        session = Session(engine)
        try:
            for file_id, distance in results:
                file_obj = session.get(FileRecord, file_id)
                if file_obj:
                    search_results.append(SearchResult(
                        file_id=file_obj.id or 0,
                        filename=file_obj.file_name,
                        path=file_obj.absolute_path,
                        device=file_obj.device,
                        alias=file_obj.device_user,
                        size=file_obj.size,
                        distance=distance,
                        content_preview=None
                    ))
            return search_results
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files", response_model=List[dict])
async def list_files():
    """
    List all files in the database.
    """
    try:
        session = Session(engine)
        try:
            files = session.exec(select(FileRecord)).all()
            return [
                {
                    "id": f.id,
                    "file_name": f.file_name,
                    "absolute_path": f.absolute_path,
                    "device": f.device,
                    "device_ip": f.device_ip,
                    "device_user": f.device_user,
                    "last_modified_time": f.last_modified_time.isoformat(),
                    "created_time": f.created_time.isoformat(),
                    "size": f.size,
                    "file_type": f.file_type
                }
                for f in files
            ]
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{file_id}")
async def get_file(file_id: int):
    """
    Get file metadata by ID.
    """
    session = Session(engine)
    try:
        file_obj = session.get(FileRecord, file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")
        return {
            "id": file_obj.id,
            "file_name": file_obj.file_name,
            "absolute_path": file_obj.absolute_path,
            "device": file_obj.device,
            "device_ip": file_obj.device_ip,
            "device_user": file_obj.device_user,
            "last_modified_time": file_obj.last_modified_time.isoformat(),
            "created_time": file_obj.created_time.isoformat(),
            "size": file_obj.size,
            "file_type": file_obj.file_type
        }
    finally:
        session.close()


@app.get("/stats")
async def get_stats():
    """
    Get statistics about the RAG system.
    """
    try:
        vector_stats = vector_db.get_stats()
        session = Session(engine)
        try:
            files = session.exec(select(FileRecord)).all()
            total_files = len(files)
        finally:
            session.close()
        
        return {
            "total_files": total_files,
            "total_vectors": vector_stats['total_vectors'],
            "vector_dimension": vector_stats['dimension'],
            "index_type": vector_stats['index_type']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
