# Tower

A CLI tool to help you keep your files synced across devices.

## Installation

```bash
npm install
npm run build
```

To use the CLI globally, you can link it:

```bash
npm link
```

Now you can use `tower` from anywhere in your terminal.

## Quick Start

Initialize Tower with the setup wizard:

```bash
tower init
```

This will guide you through initial configuration and add your first device.

## Commands

### Watch Management

Manage files and directories in your watch list.

```bash
# Add a file to watch list
tower watch add <path>

# Add a directory recursively with tags
tower watch add /path/to/folder -r --tags project,important

# Add with exclusions
tower watch add /path/to/folder -r --exclude node_modules dist

# List all watched items
tower watch list

# Filter by tags
tower watch list --tags project

# Sort the list
tower watch list --sort name
tower watch list --sort modified

# Remove an item
tower watch remove <path>

# Clear all watched items
tower watch clear
```

### Search

Search for files within your watch list.

```bash
# Search by filename
tower search "config"

# Search by filename only
tower search "config" --name

# Search file contents
tower search "TODO" --content

# Filter by file type
tower search "function" --type js

# Filter by tags
tower search "config" --tags project
```

### Sync Operations

Manage file synchronization.

```bash
# Manually trigger sync
tower sync

# Force sync even if no changes
tower sync --force

# Dry run (see what would be synced)
tower sync --dry-run

# Show sync status
tower sync status

# View sync history
tower sync history

# View last 5 syncs
tower sync history 5

# Pause auto-sync
tower sync pause

# Resume auto-sync
tower sync resume
```

### Device Management

Manage connected devices for syncing.

```bash
# List all devices
tower devices list

# Add a new device (interactive)
tower devices add

# Remove a device
tower devices remove <device-id>

# Rename a device
tower devices rename <device-id> "New Name"
```

### Configuration

Manage Tower settings.

```bash
# List all settings
tower config list

# Get a specific setting
tower config get autoSync

# Set a setting
tower config set autoSync true
tower config set syncInterval 10

# Reset to defaults
tower config reset
```

### General

```bash
# Show overall status
tower status

# Show version
tower --version

# Show help
tower --help

# Show help for a command
tower watch --help
```

## Configuration

Tower stores its configuration in `~/.tower/config.json`.

### Default Settings

- `autoSync`: true - Automatically sync files
- `syncInterval`: 5 - Sync interval in minutes
- `conflictResolution`: "latest" - How to handle conflicts (latest, manual, keep-both)
- `excludePatterns`: Common patterns to exclude (node_modules, .git, *.log, .DS_Store)

## Features

- Watch files and directories for changes
- Recursive directory watching with exclusion patterns
- Tag-based organization
- Fuzzy filename search
- Content search across watched files
- Device management for multi-device sync
- Sync history tracking
- Interactive setup wizard
- Colorful CLI output with tables and progress indicators
- Configurable auto-sync behavior

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Watch mode for development
npm run dev

# Run locally
npm run tower -- <command>
# or
node dist/index.js <command>
```

## Project Structure

```
src/
├── commands/          # Command implementations
│   ├── config.ts     # Configuration commands
│   ├── devices.ts    # Device management
│   ├── init.ts       # Setup wizard
│   ├── search.ts     # File search
│   ├── sync.ts       # Sync operations
│   └── watch.ts      # Watch list management
├── types/            # TypeScript type definitions
│   └── index.ts
├── utils/            # Utilities
│   ├── config.ts     # Config manager
│   └── logger.ts     # Colored logging
└── index.ts          # Main CLI entry point
```

## License

MIT