# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-10-19

### Added

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
