# Tower CLI Commands Reference

Complete reference for all Tower CLI commands and their functionality.

## Interactive Mode

```bash
tower
```

**Description:** Launches interactive fuzzy finder to search and select commands.

**Features:**
- Type to search commands with fuzzy matching
- Arrow keys to navigate through filtered results
- Enter to select and execute a command
- Two-column layout: commands (green) | descriptions (gray)

---

## Watch Management

Manage files and directories in your watch list for syncing.

### `tower watch add <path>`

**Description:** Add a file or directory to the watch list.

**Arguments:**
- `<path>` - Path to file or directory to watch

**Options:**
- `-r, --recursive` - Watch directory recursively (includes all subdirectories)
- `-e, --exclude <patterns...>` - Exclude patterns (e.g., node_modules, *.log)
- `-t, --tags <tags...>` - Add tags to organize watched items

**Examples:**
```bash
# Add a single file
tower watch add /path/to/file.txt

# Add directory recursively
tower watch add /path/to/folder -r

# Add with tags
tower watch add /path/to/project -r --tags work,important

# Add with exclusions
tower watch add /path/to/project -r --exclude node_modules dist *.log
```

**Purpose:** Marks files/directories for automatic syncing across devices.

---

### `tower watch remove <path>`

**Description:** Remove a file or directory from the watch list.

**Arguments:**
- `<path>` - Path to file or directory to remove

**Examples:**
```bash
tower watch remove /path/to/file.txt
tower watch remove /path/to/folder
```

**Purpose:** Stop syncing a specific file or directory.

---

### `tower watch list`

**Description:** Display all items currently in the watch list.

**Options:**
- `--tags <tags>` - Filter by comma-separated tags
- `--sort <field>` - Sort by field (name | modified)

**Examples:**
```bash
# List all watched items
tower watch list

# Filter by tags
tower watch list --tags work

# Sort by name
tower watch list --sort name

# Sort by last modified
tower watch list --sort modified
```

**Output:** Table showing path, type (file/directory), tags, and date added.

**Purpose:** View and organize all items being synced.

---

### `tower watch clear`

**Description:** Remove all items from the watch list.

**Behavior:**
- Prompts for confirmation before clearing
- Cannot be undone

**Examples:**
```bash
tower watch clear
```

**Purpose:** Reset watch list to start fresh.

---

## Search

Search for files within your watch list.

### `tower search <query>`

**Description:** Search for files in the watch list by name or content.

**Arguments:**
- `<query>` - Search query string

**Options:**
- `-n, --name` - Search by filename only (faster)
- `-c, --content` - Search file contents (slower)
- `--tags <tags>` - Filter by comma-separated tags
- `--type <ext>` - Filter by file extension (e.g., js, md, txt)

**Examples:**
```bash
# Search by filename (default)
tower search config

# Search by filename only

tower search config --name

# Search file contents
tower search "TODO" --content

# Filter by file type
tower search function --type js

# Search with tags
tower search readme --tags project

# Combine filters
tower search api --content --type ts --tags backend
```

**Output:** Table showing matched files with path, type, and match location.

**Purpose:** Quickly find files across all watched locations using fuzzy matching.

---

## Sync Operations

Manage file synchronization across devices.

### `tower sync`

**Description:** Manually trigger a sync operation.

**Options:**
- `-f, --force` - Force sync even if no changes detected
- `--dry-run` - Show what would be synced without actually syncing

**Examples:**
```bash
# Normal sync
tower sync

# Force sync all files
tower sync --force

# Preview sync without executing
tower sync --dry-run
```

**Purpose:** Immediately sync files to all connected devices.

---

### `tower sync status`

**Description:** Show current sync status and device information.

**Output:**
- Number of watched items
- Number of connected devices
- Auto-sync status (enabled/disabled)
- Sync interval setting
- Device list with online/offline status
- Last sync timestamp and results

**Examples:**
```bash
tower sync status
```

**Purpose:** Check sync configuration and device connectivity.

---

### `tower sync history [n]`

**Description:** Display sync operation history.

**Arguments:**
- `[n]` - Number of entries to show (default: 10)

**Output:** Table with timestamp, files changed, status (success/failed), and details.

**Examples:**
```bash
# Show last 10 syncs
tower sync history

# Show last 5 syncs
tower sync history 5

# Show last 20 syncs
tower sync history 20
```

**Purpose:** Review past sync operations and troubleshoot issues.

---

### `tower sync pause`

**Description:** Temporarily pause automatic syncing.

**Examples:**
```bash
tower sync pause
```

**Purpose:** Stop automatic syncing while keeping configuration. Useful when working offline or making many changes.

---

### `tower sync resume`

**Description:** Resume automatic syncing after pausing.

**Examples:**
```bash
tower sync resume
```

**Purpose:** Re-enable automatic syncing at the configured interval.

---

## Device Management

Manage devices for multi-device syncing.

### `tower devices list`

**Description:** List all connected devices.

**Output:** Table showing device ID, name, status (online/offline/syncing), date added, and last seen.

**Examples:**
```bash
tower devices list
```

**Purpose:** View all devices configured for syncing.

---

### `tower devices add`

**Description:** Add a new device to sync group (interactive).

