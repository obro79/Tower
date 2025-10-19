/**
 * API Client for Tower CLI
 * Communicates with the FastAPI backend for file sync operations
 */

import axios, { AxiosInstance } from 'axios';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';

const execAsync = promisify(exec);

export interface FileMetadata {
  file_name: string;
  absolute_path: string;
  device: string;
  device_ip: string;
  device_user: string;
  last_modified_time: string;  // ISO format
  size: number;
  file_type: string;
}

export interface FileRecord extends FileMetadata {
  id: number;
  created_time: string;
}

export interface RegisterResponse {
  message: string;
  file_id: number;
  file_name: string;
  action: 'created' | 'updated';
}

export class TowerAPIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Check if backend server is running
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/');
      return response.data.status === 'File Sync API is running';
    } catch (error) {
      return false;
    }
  }

  /**
   * Register a file with the backend
   */
  async registerFile(metadata: FileMetadata): Promise<RegisterResponse> {
    try {
      const response = await this.client.post<RegisterResponse>('/files/register', metadata);
      return response.data;
    } catch (error: any) {
      if (error.response) {
        throw new Error(`Registration failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  /**
   * Search for files by name (supports wildcard *)
   */
  async searchFiles(query: string): Promise<FileRecord[]> {
    try {
      const response = await this.client.get<FileRecord[]>('/files/search', {
        params: { query },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return [];  // No files found
      }
      if (error.response) {
        throw new Error(`Search failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  /**
   * Get file metadata by ID
   */
  async getFile(fileId: number): Promise<FileRecord> {
    try {
      const response = await this.client.get<FileRecord>(`/files/${fileId}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(`File with ID ${fileId} not found`);
      }
      if (error.response) {
        throw new Error(`Get file failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  /**
   * Delete file metadata by ID
   */
  async deleteFile(fileId: number): Promise<void> {
    try {
      await this.client.delete(`/files/${fileId}`);
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(`File with ID ${fileId} not found`);
      }
      if (error.response) {
        throw new Error(`Delete failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  /**
   * Get local device information
   */
  getDeviceInfo(): { hostname: string; user: string; ip: string } {
    const hostname = os.hostname();
    const user = os.userInfo().username;

    // Get local IP address
    const networkInterfaces = os.networkInterfaces();
    let ip = '127.0.0.1';

    for (const [, interfaces] of Object.entries(networkInterfaces)) {
      if (!interfaces) continue;
      for (const iface of interfaces) {
        // Skip internal and non-IPv4 addresses
        if (iface.family === 'IPv4' && !iface.internal) {
          ip = iface.address;
          break;
        }
      }
      if (ip !== '127.0.0.1') break;
    }

    return { hostname, user, ip };
  }

  /**
   * Get file metadata from local filesystem
   */
  getLocalFileMetadata(filePath: string): FileMetadata {
    const absolutePath = path.resolve(filePath);
    const stats = fs.statSync(absolutePath);
    const fileName = path.basename(absolutePath);
    const fileType = path.extname(absolutePath) || '.unknown';

    const deviceInfo = this.getDeviceInfo();

    return {
      file_name: fileName,
      absolute_path: absolutePath,
      device: deviceInfo.hostname,
      device_ip: deviceInfo.ip,
      device_user: deviceInfo.user,
      last_modified_time: stats.mtime.toISOString(),
      size: stats.size,
      file_type: fileType,
    };
  }

  /**
   * Download a file from a remote device using SCP
   */
  async downloadFile(fileRecord: FileRecord, destinationPath: string): Promise<void> {
    const { device_user, device_ip, absolute_path, file_name } = fileRecord;

    // Determine destination
    const destination = destinationPath.endsWith('/')
      ? path.join(destinationPath, file_name)
      : destinationPath;

    // Check if this is a localhost download (same device)
    const currentDevice = this.getDeviceInfo();
    const isLocalhost = device_ip === currentDevice.ip ||
                        device_ip === '127.0.0.1' ||
                        device_ip.startsWith('10.') && currentDevice.ip.startsWith('10.');

    if (isLocalhost && fs.existsSync(absolute_path)) {
      // Local file copy instead of SCP
      try {
        fs.copyFileSync(absolute_path, destination);
        console.log(`File copied locally to: ${destination}`);
        return;
      } catch (error: any) {
        throw new Error(`Local file copy failed: ${error.message}`);
      }
    }

    // Build SCP command for remote devices
    const scpCommand = `scp ${device_user}@${device_ip}:"${absolute_path}" "${destination}"`;

    try {
      await execAsync(scpCommand);
      console.log(`File downloaded successfully to: ${destination}`);
    } catch (error: any) {
      throw new Error(`SCP transfer failed: ${error.message}`);
    }
  }
}

// Export singleton instance
export const apiClient = new TowerAPIClient();
