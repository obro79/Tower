# Tower Setup Guide

Tower is a cross-device file syncing system that uses a central registry (hosted on a Raspberry Pi or server) to track file metadata across devices on a local network. Files are retrieved on-demand via SCP, meaning the central server never stores the actual files.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Backend Setup (Raspberry Pi / Server)](#backend-setup-raspberry-pi--server)
- [CLI Setup (Client Devices)](#cli-setup-client-devices)
- [Network Configuration](#network-configuration)
- [First Use](#first-use)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

Tower works in three main steps:

1. **Registration**: Each device registers file metadata (name, path, size, etc.) with the central backend server
2. **Search**: Users search for files across all registered devices via the CLI
3. **Retrieval**: Files are downloaded directly from source devices using SCP (not from the central server)

**Important**: The backend server only stores metadata - it never receives or stores the actual files. This keeps the system lightweight and fast.

---

## Prerequisites

### For the Backend (Raspberry Pi / Server)

- Python 3.8 or higher
- pip (Python package manager)
- A Raspberry Pi or any Linux server on your local network
- Static IP address (recommended) or hostname

### For the CLI (Client Devices)

- Node.js 16 or higher
- npm (comes with Node.js)
- SSH access configured (for SCP file transfers)
- macOS, Linux, or Windows with WSL

---

## Backend Setup (Raspberry Pi / Server)

### 1. Clone the Repository

```bash
cd ~
git clone <repository-url>
cd dubhacks2/backend
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- FastAPI - Web framework
- SQLModel - Database ORM
- Uvicorn - ASGI server
- SQLAlchemy - Database toolkit

### 3. Configure the Server

The backend uses SQLite by default, which requires no configuration. The database file will be created automatically at `backend/file_sync.db` on first run.

### 4. Start the Backend Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Flags explained:**
- `--reload`: Auto-restart on code changes (remove for production)
- `--host 0.0.0.0`: Listen on all network interfaces
- `--port 8000`: Run on port 8000

### 5. Verify the Server is Running

From another device on the same network:

```bash
curl http://<raspberry-pi-ip>:8000/
```

You should see:
```json
{"status": "File Sync API is running"}
```

### 6. (Optional) Run as a System Service

To keep the backend running automatically on boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/tower-backend.service
```

Add:

```ini
[Unit]
Description=Tower File Sync Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/dubhacks2/backend
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable tower-backend
sudo systemctl start tower-backend
sudo systemctl status tower-backend
```

---

## CLI Setup (Client Devices)

### 1. Clone the Repository

```bash
cd ~
git clone <repository-url>
cd dubhacks2
```

### 2. Install Dependencies

```bash
cd tower_cli
npm install
```

### 3. Build the CLI

```bash
npm run build
```

This compiles the TypeScript code to JavaScript in the `dist/` folder.

### 4. Link the CLI Globally (Optional but Recommended)

This allows you to use `tower` from anywhere in your terminal:

```bash
npm link
```

Alternatively, you can run it directly:

```bash
node dist/index.js <command>
```

### 5. Configure the Backend URL

Create a `.env` file in the project root (not in `tower_cli/`):

```bash
cd /Users/<your-username>/WebstormProjects/dubhacks2  # or wherever you cloned it
nano .env
```

Add:

```bash
TOWER_BACKEND_URL="http://<raspberry-pi-ip>:8000"
```

Example:
```bash
TOWER_BACKEND_URL="http://192.168.1.100:8000"
```

**Important**: Use the IP address or hostname of your Raspberry Pi/server. Do not include a trailing slash.

### 6. Verify CLI Installation

```bash
tower --version
```

You should see:
```
0.1.0
```

---

## Network Configuration

### SSH Setup for SCP Transfers

Tower uses SCP to transfer files between devices. Each device needs SSH access to all other devices.

#### 1. Generate SSH Keys (if you don't have one)

On each client device:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Press Enter to accept defaults (no passphrase recommended for automation).

#### 2. Copy SSH Keys to Other Devices

From Device A to Device B:

```bash
ssh-copy-id username@device-b-ip
```

Example:
```bash
ssh-copy-id john@192.168.1.101
```

Repeat this for every device pair that needs to transfer files.

#### 3. Test SSH Connection

```bash
ssh username@device-ip
```

You should be able to log in without a password.

### Static IP Addresses (Recommended)

For reliability, assign static IPs to your devices:

1. Access your router's admin panel (usually `192.168.1.1` or `192.168.0.1`)
2. Find DHCP settings or "Address Reservation"
3. Assign fixed IPs based on MAC addresses

Alternatively, configure static IPs on each device (method varies by OS).

---

## First Use

### 1. Initialize Tower

Run the interactive setup wizard:

```bash
tower init
```

This will:
- Create the configuration directory (`~/.tower/`)
- Set up default settings
- Guide you through adding your first device

### 2. Add Files to Watch List

Add individual files:

```bash
tower watch add /path/to/document.pdf
```

Add directories recursively:

```bash
tower watch add /path/to/projects -r --exclude node_modules dist .git
```

Add with tags for organization:

```bash
tower watch add /path/to/work -r --tags work,important
```

### 3. Register Files with Backend

Files in your watch list need to be registered with the backend. This happens automatically during sync:

```bash
tower sync
```

Or register manually (implementation may vary based on current codebase).

### 4. Search and Download Files

Search for files across all devices:

```bash
tower search "*.pdf"
tower search "report"
```

Download a file by its ID:

```bash
tower download <file-id> -d ~/Downloads/
```

---

## Usage Examples

### Scenario 1: Syncing Project Files

```bash
# On Device A (work laptop)
tower watch add ~/Projects/myapp -r --exclude node_modules dist --tags work
tower sync

# On Device B (home desktop)
tower search "myapp"
tower download <file-id> -d ~/Projects/
```

### Scenario 2: Sharing Documents

```bash
# On Device A
tower watch add ~/Documents/reports -r --tags documents
tower sync

# On Device B
tower search "*.docx" --tags documents
tower download <file-id>
```

### Scenario 3: Viewing Sync Status

```bash
# Check what's being watched
tower watch list

# Check sync status
tower sync status

# View sync history
tower sync history

# Manage devices
tower devices list
```

### Scenario 4: Managing Configuration

```bash
# View all settings
tower config list

# Enable/disable auto-sync
tower config set autoSync true

# Set sync interval (in minutes)
tower config set syncInterval 10

# Reset to defaults
tower config reset
```

---

## Troubleshooting

### Backend Not Accessible

**Problem**: `curl http://<pi-ip>:8000` doesn't work

**Solutions**:
1. Verify the backend is running: `sudo systemctl status tower-backend` (if using systemd)
2. Check firewall rules:
   ```bash
   sudo ufw allow 8000/tcp
   ```
3. Verify you're on the same network as the Pi
4. Check the Pi's IP address: `hostname -I`

### CLI Can't Connect to Backend

**Problem**: CLI commands fail with connection errors

**Solutions**:
1. Check `.env` file has correct URL (no trailing slash)
2. Test backend manually: `curl http://<backend-url>/`
3. Ensure backend is running on port 8000

### SCP Transfer Fails

**Problem**: `tower download` fails with SSH/SCP errors

**Solutions**:
1. Test SSH manually: `ssh username@target-device-ip`
2. Ensure SSH keys are set up: `ssh-copy-id username@target-device-ip`
3. Verify the source device is powered on and connected
4. Check file permissions on source device

### File Not Found During Download

**Problem**: Backend returns file metadata but SCP fails

**Solutions**:
1. The file may have been moved/deleted on the source device
2. Verify the file still exists: SSH into source device and check path
3. Re-sync from source device: `tower sync --force`

### Watch List Not Persisting

**Problem**: `tower watch list` shows nothing after adding files

**Solutions**:
1. Check config directory exists: `ls -la ~/.tower/`
2. Verify permissions: `chmod -R 755 ~/.tower/`
3. Re-run `tower init` to recreate config

### Port 8000 Already in Use

**Problem**: Backend fails to start

**Solutions**:
1. Check what's using port 8000:
   ```bash
   sudo lsof -i :8000
   ```
2. Kill the process or change the port:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080
   ```
3. Update `.env` with new port

---

## API Reference (for Developers)

### Backend API Endpoints

#### `GET /files/search?query=<pattern>`
Search for files by name with wildcard support.

**Example**:
```bash
curl "http://192.168.1.100:8000/files/search?query=*.pdf"
```

#### `GET /files/{file_id}`
Get metadata for a specific file (includes SCP details).

**Example**:
```bash
curl "http://192.168.1.100:8000/files/123"
```

#### `POST /files/register`
Register file metadata with the backend.

**Example**:
```bash
curl -X POST "http://192.168.1.100:8000/files/register" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "document.pdf",
    "absolute_path": "/home/user/docs/document.pdf",
    "device": "laptop",
    "device_ip": "192.168.1.101",
    "device_user": "john",
    "last_modified_time": "2025-10-19T10:00:00",
    "size": 1024000,
    "file_type": ".pdf"
  }'
```

#### `DELETE /files/{file_id}`
Delete file metadata (doesn't delete actual file).

**Example**:
```bash
curl -X DELETE "http://192.168.1.100:8000/files/123"
```

---

## Configuration Files

### `~/.tower/config.json`

Default configuration:

```json
{
  "autoSync": true,
  "syncInterval": 5,
  "conflictResolution": "latest",
  "excludePatterns": ["node_modules", ".git", "*.log", ".DS_Store"],
  "devices": [],
  "watchList": []
}
```

### `.env` (Project Root)

```bash
TOWER_BACKEND_URL="http://192.168.1.100:8000"
```

---

## Development

### Running in Development Mode

#### Backend (with auto-reload):
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### CLI (with watch mode):
```bash
cd tower_cli
npm run dev
```

In another terminal:
```bash
node dist/index.js <command>
```

### Database Management

View the SQLite database:

```bash
cd backend
sqlite3 file_sync.db
```

Common queries:
```sql
-- View all registered files
SELECT * FROM filerecord;

-- Search for files
SELECT * FROM filerecord WHERE file_name LIKE '%report%';

-- Count files per device
SELECT device, COUNT(*) FROM filerecord GROUP BY device;

-- Clear all records
DELETE FROM filerecord;
```

---

## Security Considerations

1. **Local Network Only**: Tower is designed for local network use. Do not expose the backend to the internet without proper authentication.

2. **SSH Security**:
   - Use strong passwords or SSH keys
   - Consider SSH key passphrases for sensitive environments
   - Restrict SSH access with firewalls

3. **File Permissions**: Ensure watched files have appropriate permissions on source devices.

4. **HTTPS**: For production, consider adding HTTPS to the backend using a reverse proxy like Nginx.

---

## Contributing

To contribute to Tower:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT

---

## Support

For issues and questions:
- GitHub Issues: `<repository-url>/issues`
- Documentation: This file

---

**Happy syncing!**