**Behavior:**
- Prompts for device name
- Generates unique device ID
- Adds device to configuration

**Examples:**
```bash
tower devices add
# Interactive prompts:
# - Device name: My Laptop
# - Device ID: dev_1234567890_abc123
```

**Purpose:** Register a new device for syncing.

---

### `tower devices remove <device-id>`

**Description:** Remove a device from sync group.

**Arguments:**
- `<device-id>` - Unique ID of device to remove

**Behavior:**
- Prompts for confirmation
- Removes device from configuration

**Examples:**
```bash
tower devices remove dev_1234567890_abc123
```

**Purpose:** Unregister a device that should no longer sync.

---

### `tower devices rename <device-id> <name>`

**Description:** Change the display name of a device.

**Arguments:**
- `<device-id>` - Unique ID of device
- `<name>` - New display name

**Examples:**
```bash
tower devices rename dev_1234567890_abc123 "Work Laptop"
```

**Purpose:** Update device name for easier identification.

---

## Configuration

Manage Tower settings.

### `tower config list`

**Description:** Display all configuration settings.

**Output:** Table showing setting names and current values.

**Settings:**
- `autoSync` - Enable/disable automatic syncing (boolean)
- `syncInterval` - Minutes between auto-syncs (number)
- `conflictResolution` - How to handle conflicts (latest | manual | keep-both)
- `excludePatterns` - Patterns to exclude from sync (array)

**Examples:**
```bash
tower config list
```

**Purpose:** View current configuration.

---

### `tower config get <key>`

**Description:** Get the value of a specific setting.

**Arguments:**
- `<key>` - Setting name (e.g., autoSync, syncInterval)

**Examples:**
```bash
tower config get autoSync
tower config get syncInterval
tower config get conflictResolution
```

**Purpose:** Check a specific setting value.

---

### `tower config set <key> <value>`

**Description:** Update a configuration setting.

**Arguments:**
- `<key>` - Setting name
- `<value>` - New value

**Examples:**
```bash
# Enable auto-sync
tower config set autoSync true

# Change sync interval to 10 minutes
tower config set syncInterval 10

# Change conflict resolution strategy
tower config set conflictResolution keep-both
```

**Purpose:** Customize Tower behavior.

---

### `tower config reset`

**Description:** Reset all settings to default values.

**Behavior:**
- Prompts for confirmation
- Restores factory defaults
- Keeps watch list and devices

**Examples:**
```bash
tower config reset
```

**Purpose:** Restore default configuration.

---

## General Commands

### `tower init`

**Description:** Interactive setup wizard for initial configuration.

**Behavior:**
- Prompts for sync preferences
- Asks to add first device
- Creates configuration file

**Prompts:**
1. Enable automatic syncing? (yes/no)
2. Sync interval in minutes (default: 5)
3. Conflict resolution strategy (latest/manual/keep-both)
4. Add this device? (yes/no)
5. Device name (default: hostname)

**Examples:**
```bash
tower init
```

**Purpose:** Set up Tower for first-time use.

---

### `tower status`

**Description:** Show overall Tower status (same as `tower sync status`).

**Examples:**
```bash
tower status
```

**Purpose:** Quick status check.

---

### `tower help [command]`

**Description:** Display help information.

**Arguments:**
- `[command]` - Optional command name for specific help

**Examples:**
```bash
# Show all commands
tower help

# Show help for watch commands
tower help watch

# Show help for sync commands
tower help sync

# Show help for devices commands
tower help devices

# Show help for config commands
tower help config

# Show help for search command
tower help search
```

**Purpose:** Get command usage information.

---

## Configuration File

Tower stores its configuration in `~/.tower/config.json`.

### Default Settings

```json
{
  "watchList": [],
  "devices": [],
  "syncHistory": [],
  "settings": {
    "autoSync": true,
    "syncInterval": 5,
    "conflictResolution": "latest",
    "excludePatterns": ["node_modules", ".git", "*.log", ".DS_Store"]
  }
}
```

---

## Common Workflows

### First-Time Setup
```bash
# 1. Initialize Tower
tower init

# 2. Add files to watch
tower watch add ~/Documents -r --tags personal
tower watch add ~/Projects -r --tags work --exclude node_modules dist

# 3. Check status
tower status

# 4. Manual sync
tower sync
```

### Adding Another Device
```bash
# On new device:
# 1. Initialize
tower init

# 2. Add device
tower devices add

# 3. Add same watch list
tower watch add ~/Documents -r
tower watch add ~/Projects -r
```

### Searching Files
```bash
# Find config files
tower search config

# Find TODOs in code
tower search "TODO" --content --type js

# Find project files
tower search --tags project
```

### Managing Sync
```bash
# Pause before making lots of changes
tower sync pause

# Make changes...

# Resume and sync
tower sync resume
tower sync

# Check history
tower sync history
```

---

## Exit Codes

- `0` - Success
- `1` - Error occurred

---

## Tips

1. **Use tags** to organize watched items by project, priority, or category
2. **Exclude patterns** to avoid syncing large or temporary files
3. **Check sync history** to troubleshoot sync issues
4. **Use dry-run** before forcing a full sync
5. **Pause sync** when working offline or making bulk changes
6. **Interactive mode** (`tower`) for discovering commands
