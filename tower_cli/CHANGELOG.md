# Tower CLI - Refactoring Changelog

**Date:** October 19, 2025
**Goal:** Simplify Tower CLI to MVP functionality - remove complexity, focus on watch/search/get

---

## Changes

### Phase 1: Configuration & Types Simplification

#### 2025-10-19 - Initial CHANGELOG created
- Created this changelog to track refactoring progress

#### 2025-10-19 - Simplified types/index.ts
- **Removed interfaces:** `Device`, `SyncHistory`, `SearchOptions`, `WatchOptions`
- **Simplified `WatchedItem`:** Removed `recursive`, `exclude`, `tags`, `lastModified` fields
- **Simplified `Config`:** Now contains only:
  - `backendUrl`: Backend API endpoint
  - `syncInterval`: Sync frequency in minutes
  - `deviceName`: Auto-detected hostname
  - `deviceIp`: Auto-detected IP address
  - `deviceUser`: Auto-detected username
  - `watchList`: Simple array of watched paths with timestamps

#### 2025-10-19 - Simplified utils/config.ts
- **Removed methods:** `addDevice`, `removeDevice`, `getDevices`, `updateDevice`, `addSyncHistory`, `getSyncHistory`, `getSetting`, `setSetting`, `getAllSettings`, `reset`
- **Simplified ConfigManager:**
  - No default config (requires explicit initialization via `tower init`)
  - Added `isInitialized()` method
  - Added `initialize()` method for first-time setup
  - Removed complex settings and device management
  - Only manages: backend URL, sync interval, device info, and watch list

#### 2025-10-19 - Rewrote commands/init.ts
- **Removed:** Device management prompts, conflict resolution, auto-sync toggle
- **Added:** Auto-detection of device info using Node.js APIs
  - `os.hostname()` for device name
  - `os.userInfo().username` for SSH username
  - `dns.lookup()` for local IP address
- **Simplified prompts:** Only asks for backend URL and sync interval
- **Updated next steps:** Simplified command suggestions

#### 2025-10-19 - Simplified commands/watch.ts
- **Removed functions:** `clearWatch()`, `listWatchInteractive()`, `displayDirectoryTree()`, `formatBytes()`
- **Removed options:** tags, exclude patterns, recursive flag, tree view, sort
- **Simplified `addWatch()`:**
  - Single parameter (no options object)
  - Checks if Tower is initialized
  - Registers files/directories with backend immediately
  - For directories, recursively registers all files
- **Enhanced `removeWatch()`:**
  - Added backend deletion via new `deleteFromBackend()` helper
  - Deletes all files under path from backend registry
- **Simplified `listWatch()`:**
  - Removed filtering and sorting
  - Simple table view only
  - Shows: path, type (File/Directory/Missing), added timestamp

#### 2025-10-19 - Simplified commands/search.ts
- **Removed:** `searchLocal()` function and all local search logic
- **Removed dependencies:** Fuse.js fuzzy search, glob file collection, fs content search
- **Removed options:** `SearchOptions` interface (name, content, tags, type filtering)
- **Simplified `search()`:**
  - Backend search only (no fallback to local)
  - Single parameter (query string)
  - Checks if Tower is initialized
  - Auto-wraps query with wildcards if not present
  - Updated help text to suggest "tower get" instead of "tower download"

#### 2025-10-19 - Renamed and updated commands/download.ts → commands/get.ts
- **Renamed file:** `download.ts` → `get.ts`
- **Added natural language detection:**
  - `isNaturalLanguageQuery()` helper function
  - Detects queries with multiple words, no wildcards, no file extension
  - Shows "not yet implemented" message for NL queries
- **Made filename optional:**
  - Shows usage instructions if no filename provided
  - Suggests both filename patterns and NL query examples
- **Added initialization check:** Verifies Tower is configured before proceeding

#### 2025-10-19 - Created commands/get-remote.ts stub
- **New command:** `tower get-remote`
- **Purpose:** List all files in backend registry across all devices (future feature)
- **Current behavior:** Shows "not yet implemented" message
- **Workaround:** Suggests using `tower search *` to see all files

#### 2025-10-19 - Refactored utils/api-client.ts
- **Removed:** `getDeviceInfo()` method, SCP execution logic, hardcoded baseURL
- **Changed constructor:** No longer takes baseURL parameter, uses ConfigManager instead
- **Added:** `getClient()` private method that reads backend URL from config
- **Updated methods:** All API methods now use `getClient()` to get configured axios instance
- **New method:** `deleteFileByPath()` - searches for file by absolute path and deletes it
- **Updated `getLocalFileMetadata()`:** Uses device info from config instead of auto-detecting
- **Updated `downloadFile()`:** Now calls backend GET endpoint with destination params (backend handles 2-hop SCP)
- **Removed local copy logic:** All downloads go through backend, even for localhost

