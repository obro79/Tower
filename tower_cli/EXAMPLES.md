# Tower CLI - Sample Commands

## Prerequisites
1. Backend server must be running:
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Build the CLI:
   ```bash
   cd tower_cli
   npm install
   npm run build
   ```

---

## 1. Initialize Tower

Configure the CLI with your backend URL and sync interval.

```bash
# First time setup
node dist/index.js init
```

**Example interaction:**
```
Welcome to Tower!

Let's set up your file sync configuration.

Auto-detected device info:
  Device: MacBook-Pro
  User: john
  IP: 192.168.1.100

? Backend API URL (e.g., http://192.168.1.10:8000): http://192.168.1.50:8000
? Auto-sync interval (minutes): 5

✓ Configuration saved!

Next steps:
  - Add files to watch: tower watch <path>
  - Search for files: tower search <query>
  - Download files: tower get <filename>
```

---

## 2. Watch Files/Directories

Add files or directories to your watch list. They will be registered with the backend immediately.

### Add a single file
```bash
node dist/index.js watch /Users/john/documents/report.pdf
```

**Output:**
```
✓ Added to watch list: /Users/john/documents/report.pdf
✓ Registered with backend: report.pdf (ID: 1)
```

### Add a directory (recursive)
```bash
node dist/index.js watch /Users/john/projects/my-app
```

**Output:**
```
✓ Added to watch list: /Users/john/projects/my-app
✓ Registered 47 file(s) from directory with backend
```

### Remove from watch list
```bash
node dist/index.js watch /Users/john/documents/report.pdf --remove
```

**Output:**
```
✓ Removed from watch list: /Users/john/documents/report.pdf
✓ Removed file from backend registry
```

### List watched items
```bash
node dist/index.js watch-list
```

**Output:**
```
┌────────────────────────────────────────────┬───────────┬─────────────────────┐
│ Path                                       │ Type      │ Added               │
├────────────────────────────────────────────┼───────────┼─────────────────────┤
│ /Users/john/documents/report.pdf          │ File      │ 10/19/2025, 2:30 PM │
│ /Users/john/projects/my-app                │ Directory │ 10/19/2025, 2:35 PM │
└────────────────────────────────────────────┴───────────┴─────────────────────┘
✓ Total: 2 item(s)
```

---

## 3. Search Files

Search for files across all devices registered in the backend.

### Search by exact filename
```bash
node dist/index.js search "report.pdf"
```

**Output:**
```
ℹ Searching backend registry for: "report.pdf"
┌────┬─────────────┬──────────────┬──────────┬─────────────────────┐
│ ID │ File        │ Device       │ Size     │ Modified            │
├────┼─────────────┼──────────────┼──────────┼─────────────────────┤
│ 1  │ report.pdf  │ MacBook-Pro  │ 1.23 MB  │ 10/19/2025, 1:45 PM │
│ 15 │ report.pdf  │ Desktop-PC   │ 1.25 MB  │ 10/19/2025, 2:10 PM │
└────┴─────────────┴──────────────┴──────────┴─────────────────────┘
✓ Found 2 file(s) across all devices
ℹ Use "tower get <filename>" to download a file
```

### Search with wildcards
```bash
node dist/index.js search "*.pdf"
```

**Output:**
```
ℹ Searching backend registry for: "*.pdf"
┌────┬─────────────────┬──────────────┬──────────┬─────────────────────┐
│ ID │ File            │ Device       │ Size     │ Modified            │
├────┼─────────────────┼──────────────┼──────────┼─────────────────────┤
│ 1  │ report.pdf      │ MacBook-Pro  │ 1.23 MB  │ 10/19/2025, 1:45 PM │
│ 3  │ invoice.pdf     │ MacBook-Pro  │ 0.45 MB  │ 10/18/2025, 9:20 AM │
│ 15 │ report.pdf      │ Desktop-PC   │ 1.25 MB  │ 10/19/2025, 2:10 PM │
└────┴─────────────────┴──────────────┴──────────┴─────────────────────┘
✓ Found 3 file(s) across all devices
```

### Search for all files
```bash
node dist/index.js search "*"
```

### Search with partial match
```bash
node dist/index.js search "2024"
```

---

## 4. Download Files (Get)

Download files from remote devices.

### Get by filename pattern
```bash
node dist/index.js get "report.pdf"
```

