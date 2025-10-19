# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-10-19

### Added

#### RAG (Retrieval-Augmented Generation) Search Integration
- **New models** in `models.py`:
  - `EmbeddingRequest`: Request model for registering file embeddings from clients
  - `SemanticSearchRequest`: Request model for semantic search queries with embedding vectors
  - `SemanticSearchResult`: Response model including file metadata and similarity scores

- **New endpoint**: `POST /files/register-embedding`
  - Accepts file embeddings generated on the client side
  - Stores embeddings in FAISS vector database for similarity search
  - Parameters:
    - `file_id`: ID of the file to associate embedding with
    - `embedding`: 384-dimensional float array (from all-MiniLM-L6-v2 model)
  - Validates embedding dimensions (must be 384)
  - Returns success/failure status
  - **Important**: Embeddings are generated CLIENT-SIDE since backend doesn't have access to file content

- **New endpoint**: `POST /files/semantic-search`
  - Semantic search using vector similarity (cosine distance via FAISS)
  - Accepts query embedding from client (generated from natural language query)
  - Parameters:
    - `query_embedding`: 384-dimensional float array
    - `k`: Number of results to return (default: 5)
  - Returns ranked list of files with similarity scores
  - Similarity score calculated as: `1.0 / (1.0 + distance)`
  - **Client workflow**:
    1. User enters query: "research paper about AI"
    2. Client generates embedding from query text
    3. Client sends embedding to this endpoint
    4. Backend returns most similar files based on their content embeddings

- **Vector database initialization**:
  - Integrated `vector_db.py` and `embedding.py` modules into main application
  - Vector database initialized on server startup via `init_vector_db()`
  - FAISS index for efficient similarity search
  - SQLite backend for embedding storage
  - Automatic index persistence to disk

- **Embedding cleanup on file deletion**:
  - Modified `DELETE /files/{file_id}` to also remove embeddings from vector database
  - Ensures vector database stays in sync with file metadata

### Changed

- **Updated `vector_db.py`**:
  - Changed `EMBEDDING_DIMENSION` from 768 to 384 to match all-MiniLM-L6-v2 model
  - This model is lightweight and runs efficiently on client devices

- **Updated `main.py`**:
  - Added vector database imports and initialization
  - Global `vector_db` instance for RAG operations
  - Enhanced startup sequence to initialize vector database
  - Integrated embedding deletion in file deletion endpoint

### Technical Architecture

#### Client-Side Embedding Generation
The embedding generation happens **entirely on the client side** because:
1. Backend doesn't have access to file content (only metadata)
2. Files may be large or contain sensitive data
3. Distributes computational load to client devices
4. Client has direct access to file content

**Recommended client-side flow**:
```
1. User runs: tower watch <file>
2. Client reads file content
3. Client generates embedding using Transformers.js (all-MiniLM-L6-v2)
4. Client sends metadata to POST /files/register
5. Client sends embedding to POST /files/register-embedding
```

**Recommended semantic search flow**:
```
1. User runs: tower get "research paper about AI"
2. Client detects natural language query
3. Client generates embedding from query text
4. Client sends embedding to POST /files/semantic-search
5. Backend returns ranked file results
6. Client displays results to user
```

#### Vector Database Stack
- **FAISS**: Fast similarity search library by Facebook AI
- **SQLite**: Persistent storage for embeddings
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
  - Sentence transformer model
  - Runs locally without API keys
  - Efficient for embedding generation
  - Good balance of speed and accuracy

#### Embedding Storage Format
- Stored as pickled numpy arrays in SQLite BLOB field
- Indexed by file_id for fast lookups
- FAISS index rebuilt on server startup from SQLite data
- Automatic synchronization between SQLite and FAISS

### Dependencies
Vector search requires the following Python packages (already in requirements.txt):
- `numpy>=1.24.2`
- `sentence-transformers>=2.2.0` (for backend embedding utilities)
- `faiss-cpu>=1.7.4` (vector similarity search)

**Note**: The backend embedding utilities in `embedding.py` are available for testing but NOT used in production since embeddings are generated client-side.

### Files Modified
- `models.py` - Added embedding request/response models
- `main.py` - Added RAG endpoints and vector DB initialization
- `vector_db.py` - Updated embedding dimension to 384
- `CHANGELOG.md` - This file

### Next Steps for Tower CLI Integration
To complete the RAG integration, the Tower CLI needs:

1. **Install embedding library**:
   ```bash
   npm install @xenova/transformers
   ```

2. **Create `src/utils/embedding.ts`**:
   - Generate embeddings from file content
   - Generate embeddings from query text
   - Use model: `Xenova/all-MiniLM-L6-v2`

3. **Update `src/utils/api-client.ts`**:
   - Add `registerEmbedding(fileId: number, embedding: number[])`
   - Add `semanticSearch(queryEmbedding: number[], k: number)`

4. **Update `src/daemon/sync-daemon.ts`**:
   - After registering file, generate and send embedding

5. **Update `src/commands/get.ts`**:
   - When natural language query detected, use semantic search

### Added (continued from above)

