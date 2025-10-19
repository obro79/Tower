#!/bin/bash

echo "Testing SSH Key Manager Implementation"
echo "======================================="
echo ""

echo "1. Testing SSH Key Generation..."
python3 << PYTHON
from ssh_key_manager import ssh_key_manager
private, public = ssh_key_manager.generate_keypair()
print(f"✓ Keys generated at {private}")
print(f"✓ Public key: {public}")
PYTHON

echo ""
echo "2. Checking file permissions..."
ls -la ~/.ssh/tower_backend_key*

echo ""
echo "3. Getting key fingerprint..."
ssh-keygen -lf ~/.ssh/tower_backend_key.pub

echo ""
echo "======================================="
echo "✓ SSH Key Manager test complete!"
echo ""
echo "Next steps:"
echo "  1. Start the backend: uvicorn main:app --host 0.0.0.0 --port 8000"
echo "  2. Test endpoint: curl http://localhost:8000/ssh/public-key"
echo "  3. Run tower init from a client device"
