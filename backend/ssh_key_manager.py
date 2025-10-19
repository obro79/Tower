import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

SSH_DIR = Path.home() / ".ssh"
PRIVATE_KEY_PATH = SSH_DIR / "tower_backend_key"
PUBLIC_KEY_PATH = SSH_DIR / "tower_backend_key.pub"

class SSHKeyManager:
    def __init__(self):
        self.private_key_path = PRIVATE_KEY_PATH
        self.public_key_path = PUBLIC_KEY_PATH
        
    def ensure_ssh_dir(self) -> None:
        SSH_DIR.mkdir(mode=0o700, exist_ok=True)
        
    def key_exists(self) -> bool:
        return self.private_key_path.exists() and self.public_key_path.exists()
    
    def generate_keypair(self) -> Tuple[str, str]:
        self.ensure_ssh_dir()
        
        if self.key_exists():
            logger.info(f"SSH key already exists at {self.private_key_path}")
            return self._read_keys()
        
        logger.info("Generating new SSH keypair for Tower backend...")
        
        subprocess.run([
            'ssh-keygen',
            '-t', 'ed25519',
            '-f', str(self.private_key_path),
            '-N', '',
            '-C', 'tower_backend_auto_generated'
        ], check=True, capture_output=True)
        
        self.private_key_path.chmod(0o600)
        self.public_key_path.chmod(0o644)
        
        logger.info(f"SSH keypair generated successfully at {self.private_key_path}")
        
        return self._read_keys()
    
    def _read_keys(self) -> Tuple[str, str]:
        with open(self.public_key_path, 'r') as f:
            public_key_content = f.read().strip()
        
        return (str(self.private_key_path), public_key_content)
    
    def get_public_key(self) -> str:
        if not self.key_exists():
            _, public_key = self.generate_keypair()
            return public_key
        
        with open(self.public_key_path, 'r') as f:
            return f.read().strip()
    
    def get_private_key_path(self) -> str:
        if not self.key_exists():
            self.generate_keypair()
        return str(self.private_key_path)

ssh_key_manager = SSHKeyManager()