#### Client IP Detection Endpoint
- **New endpoint**: `GET /client-info`
  - Returns client's IP address as seen by the backend
  - More reliable than client-side IP detection (avoids loopback/IPv6 issues)
  - Called by `tower init` to auto-detect network-facing IP
  - Response includes:
    - `ip`: Client's IP from backend's perspective
    - `hostname`: Reserved for future use
  - Solves issue where Linux clients detected `127.0.1.1` instead of real IP
  - Solves issue where Windows clients detected IPv6 instead of IPv4

#### Windows Path Support
- **New function**: `format_scp_path()` in `main.py`
  - Converts Windows backslashes to forward slashes for SCP compatibility
  - Transforms Windows drive letters (C:) to Cygwin format (/C/)
  - Applied to both source and destination paths in file transfers
  - Fixes SCP errors with Windows paths like `C:\Users\...`
  
### Fixed

#### Path Conversion Bug
- **Issue**: `format_scp_path()` was creating double slashes (`/C//Users/...`)
- **Cause**: Only skipped `C:` but not the trailing `/` after conversion
- **Solution**: Use `.lstrip('/')` to remove all leading slashes after drive letter
- **Before**: `C:\Users\file.txt` → `/C//Users/file.txt` ❌
- **After**: `C:\Users\file.txt` → `/C/Users/file.txt` ✅

#### SSH Key Management System
- **New file**: `ssh_key_manager.py` - Automated SSH key management
  - Automatically generates SSH keypair on backend startup if not present
  - Uses ed25519 algorithm (modern, secure, fast)
  - Key stored at `~/.ssh/tower_backend_key` (private) and `~/.ssh/tower_backend_key.pub` (public)
  - No passphrase for automated SCP operations
  - Proper file permissions (600 for private, 644 for public)
  - Singleton pattern with global instance

- **New endpoint**: `GET /ssh/public-key`
  - Returns backend's SSH public key for client authorization
  - Response includes:
    - `public_key`: Full SSH public key string
    - `key_type`: Algorithm (e.g., 'ssh-ed25519')
    - `comment`: Key comment ('tower_backend_auto_generated')
    - `fingerprint`: Key fingerprint for verification
  - Called by `tower init` to enable passwordless SCP access
  - Logged in request logs

- **Enhanced SCP operations**
  - All SCP commands now use the generated SSH private key (`-i` flag)
  - Added `StrictHostKeyChecking=no` for automatic host key acceptance
  - Applies to both source→backend and backend→destination transfers

#### Request Logging System
- **New file**: `logging_config.py` - Comprehensive logging configuration module
  - Rotating file handler for request logs (max 10MB per file, 5 backup files)
  - Logs stored in `logs/requests.log`
  - Structured JSON logging format for easy parsing
  - Separate functions for logging requests, responses, and errors
  - Console output alongside file logging for development

- **Middleware**: `RequestLoggingMiddleware` in `main.py`
  - Automatically logs all incoming HTTP requests
  - Captures request method, path, headers, query parameters, and body payloads
  - Records client IP addresses
  - Logs response status codes and request duration in milliseconds
  - Error tracking with exception details

#### Endpoint-Specific Logging
Enhanced all API endpoints with detailed logging:

- **GET /files/search**
  - Logs search queries
  - Tracks number of results found
  - Warns when no files match search criteria

- **GET /files/{file_id}**
  - Logs file download requests with destination details
  - Tracks SCP transfer operations (source → temp → destination)
  - Records successful transfers and SCP failures

- **POST /files/register**
  - Logs complete file metadata payloads
  - Tracks whether files are created new or updated
  - Records file IDs for created/updated records
  - Captures registration errors

- **DELETE /files/{file_id}**
  - Logs file deletion requests
  - Records deleted file names and source devices
  - Warns when attempting to delete non-existent files

### Technical Details

#### Log Format
All logs follow this JSON structure:
```json
{
  "timestamp": "2025-10-19T12:34:56.789",
  "method": "POST",
  "path": "/files/register",
  "client_ip": "192.168.1.100",
  "headers": {...},
  "query_params": {...},
  "body": {...}
}
```

#### Log Rotation
- Maximum log file size: 10MB
- Backup count: 5 files
- Automatic rotation when size limit reached
- Old logs are preserved as `requests.log.1`, `requests.log.2`, etc.

### Changed
- Updated `main.py` imports to include logging dependencies and SSH key manager
- Added `Request` import from FastAPI
- Added middleware imports from Starlette
- Modified `on_startup()` to generate SSH keys on server startup
- Updated SCP commands in `GET /files/{file_id}` to use backend's SSH key

### Files Modified
- `main.py` - Added logging middleware, endpoint logging, SSH key startup, and new `/ssh/public-key` endpoint
- Created `logging_config.py` - New logging configuration module
- Created `ssh_key_manager.py` - SSH key generation and management
- Updated `CHANGELOG.md` - This file

### Dependencies
No new external dependencies required. Uses Python standard library:
- `logging`
- `logging.handlers.RotatingFileHandler`
- `json`
- `datetime`
- `pathlib`
