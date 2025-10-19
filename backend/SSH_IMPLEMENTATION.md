# SSH Key Management Implementation

## Overview

Implemented automatic SSH key generation and distribution system for Tower File Sync. The backend generates an SSH keypair on startup, and clients automatically install the public key during `tower init`, enabling passwordless SCP transfers.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    SSH Key Flow                               │
└──────────────────────────────────────────────────────────────┘

1. Backend Startup
   └─> Checks for ~/.ssh/tower_backend_key
       ├─> If exists: Load existing key
       └─> If not: Generate new ed25519 keypair

2. Client Init (tower init)
   ├─> User enters backend URL
   ├─> GET /ssh/public-key → Fetch backend's public key
   ├─> Append to ~/.ssh/authorized_keys (with # tower_cli marker)
   └─> Save config to ~/.tower/config.json

3. File Transfer
   ├─> Backend uses -i ~/.ssh/tower_backend_key for SCP
   └─> No password prompt (key-based auth)
```

## Backend Implementation

### Files Created

#### 1. `ssh_key_manager.py`
**Purpose:** Manage SSH keypair lifecycle

**Key Features:**
- Automatic key generation on first run
- Uses ed25519 algorithm (secure, fast, small keys)
- Proper file permissions (600 for private, 644 for public)
- Singleton pattern for global access

**API:**
```python
ssh_key_manager.generate_keypair() -> (private_path, public_key_content)
ssh_key_manager.get_public_key() -> str
ssh_key_manager.get_private_key_path() -> str
ssh_key_manager.key_exists() -> bool
```

**Key Location:**
- Private: `~/.ssh/tower_backend_key`
- Public: `~/.ssh/tower_backend_key.pub`

### Files Modified

#### 2. `main.py`
**Changes:**
1. Added `from ssh_key_manager import ssh_key_manager`
2. Modified `on_startup()` to generate keys
3. Added new endpoint `GET /ssh/public-key`
4. Updated SCP commands to use backend's private key

**New Endpoint:**
```python
GET /ssh/public-key

Response:
{
  "public_key": "ssh-ed25519 AAAA... tower_backend_auto_generated",
  "key_type": "ssh-ed25519",
  "comment": "tower_backend_auto_generated",
  "fingerprint": "SHA256:vD6A2BxfSCpgGIVxpqHpmT5qXYjEoXhKzeSryln04Tk"
}
```

**SCP Enhancement:**
```python
# Before
subprocess.run(['scp', source, dest], check=True)

# After
ssh_key = ssh_key_manager.get_private_key_path()
subprocess.run([
    'scp', 
    '-i', ssh_key,
    '-o', 'StrictHostKeyChecking=no',
    source, dest
], check=True)
```

## Frontend (tower_cli) Implementation

### Files Created

#### 1. `src/utils/ssh-setup.ts`
**Purpose:** Fetch and install backend's SSH public key

**Key Features:**
- Fetches key from backend API
- Checks for duplicates before installing
- Creates SSH directory if missing
- Sets correct permissions (700 for .ssh, 600 for authorized_keys)
- Adds marker comment for easy identification

**API:**
```typescript
sshSetup.setupSSHAccess(backendUrl: string) -> Promise<void>
sshSetup.fetchPublicKey(backendUrl: string) -> Promise<SSHPublicKeyResponse>
sshSetup.installPublicKey(publicKey: string, comment?: string) -> void
sshSetup.removeInstalledKeys() -> number
```

**Authorized Keys Entry:**
```
ssh-ed25519 AAAA... tower_backend_auto_generated # tower_cli_auto_added
```

### Files Modified

#### 2. `src/commands/init.ts`
**Changes:**
1. Added `import { sshSetup } from '../utils/ssh-setup'`
2. Added SSH setup step after backend URL prompt
3. Non-fatal error handling (warns user if SSH setup fails)

**New Flow:**
```typescript
1. Prompt for backend URL and sync interval
2. Call sshSetup.setupSSHAccess(backendUrl)
   ├─> Success: Show fingerprint, continue
   └─> Failure: Warn user, continue anyway
3. Save config to ~/.tower/config.json
```

## Testing

### Backend Test

```bash
# Test SSH key generation
cd backend
python3 << EOF
from ssh_key_manager import ssh_key_manager
private, public = ssh_key_manager.generate_keypair()
print(f"Private: {private}")
print(f"Public: {public}")
EOF

# Check file permissions
ls -la ~/.ssh/tower_backend_key*

# Get fingerprint
ssh-keygen -lf ~/.ssh/tower_backend_key.pub

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000

# Test endpoint (from another terminal)
curl http://localhost:8000/ssh/public-key
```

### Frontend Test

```bash
# Build CLI
cd tower_cli
npm run build

# Initialize (replace with your backend IP)
./dist/index.js init
# Enter: http://192.168.50.182:8000
# Enter: 5 (sync interval)

# Verify key installed
grep "tower_cli" ~/.ssh/authorized_keys

# Test SSH from backend to client
ssh <your-username>@<your-ip> "echo 'SSH test successful'"
```

## Security Considerations

1. **No Passphrase**: Private key has no passphrase (required for automated SCP)
   - Risk: If backend server is compromised, attacker can SSH to all clients
   - Mitigation: Keep backend server secure, limit to trusted network

2. **StrictHostKeyChecking=no**: Automatically accepts new host keys
   - Risk: Vulnerable to MITM attacks on first connection
   - Mitigation: Use on trusted local network only

3. **Marker Comments**: All installed keys have `# tower_cli_auto_added`
   - Benefit: Easy to identify and remove Tower keys
   - Cleanup: `sshSetup.removeInstalledKeys()` removes all Tower keys

4. **Key Algorithm**: Uses ed25519 (modern, secure)
   - 256-bit security (equivalent to 3072-bit RSA)
   - Fast signature generation and verification
   - Small key size (68 bytes public, 419 bytes private)

## Troubleshooting

### Backend Can't Generate Keys

**Error:** `ssh-keygen: command not found`

**Solution:**
```bash
# macOS (should be pre-installed)
which ssh-keygen

# Linux
sudo apt-get install openssh-client
```

### Client Can't Fetch Public Key

**Error:** `Failed to fetch SSH key: Network Error`

**Check:**
1. Backend is running: `curl http://<backend-ip>:8000`
2. Firewall allows port 8000
3. Backend URL is correct in tower init

### SSH Still Asks for Password

**Possible Causes:**
1. Public key not in authorized_keys
2. Wrong file permissions (should be 600)
3. SSH service not running (Windows)
4. User mismatch in config

## Files Modified Summary

### Backend
- ✅ Created `ssh_key_manager.py`
- ✅ Modified `main.py`
- ✅ Updated `CHANGELOG.md`

### Frontend
- ✅ Created `src/utils/ssh-setup.ts`
- ✅ Modified `src/commands/init.ts`
- ✅ Updated `CHANGELOG.md`
