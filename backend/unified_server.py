"""
Unified File Sync & RAG Server
Combines file metadata management with semantic search using vector embeddings.
Implements Colinear Query Expansion for improved search results.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select, or_
from typing import List, Optional
from contextlib import asynccontextmanager
import os
import tempfile
from pathlib import Path
from datetime import datetime
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from embedding import generate_embedding
from vector_db import VectorDatabase, init_vector_db
from database import create_db_and_tables, get_session, engine
from models import FileRecord, FileSearchResponse

# Global instances
vector_db: Optional[VectorDatabase] = None
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension (local model, no API key needed!)


# ==================== Lifespan Context Manager ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event decorators.
    """
    global vector_db
    
    # Startup
    print("🚀 Starting Unified File Sync & RAG Server...")
    create_db_and_tables()
    vector_db = init_vector_db(dimension=EMBEDDING_DIM)
    print("✓ Unified File Sync & RAG Server initialized successfully")
    
    yield  # Server runs here
    
    # Shutdown
    print("🛑 Shutting down server...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Unified File Sync & RAG Server",
    version="2.0.0",
    description="File metadata management with semantic search and query expansion",
    lifespan=lifespan
)

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

# ==================== Request/Response Models ====================

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


class QueryRequest(BaseModel):
    """Semantic search query with query expansion support"""
    query: str
    top_k: int = 5
    use_query_expansion: bool = True  # Enable Colinear Query Expansion by default
    expansion_count: int = 3  # Number of expanded queries to generate


class SearchResult(BaseModel):
    """Enhanced search result with similarity score"""
    file_id: int
    filename: str
    path: str
    device: str
    device_ip: str
    device_user: str
    size: int
    file_type: str
    similarity_score: float  # 0-1, higher is better (converted from distance)
    last_modified_time: datetime
    matched_via: str  # "original_query" or "expanded_query_N"


class UploadResponse(BaseModel):
    file_id: int
    filename: str
    message: str
    action: str  # "created" or "updated"


# ==================== CORS Middleware ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Unified File Sync & RAG Server",
        "version": "2.0.0",
        "features": ["metadata_search", "semantic_search", "query_expansion"]
    }


# ==================== File Registration (Metadata Only) ====================

@app.post("/files/register", response_model=UploadResponse)
def register_file(
    file_metadata: FileMetadata,
    session: Session = Depends(get_session)
):
    """
    Register file metadata WITHOUT uploading the actual file.
    
    The Pi does NOT receive the actual file. It only stores metadata about where
    the file exists on the network. When a user wants to download, the CLI will
    use SCP to retrieve it from the source device.
    
    If a file with the same absolute_path and device already exists, it will be updated.
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
            existing_file.created_time = datetime.utcnow()
            
            session.add(existing_file)
            session.commit()
            session.refresh(existing_file)
            
            return UploadResponse(
                file_id=existing_file.id,
                filename=existing_file.file_name,
                message="File metadata updated successfully",
                action="updated"
            )
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
            
            return UploadResponse(
                file_id=file_record.id,
                filename=file_record.file_name,
                message="File metadata registered successfully",
                action="created"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering file metadata: {str(e)}")


# ==================== File Upload with Embedding (For RAG) ====================

@app.post("/files/upload", response_model=UploadResponse)
async def upload_file_with_embedding(
    file: UploadFile = File(...),
    device: str = Query(..., description="Device identifier"),
    device_ip: str = Query(..., description="Device IP address"),
    device_user: str = Query(..., description="Device SSH username"),
    absolute_path: str = Query(..., description="Absolute path on device")
):
    """
    Upload a file, generate embedding, and store in both databases.
    
    Use this endpoint when you want to enable semantic search on the file content.
    The file content is read to generate embeddings, then discarded.
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
            # Check if file already exists
            statement = select(FileRecord).where(
                FileRecord.absolute_path == absolute_path,
                FileRecord.device == device
            )
            existing_file = session.exec(statement).first()
            
            if existing_file:
                # Update existing record
                existing_file.file_name = file.filename or "unknown"
                existing_file.device_ip = device_ip
                existing_file.device_user = device_user
                existing_file.last_modified_time = datetime.utcnow()
                existing_file.size = len(content)
                existing_file.file_type = suffix or ".txt"
                existing_file.created_time = datetime.utcnow()
                
                session.add(existing_file)
                session.commit()
                session.refresh(existing_file)
                
                # Update embedding in vector database
                vector_db.delete_embedding(existing_file.id)
                vector_db.insert(embedding, existing_file.id)
                
                return UploadResponse(
                    file_id=existing_file.id,
                    filename=file.filename or "unknown",
                    message="File uploaded and indexed successfully",
                    action="updated"
                )
            else:
                # Create new record
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
                    message="File uploaded and indexed successfully",
                    action="created"
                )
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ==================== Colinear Query Expansion ====================

def colinear_query_expansion(
    original_query: str,
    expansion_count: int = 3
) -> List[str]:
    """
    Generate expanded queries using colinear query expansion technique.
    
    This creates related queries by:
    1. Adding synonyms and related terms
    2. Reformulating the query in different ways
    3. Adding context-specific expansions
    
    Args:
        original_query: The original search query
        expansion_count: Number of expanded queries to generate
    
    Returns:
        List of expanded query strings (including original)
    """
    expanded_queries = [original_query]
    
    # Simple expansion strategies (can be enhanced with LLM in future)
    # Strategy 1: Add common document-related terms
    if expansion_count >= 1:
        expanded_queries.append(f"document about {original_query}")
    
    # Strategy 2: Add file content context
    if expansion_count >= 2:
        expanded_queries.append(f"file containing {original_query}")
    
    # Strategy 3: Add informational context
    if expansion_count >= 3:
        expanded_queries.append(f"information regarding {original_query}")
    
    # Strategy 4: Add data context
    if expansion_count >= 4:
        expanded_queries.append(f"data related to {original_query}")
    
    return expanded_queries[:expansion_count + 1]


