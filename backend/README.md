# File Sync Backend API

FastAPI backend server for syncing files across devices on a local network.

**IMPORTANT**: This server does NOT store actual files. It only maintains a metadata registry of files and their locations across devices. Files are retrieved on-demand via SCP from source devices.

## Architecture

1. Devices register file metadata with the Pi (POST /files/register)
2. Pi stores metadata in SQLite database (file location, device IP, etc.)
3. Users search for files (GET /files/search)
4. CLI retrieves files via SCP directly from source devices
5. Only latest version of each file is kept in the registry

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /files/search
Fuzzy search for files by name with wildcard support

**Query Parameters:**
- `query` (required): Search term with optional * wildcard
  - Examples: `*.txt`, `report*`, `*2024*`, `document.pdf`

**Response:** List of file metadata records

**Example:**
```bash
# Search for all PDF files
curl "http://localhost:8000/files/search?query=*.pdf"

# Search for files containing "report"
curl "http://localhost:8000/files/search?query=*report*"
```

### GET /files/{file_id}
Get metadata for a specific file (for SCP retrieval)

**Response:** Full file metadata including device IP and absolute path

**Example:**
```bash
curl "http://localhost:8000/files/1"
```

### POST /files/register
Register file metadata (NO FILE UPLOAD - metadata only!)

**Request Body (JSON):**
```json
{
  "file_name": "document.pdf",
  "absolute_path": "/home/user/documents/document.pdf",
  "device": "laptop1",
  "device_ip": "192.168.1.100",
  "device_user": "username",
  "last_modified_time": "2025-10-18T10:30:00",
  "size": 1024000,
  "file_type": ".pdf"
}
```

**Behavior:**
- If file already exists (same path + device), it updates the record
- Only latest version is kept

**Example:**
```bash
curl -X POST "http://localhost:8000/files/register" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "test.txt",
    "absolute_path": "/home/user/test.txt",
    "device": "laptop1",
    "device_ip": "192.168.1.100",
    "device_user": "user",
    "last_modified_time": "2025-10-18T10:30:00",
    "size": 1024,
    "file_type": ".txt"
  }'
```

### DELETE /files/{file_id}
Delete file metadata record (doesn't delete actual file on source device)

**Example:**
```bash
curl -X DELETE "http://localhost:8000/files/1"
```

## Database Schema

**FileRecord Table:**
- `id`: Primary key (auto-generated, unique)
- `file_name`: Original file name (for display/search)
- `absolute_path`: Full path on source device
- `device`: Device hostname/name
- `device_ip`: IP address for SCP connection
- `device_user`: SSH username for SCP
- `last_modified_time`: Last modification time
- `created_time`: When record was created/updated in DB
- `size`: File size in bytes
- `file_type`: File extension

## File Retrieval Flow

1. Client searches: `GET /files/search?query=*.txt`
2. Server returns metadata list (IDs, names, devices, sizes, etc.)
3. CLI displays options to user
4. User selects file by ID
5. Client gets full metadata: `GET /files/{file_id}`
6. CLI executes SCP command using device_ip, device_user, and absolute_path
7. File is transferred directly from source device to client

**Example SCP command:**
```bash
scp user@192.168.1.100:/home/user/documents/file.txt ./downloads/
```
