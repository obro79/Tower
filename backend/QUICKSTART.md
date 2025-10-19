# Quick Start Guide - Running the Backend Server

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Setup Instructions

### Step 1: Install Dependencies
Open PowerShell in the `backend` folder and run:

```powershell
# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start the FastAPI Server
```powershell
# Make sure you're in the backend folder
cd backend

# Start the server (accessible from other computers on your network)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Important flags:**
- `--host 0.0.0.0` - Makes server accessible from other computers (not just localhost)
- `--port 8000` - Server runs on port 8000
- `--reload` - Auto-reloads on code changes (remove for production)

### Step 3: Find Your IP Address
Other computers need your IP address to connect. Run:

```powershell
# Get your local IP address
ipconfig
```

Look for "IPv4 Address" under your active network adapter (usually starts with 192.168.x.x or 10.x.x.x)

### Step 4: Test the Server

**On your computer (the server):**
```powershell
# Test health check
curl http://localhost:8000
```

**From another computer on the same network:**
```bash
# Replace <YOUR_IP> with your actual IP address
curl http://<YOUR_IP>:8000
```

## API Endpoints

### Base URL
- **Local**: `http://localhost:8000`
- **Network**: `http://<YOUR_IP>:8000` (e.g., `http://192.168.1.100:8000`)

### Available Endpoints

1. **Health Check**
   ```bash
   GET /
   ```

2. **Register File Metadata**
   ```bash
   POST /files/register
   ```

3. **Search Files**
   ```bash
   GET /files/search?query=*.txt
   ```

4. **Get File by ID**
   ```bash
   GET /files/{file_id}
   ```

5. **Delete File Metadata**
   ```bash
   DELETE /files/{file_id}
   ```

## Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs` (on server) or `http://<YOUR_IP>:8000/docs` (from other computers)
- **ReDoc**: `http://localhost:8000/redoc`

You can test all endpoints directly from the browser!

## Database

- **Location**: `backend/file_records.db`
- **Type**: SQLite
- **Auto-created**: Database is automatically created when you start the server

## Firewall Configuration

If other computers can't connect, you may need to allow the port through Windows Firewall:

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "File Sync API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, change the port:
```powershell
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Can't Connect from Other Computer
1. Check your IP address with `ipconfig`
2. Make sure both computers are on the same network
3. Check Windows Firewall settings
4. Verify the server is running with `--host 0.0.0.0`

### Import Errors
Make sure you're in the `backend` directory and virtual environment is activated.

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.
