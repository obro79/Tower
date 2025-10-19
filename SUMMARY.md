# Tower - Cross-Device File Sync

**Version:** 0.1.0

## Overview

Tower is a CLI tool for syncing and discovering files across devices on a local network. Multiple clients connect to a central FastAPI backend that maintains a metadata registry. Files are transferred directly between devices via SCP.

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────┐
│ Tower CLI   │◄──REST──│   Backend    │◄──SQL───│ SQLite   │
│ (TypeScript)│         │  (FastAPI)   │         │ (Metadata)│
└─────────────┘         └──────────────┘         └──────────┘
```

**Backend**: Metadata registry only (no file storage). Handles 2-hop SCP transfers (source → backend → destination).

**CLI**: Watches files/folders, auto-syncs metadata to backend, searches and downloads files.

## CLI Commands

- `tower init` - Configure backend API endpoint (required)
- `tower watch <path>` - Add file/folder to watch list
- `tower search <query>` - Search files by name (wildcard support: `*.txt`)
- `tower get` - Download file from network (natural language search stub - not implemented)

## Auto-Sync

Background process syncs watched files every N minutes:
- New/modified files → `POST /files/register`
- Deleted files → `DELETE /files/{id}`

## Backend API

- `POST /files/register` - Register/update file metadata
- `GET /files/search?query=` - Wildcard search
- `GET /files/{id}` - Download file via 2-hop SCP
- `DELETE /files/{id}` - Remove metadata

## Configuration

- Local network only (no authentication)
- Backend IP set manually via `tower init`