### Phase 2: Command Structure Simplification

#### 2025-10-19 - Completely rewrote index.ts
- **Removed imports:** chalk, sync commands, devices commands, config commands, help utilities, interactive picker
- **Removed command hierarchies:** No more nested `watch add/remove/list`, `sync`, `devices`, `config` subcommands
- **Removed custom help system:** Using commander's default help
- **Removed interactive picker:** No fallback menu when no args provided
- **New flat command structure:**
  - `tower init` - Initialize configuration
  - `tower watch <path>` - Add to watch list (with `--remove` and `--list` flags)
  - `tower watch-list` - Alternative command to list watched items
  - `tower search <query>` - Search files across devices
  - `tower get [filename]` - Download file (optional filename for NL stub)
  - `tower get-remote` - List all remote files (stub)
- **Reduced from 280+ lines to ~60 lines**

#### 2025-10-19 - Deleted obsolete files
- **Removed command files:**
  - `commands/sync.ts` (manual sync, pause/resume, history, status)
  - `commands/devices.ts` (device management)
  - `commands/config.ts` (get/set/list/reset config)
- **Removed utility files:**
  - `utils/help.ts` (custom help system)
  - `utils/interactive.ts` (interactive picker)

### Phase 3: Background Sync Implementation

#### 2025-10-19 - Created daemon/sync-daemon.ts
- **New file:** Background sync daemon for automatic file synchronization
- **Features:**
  - Runs on configurable interval (from config.syncInterval)
  - Tracks file states (path, mtime, size) in memory
  - Detects changes and syncs to backend via POST /files/register
  - Detects deletions and removes from backend via DELETE
  - Handles both individual files and directories recursively
- **Methods:**
  - `start()` - Starts daemon with interval timer
  - `stop()` - Stops daemon gracefully
  - `syncOnce()` - Performs one sync cycle for all watched paths
  - `syncFile()` - Checks and syncs individual file if changed
  - `syncDirectory()` - Recursively syncs all files in directory
  - `handleDeletedPath()` - Removes deleted files from backend
  - `cleanupDeletedFiles()` - Removes files no longer in directory
- **Can be run standalone:** `node dist/daemon/sync-daemon.js`
- **Handles signals:** SIGINT and SIGTERM for graceful shutdown
- **Note:** Daemon management (auto-start, PID file, daemonization) not implemented yet

#### 2025-10-19 - Updated package.json dependencies
- **Removed unused dependencies:**
  - `fuse.js` - No longer using local fuzzy search
  - `inquirer-autocomplete-prompt` - Not used
  - `ora` - Not used for spinners
- **Kept dependencies:**
  - `axios` - Backend API communication
  - `chalk` - Terminal colors in init.ts
  - `cli-table3` - Table formatting in search/watch
  - `commander` - CLI framework
  - `glob` - File pattern matching
  - `inquirer` - Interactive prompts in init/get

---

## Summary

### Files Changed
- **Modified:** 7 files (types/index.ts, utils/config.ts, utils/api-client.ts, commands/init.ts, commands/watch.ts, commands/search.ts, index.ts)
- **Renamed:** 1 file (commands/download.ts → commands/get.ts)
- **Created:** 2 files (commands/get-remote.ts, daemon/sync-daemon.ts, CHANGELOG.md)
- **Deleted:** 5 files (commands/sync.ts, commands/devices.ts, commands/config.ts, utils/help.ts, utils/interactive.ts)

### Lines of Code Reduction
- **index.ts:** 320 lines → 60 lines (81% reduction)
- **types/index.ts:** 49 lines → 9 lines (82% reduction)
- **config.ts:** 150 lines → 85 lines (43% reduction)
- **watch.ts:** 315 lines → 130 lines (59% reduction)
- **search.ts:** 211 lines → 60 lines (72% reduction)
- **Overall:** ~1500+ lines removed

### Commands Before vs After
**Before:** 
- tower init, tower watch add/remove/list/clear, tower search (with options), tower sync/status/history/pause/resume, tower devices list/add/remove/rename, tower config get/set/list/reset, tower get

**After:**
- tower init, tower watch (with flags), tower watch-list, tower search, tower get, tower get-remote

### Next Steps (Not Implemented)
1. Daemon auto-start on `tower init`
2. Daemon management commands (start/stop/status)
3. PID file management for daemon
4. Natural language search implementation
5. `tower get-remote` full implementation

---

## [Unreleased] - 2025-10-19

### Added - SSH Key Management System