**Example interaction (single match):**
```
ℹ Searching for files matching "report.pdf"...
✓ Found 1 matching file
ℹ Using: report.pdf from MacBook-Pro
ℹ File: report.pdf
ℹ Location: MacBook-Pro (192.168.1.100)
ℹ Size: 1.23 MB
ℹ Initiating file transfer via SCP...
ℹ From: john@192.168.1.100:/Users/john/documents/report.pdf
ℹ To: /Users/jane/Downloads/report.pdf
✓ File downloaded successfully!
✓ Location: /Users/jane/Downloads/report.pdf
```

**Example interaction (multiple matches):**
```
ℹ Searching for files matching "report.pdf"...
✓ Found 2 matching files

? Select file to download: (Use arrow keys)
❯ report.pdf (MacBook-Pro @ 192.168.1.100) - 1.23 MB - /Users/john/documents/report.pdf - Modified: 10/19/2025
  report.pdf (Desktop-PC @ 192.168.1.150) - 1.25 MB - /home/john/docs/report.pdf - Modified: 10/19/2025

[After selection, download proceeds...]
```

### Get with custom destination
```bash
node dist/index.js get "report.pdf" -d /Users/jane/projects/
```

### Natural language query (not implemented yet)
```bash
node dist/index.js get "research paper about AI"
```

**Output:**
```
⚠ Natural language search is not yet implemented
ℹ For now, use filename patterns like: tower get "*.pdf" or tower get "paper"
```

### Get without query (shows usage)
```bash
node dist/index.js get
```

**Output:**
```
✖ Please provide a filename or search query
ℹ Usage: tower get <filename>
ℹ        tower get "research paper about AI"  (natural language - not implemented)
```

---

## 5. List Remote Files (Get-Remote)

List all files in the backend registry across all devices.

```bash
node dist/index.js get-remote
```

**Output:**
```
⚠ tower get-remote is not yet implemented
ℹ This command will list all files registered in the backend across all devices
ℹ For now, use "tower search *" to see all files
```

---

## 6. Background Sync Daemon

The daemon automatically syncs watched files to the backend at regular intervals.

### Start the daemon
```bash
node dist/daemon/sync-daemon.js
```

**Output:**
```
ℹ Starting sync daemon (interval: 5 minutes)
✓ Sync daemon started
```

The daemon will:
- Check watched files every N minutes (configured in `tower init`)
- Register new/modified files with backend
- Delete removed files from backend
- Run until you press Ctrl+C

### Stop the daemon
Press `Ctrl+C` or send SIGTERM:
```
^C
ℹ Received SIGINT, shutting down...
ℹ Sync daemon stopped
```

---

## Common Workflows

### Workflow 1: Share a file with another device

**On Device A (source):**
```bash
# Initialize and add file to watch
node dist/index.js init  # Configure backend
node dist/index.js watch /Users/alice/documents/presentation.pptx
```

**On Device B (destination):**
```bash
# Initialize and search for the file
node dist/index.js init  # Configure same backend
node dist/index.js search "presentation.pptx"
node dist/index.js get "presentation.pptx"
```

### Workflow 2: Sync a project directory

```bash
# Add entire project to watch list
node dist/index.js watch /Users/alice/projects/my-app

# Start background daemon for auto-sync
node dist/daemon/sync-daemon.js
```

Now any changes in `/Users/alice/projects/my-app` will be automatically synced to the backend every 5 minutes (or whatever interval you configured).

### Workflow 3: Find files across all your devices

```bash
# Search for all Python files
node dist/index.js search "*.py"

# Search for files with "budget" in the name
node dist/index.js search "budget"

# Download specific file
node dist/index.js get "budget_2024.xlsx"
```

---

## Tips

1. **Wildcards**: Use `*` for pattern matching: `*.pdf`, `report*`, `*2024*`
2. **Backend must be running**: All commands except `init` require the backend to be accessible
3. **Auto-sync**: Start the daemon (`node dist/daemon/sync-daemon.js`) to automatically sync watched files
4. **Config location**: Tower stores its configuration in `~/.tower/config.json`
5. **Same backend**: All devices must be configured to use the same backend URL to share files

---

## Troubleshooting

### "Tower not initialized"
```bash
node dist/index.js init
```

### "Backend server not running"
Check if the backend is running:
```bash
curl http://your-backend-ip:8000/
```

### File not syncing
- Check if the file/directory is in your watch list: `node dist/index.js watch-list`
- Manually register it: `node dist/index.js watch <path>`
- Start the daemon: `node dist/daemon/sync-daemon.js`
