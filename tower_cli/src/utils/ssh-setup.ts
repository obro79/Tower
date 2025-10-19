import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import axios from 'axios';
import { Logger } from './logger';

const SSH_DIR = path.join(os.homedir(), '.ssh');
const AUTHORIZED_KEYS_PATH = path.join(SSH_DIR, 'authorized_keys');
const TOWER_MARKER = '# tower_cli_auto_added';

export interface SSHPublicKeyResponse {
  public_key: string;
  key_type: string;
  comment: string;
  fingerprint: string;
}

export class SSHSetup {
  
  private ensureSSHDir(): void {
    if (!fs.existsSync(SSH_DIR)) {
      fs.mkdirSync(SSH_DIR, { mode: 0o700, recursive: true });
      Logger.success(`Created SSH directory: ${SSH_DIR}`);
    }
  }

  private ensureAuthorizedKeys(): void {
    this.ensureSSHDir();
    
    if (!fs.existsSync(AUTHORIZED_KEYS_PATH)) {
      fs.writeFileSync(AUTHORIZED_KEYS_PATH, '', { mode: 0o600 });
      Logger.success(`Created authorized_keys file`);
    } else {
      fs.chmodSync(AUTHORIZED_KEYS_PATH, 0o600);
    }
  }

  private keyAlreadyInstalled(publicKey: string): boolean {
    if (!fs.existsSync(AUTHORIZED_KEYS_PATH)) {
      return false;
    }

    const authorizedKeys = fs.readFileSync(AUTHORIZED_KEYS_PATH, 'utf-8');
    const keyParts = publicKey.split(' ');
    const keyData = keyParts[1];

    return authorizedKeys.includes(keyData);
  }

  async fetchPublicKey(backendUrl: string): Promise<SSHPublicKeyResponse> {
    try {
      const url = `${backendUrl}/ssh/public-key`;
      Logger.info(`Fetching SSH public key from ${url}...`);
      
      const response = await axios.get<SSHPublicKeyResponse>(url, {
        timeout: 10000
      });

      Logger.success(`Received SSH public key (${response.data.key_type})`);
      Logger.info(`Fingerprint: ${response.data.fingerprint}`);
      
      return response.data;
    } catch (error: any) {
      if (error.response) {
        throw new Error(`Failed to fetch SSH key: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  installPublicKey(publicKey: string, comment: string = 'tower_backend'): void {
    this.ensureAuthorizedKeys();

    if (this.keyAlreadyInstalled(publicKey)) {
      Logger.info('SSH public key already installed in authorized_keys');
      return;
    }

    let authorizedKeys = '';
    if (fs.existsSync(AUTHORIZED_KEYS_PATH)) {
      authorizedKeys = fs.readFileSync(AUTHORIZED_KEYS_PATH, 'utf-8');
    }

    if (authorizedKeys.length > 0 && !authorizedKeys.endsWith('\n')) {
      authorizedKeys += '\n';
    }

    const keyEntry = `${publicKey} ${TOWER_MARKER}\n`;
    authorizedKeys += keyEntry;

    fs.writeFileSync(AUTHORIZED_KEYS_PATH, authorizedKeys, { mode: 0o600 });
    
    Logger.success('SSH public key added to ~/.ssh/authorized_keys');
    Logger.info('Backend can now perform passwordless SCP to this device');
  }

  async setupSSHAccess(backendUrl: string): Promise<void> {
    try {
      const keyData = await this.fetchPublicKey(backendUrl);
      this.installPublicKey(keyData.public_key, keyData.comment);
    } catch (error: any) {
      throw new Error(`SSH setup failed: ${error.message}`);
    }
  }

  removeInstalledKeys(): number {
    if (!fs.existsSync(AUTHORIZED_KEYS_PATH)) {
      return 0;
    }

    const authorizedKeys = fs.readFileSync(AUTHORIZED_KEYS_PATH, 'utf-8');
    const lines = authorizedKeys.split('\n');
    
    const filteredLines = lines.filter(line => !line.includes(TOWER_MARKER));
    
    const removedCount = lines.length - filteredLines.length;
    
    if (removedCount > 0) {
      fs.writeFileSync(AUTHORIZED_KEYS_PATH, filteredLines.join('\n'), { mode: 0o600 });
      Logger.success(`Removed ${removedCount} Tower SSH key(s) from authorized_keys`);
    }
    
    return removedCount;
  }
}

export const sshSetup = new SSHSetup();