#### New file: `src/utils/ssh-setup.ts`
- **Purpose:** Automatic SSH key installation for passwordless SCP transfers
- **Class:** `SSHSetup` with singleton pattern (`sshSetup` export)
- **Features:**
  - Fetches backend's SSH public key via `GET /ssh/public-key`
  - Installs key to `~/.ssh/authorized_keys`
  - Adds comment marker `# tower_cli_auto_added` for easy identification
  - Checks for duplicate keys before installation
  - Creates SSH directory and authorized_keys file if missing
  - Sets correct file permissions (700 for .ssh, 600 for authorized_keys)
  - Displays key fingerprint for verification

**Methods:**
- `fetchPublicKey(backendUrl)` - GET request to backend for public key
- `installPublicKey(publicKey, comment)` - Appends key to authorized_keys
- `setupSSHAccess(backendUrl)` - Combined fetch + install operation
- `removeInstalledKeys()` - Removes all tower_cli added keys (cleanup)
- `keyAlreadyInstalled(publicKey)` - Checks if key exists in authorized_keys
- `ensureSSHDir()` - Creates ~/.ssh if missing
- `ensureAuthorizedKeys()` - Creates authorized_keys if missing

**Response Interface:**
```typescript
interface SSHPublicKeyResponse {
  public_key: string;
  key_type: string;
  comment: string;
  fingerprint: string;
}
```

#### Updated: `src/commands/init.ts`
- **Import:** Added `sshSetup` from `../utils/ssh-setup`
- **New step:** Calls `sshSetup.setupSSHAccess(backendUrl)` after backend URL prompt
- **Error handling:** SSH setup failure is non-fatal (shows warning, continues)
- **User feedback:** 
  - Shows "Setting up SSH access for passwordless file transfers..."
  - Displays key fingerprint on success
  - Warns user if SSH setup fails (manual configuration needed)

### Changed

- **init.ts workflow:** Now includes SSH key installation step before saving config
- **SSH key location:** Backend key installed to `~/.ssh/authorized_keys` on client

### Technical Details

#### SSH Key Flow
1. User runs `tower init`
2. CLI prompts for backend URL and sync interval
3. CLI calls `GET http://<backend>/ssh/public-key`
4. Backend responds with ed25519 public key + fingerprint
5. CLI appends key to `~/.ssh/authorized_keys` with tower_cli marker
6. Backend can now SCP to/from this device without password
7. Config saved to `~/.tower/config.json`

#### Security Considerations
- Public key only (no private key exchange)
- Keys marked with comment for traceability
- Duplicate detection prevents key accumulation
- Non-fatal failure (user can manually configure SSH)
- StrictHostKeyChecking=no in backend (auto-accepts host keys)

### Files Modified
- Created `src/utils/ssh-setup.ts` - SSH key installation utility
- Updated `src/commands/init.ts` - Added SSH setup step
- Updated `CHANGELOG.md` - This file

### Dependencies
No new dependencies. Uses existing:
- `axios` - HTTP request to backend
- `fs` - File system operations
- `os` - Home directory detection
- `path` - Path manipulation

### Testing Instructions
1. Run `tower init` with backend URL
2. Check `~/.ssh/authorized_keys` for tower_cli marker
3. Verify backend can SSH to device: `ssh user@device-ip "echo test"`
4. Verify SCP works: `scp user@device-ip:/path/to/file ./test`


---

## [Bugfix] - 2025-10-19 (Post-SSH Implementation)

### Fixed

#### IPv4 Detection on Windows
- **Issue:** `dns.lookup(os.hostname())` was returning IPv6 link-local addresses (fe80::...) on Windows instead of IPv4
- **Solution:** 
  - Added `{ family: 4 }` option to `dns.lookup()` to force IPv4
  - Added fallback to iterate through `os.networkInterfaces()` to find non-internal IPv4
  - Prioritizes external IPv4 addresses over loopback
- **Impact:** Clients now correctly register with IPv4 addresses (192.168.x.x) instead of IPv6
- **File:** `src/commands/init.ts`

**Before:**
```typescript
dns.lookup(os.hostname(), (err, address) => { ... })
// Returns: fe80::144b:6510:cbe6:20b8 on Windows
```

**After:**
```typescript
dns.lookup(os.hostname(), { family: 4 }, (err, address) => {
  if (err || !address) {
    // Fallback: iterate network interfaces for IPv4
    const networkInterfaces = os.networkInterfaces();
    for (const interfaceName in networkInterfaces) {
      const addresses = networkInterfaces[interfaceName];
      if (addresses) {
        for (const addr of addresses) {
          if (addr.family === 'IPv4' && !addr.internal) {
            resolve(addr.address);
            return;
          }
        }
      }
    }
    resolve('127.0.0.1');
  }
})
// Returns: 192.168.50.142
```

### Related Backend Fix

Backend also received fix for Windows path handling:
- Added `format_scp_path()` function to convert `C:\Users\...` to `/C/Users/...`
- SCP now works correctly with Windows file paths

