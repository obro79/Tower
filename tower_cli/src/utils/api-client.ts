import axios, { AxiosInstance } from 'axios';
import { ConfigManager } from './config';
import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';

export interface FileMetadata {
  file_name: string;
  absolute_path: string;
  device: string;
  device_ip: string;
  device_user: string;
  last_modified_time: string;
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
  private client: AxiosInstance | null = null;
  private configManager: ConfigManager;

  constructor() {
    this.configManager = new ConfigManager();
  }

  private getClient(): AxiosInstance {
    if (!this.configManager.isInitialized()) {
      throw new Error('Tower not initialized. Run "tower init" first.');
    }

    const config = this.configManager.getConfig();
    
    if (!this.client) {
      this.client = axios.create({
        baseURL: config.backendUrl,
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }

    return this.client;
  }

  async healthCheck(): Promise<boolean> {
    try {
      if (!this.configManager.isInitialized()) {
        return false;
      }
      const client = this.getClient();
      const response = await client.get('/');
      return response.data.status === 'File Sync API is running';
    } catch (error) {
      return false;
    }
  }

  async registerFile(metadata: FileMetadata): Promise<RegisterResponse> {
    try {
      const client = this.getClient();
      const response = await client.post<RegisterResponse>('/files/register', metadata);
      return response.data;
    } catch (error: any) {
      if (error.response) {
        throw new Error(`Registration failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  async searchFiles(query: string): Promise<FileRecord[]> {
    try {
      const client = this.getClient();
      const response = await client.get<FileRecord[]>('/files/search', {
        params: { query },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return [];
      }
      if (error.response) {
        throw new Error(`Search failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  async deleteFileByPath(absolutePath: string): Promise<void> {
    try {
      const client = this.getClient();
      const results = await this.searchFiles(absolutePath);
      
      for (const file of results) {
        if (file.absolute_path === absolutePath) {
          await client.delete(`/files/${file.id}`);
        }
      }
    } catch (error: any) {
      if (error.response) {
        throw new Error(`Delete failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }

  getLocalFileMetadata(filePath: string): FileMetadata {
    if (!this.configManager.isInitialized()) {
      throw new Error('Tower not initialized. Run "tower init" first.');
    }

    const config = this.configManager.getConfig();
    const absolutePath = path.resolve(filePath);
    const stats = fs.statSync(absolutePath);
    const fileName = path.basename(absolutePath);
    const fileType = path.extname(absolutePath) || '.unknown';

    return {
      file_name: fileName,
      absolute_path: absolutePath,
      device: config.deviceName,
      device_ip: config.deviceIp,
      device_user: config.deviceUser,
      last_modified_time: stats.mtime.toISOString(),
      size: stats.size,
      file_type: fileType,
    };
  }

  async downloadFile(fileRecord: FileRecord, destinationPath: string): Promise<void> {
    const client = this.getClient();
    const config = this.configManager.getConfig();
    
    const destination = destinationPath.endsWith('/')
      ? path.join(destinationPath, fileRecord.file_name)
      : destinationPath;

    try {
      await client.get(`/files/${fileRecord.id}`, {
        params: {
          device_ip: config.deviceIp,
          destination_path: destination,
          device_user: config.deviceUser
        }
      });
    } catch (error: any) {
      if (error.response) {
        throw new Error(`Download failed: ${error.response.data.detail || error.response.statusText}`);
      }
      throw new Error(`Failed to connect to backend: ${error.message}`);
    }
  }
}

export const apiClient = new TowerAPIClient();
