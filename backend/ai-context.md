# Project Context

## Setup Instructions

### Virtual Environment
This project uses a Python virtual environment located in `.venv`.

To activate:
```bash
source .venv/bin/activate
```

### Dependencies
Install with:
```bash
pip install fastapi uvicorn sqlmodel
```

Installed packages:
- **FastAPI**: Web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **SQLModel**: ORM combining SQLAlchemy and Pydantic

### Database
- SQLite database stored as `file_entries.db`
- Database is automatically created on first run
- Table: `fileentry` (auto-created from FileEntry model)

## Project Structure

### `models.py`
Defines the SQLModel for file entries:
- `id`: Primary key (auto-generated)
- `file_name`: Name of the file (indexed)
- `device`: Device identifier
- `last_modified`: Last modification timestamp
- `creation_time`: File creation timestamp
- `size`: File size in bytes
- `file_type`: Type of file

### `main.py`
FastAPI application with endpoints:
- `GET /files`: Stub endpoint (not implemented)
- `POST /files`: Create new file entry
- `DELETE /files/{file_id}`: Delete file entry by ID

## Running the Server

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

Server will run at `http://localhost:8000`
API docs available at `http://localhost:8000/docs`

## Development Notes
- The `types.py` was renamed to `models.py` to avoid circular import with Python's built-in `types` module
- GET endpoint is stubbed and needs implementation
