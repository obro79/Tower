# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-10-19

### Added

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
- Updated `main.py` imports to include logging dependencies
- Added `Request` import from FastAPI
- Added middleware imports from Starlette

### Files Modified
- `main.py` - Added logging middleware and endpoint logging
- Created `logging_config.py` - New logging configuration module
- Created `CHANGELOG.md` - This file

### Dependencies
No new external dependencies required. Uses Python standard library:
- `logging`
- `logging.handlers.RotatingFileHandler`
- `json`
- `datetime`
- `pathlib`