# ==================== Semantic Search with Query Expansion ====================

@app.post("/search/semantic", response_model=List[SearchResult])
async def semantic_search(request: QueryRequest):
    """
    Semantic search using vector embeddings with Colinear Query Expansion.
    
    This endpoint:
    1. Takes your search query
    2. Optionally expands it into multiple related queries (Colinear Query Expansion)
    3. Generates embeddings for each query variant
    4. Searches the vector database
    5. Combines and ranks results by relevance
    
    Parameters:
    - query: Search query string
    - top_k: Maximum number of results to return
    - use_query_expansion: Enable/disable query expansion (default: True)
    - expansion_count: Number of query variants to generate (default: 3)
    """
    try:
        all_results = {}  # file_id -> (distance, matched_via)
        
        # Generate query variants
        if request.use_query_expansion:
            queries = colinear_query_expansion(request.query, request.expansion_count)
            print(f"🔍 Query Expansion: {len(queries)} variants generated")
            for i, q in enumerate(queries):
                print(f"  {i}: {q}")
        else:
            queries = [request.query]
        
        # Search with each query variant
        for idx, query_variant in enumerate(queries):
            # Generate embedding for this query variant
            query_embedding = generate_embedding(query_variant, is_file=False)
            
            # Search vector database
            results = vector_db.get_file(query_embedding, k=request.top_k)
            
            # Track which query matched which file
            matched_via = "original_query" if idx == 0 else f"expanded_query_{idx}"
            
            # Combine results (keep best distance for each file)
            for file_id, distance in results:
                if file_id not in all_results or distance < all_results[file_id][0]:
                    all_results[file_id] = (distance, matched_via)
        
        # Get top_k unique results sorted by distance
        sorted_results = sorted(all_results.items(), key=lambda x: x[1][0])[:request.top_k]
        
        # Retrieve file metadata and build response
        search_results = []
        session = Session(engine)
        try:
            for file_id, (distance, matched_via) in sorted_results:
                file_obj = session.get(FileRecord, file_id)
                if file_obj:
                    # Convert L2 distance to similarity score (0-1, higher is better)
                    # Using negative exponential: similarity = e^(-distance)
                    similarity_score = float(np.exp(-distance))
                    
                    search_results.append(SearchResult(
                        file_id=file_obj.id or 0,
                        filename=file_obj.file_name,
                        path=file_obj.absolute_path,
                        device=file_obj.device,
                        device_ip=file_obj.device_ip,
                        device_user=file_obj.device_user,
                        size=file_obj.size,
                        file_type=file_obj.file_type,
                        similarity_score=similarity_score,
                        last_modified_time=file_obj.last_modified_time,
                        matched_via=matched_via
                    ))
            
            print(f"✓ Found {len(search_results)} results")
            return search_results
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Keyword/Wildcard Search (Original from main.py) ====================

@app.get("/search/keyword", response_model=List[FileSearchResponse])
def keyword_search(
    query: str = Query(..., description="Search query for file name (supports * wildcard)"),
    session: Session = Depends(get_session)
):
    """
    Traditional keyword search for files by name with wildcard support.
    
    This is faster than semantic search but only matches filenames, not content.
    
    Parameters:
    - query: Search term (supports * wildcard for fuzzy matching)
             Examples: "*.txt", "report*", "*2024*", "document.pdf"
    
    Returns:
    - List of matching file metadata records
    """
    # Convert wildcard pattern to SQL LIKE pattern
    like_pattern = query.replace("*", "%")
    
    # Fuzzy search on file_name (case-insensitive)
    statement = select(FileRecord).where(FileRecord.file_name.like(f"%{like_pattern}%"))
    
    results = session.exec(statement).all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No files found matching '{query}'")
    
    return results


# ==================== File Management ====================

@app.get("/files", response_model=List[dict])
async def list_files(session: Session = Depends(get_session)):
    """List all files in the database."""
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{file_id}", response_model=FileSearchResponse)
async def get_file_metadata(file_id: int, session: Session = Depends(get_session)):
    """
    Get metadata for a specific file by its ID.
    
    Returns file location info so the CLI can initiate SCP transfer.
    """
    file_obj = session.get(FileRecord, file_id)
    
    if not file_obj:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
    
    return file_obj


@app.delete("/files/{file_id}")
def delete_file_metadata(file_id: int, session: Session = Depends(get_session)):
    """
    Delete file metadata record and its embedding.
    
    This only removes the metadata from the Pi's database.
    The actual file remains on the source device.
    """
    file_record = session.get(FileRecord, file_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
    
    # Delete embedding from vector database
    vector_db.delete_embedding(file_id)
    
    # Delete database record
    session.delete(file_record)
    session.commit()
    
    return {
        "message": "File metadata and embedding deleted successfully",
        "file_id": file_id,
        "file_name": file_record.file_name,
        "device": file_record.device
    }


# ==================== Statistics ====================

@app.get("/stats")
async def get_stats(session: Session = Depends(get_session)):
    """Get statistics about the system."""
    try:
        vector_stats = vector_db.get_stats()
        files = session.exec(select(FileRecord)).all()
        total_files = len(files)
        total_size = sum(f.size for f in files)
        
        return {
            "total_files": total_files,
            "total_vectors": vector_stats['total_vectors'],
            "total_size_bytes": total_size,
            "vector_dimension": vector_stats['dimension'],
            "index_type": vector_stats['index_type'],
            "embedding_model": "all-MiniLM-L6-v2 (local, no API key)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
