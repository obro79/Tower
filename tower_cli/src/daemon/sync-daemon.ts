import * as fs from 'fs';
import * as path from 'path';
import { globSync } from 'glob';
import { ConfigManager } from '../utils/config';
import { apiClient } from '../utils/api-client';
import { Logger } from '../utils/logger';

interface FileState {
  path: string;
  mtime: number;
  size: number;
}

export class SyncDaemon {
  private configManager: ConfigManager;
  private fileStates: Map<string, FileState> = new Map();
  private intervalId: NodeJS.Timeout | null = null;
  private isRunning: boolean = false;

  constructor() {
    this.configManager = new ConfigManager();
  }

  async start(): Promise<void> {
    if (!this.configManager.isInitialized()) {
      Logger.error('Tower not initialized. Run "tower init" first.');
      return;
    }

    const config = this.configManager.getConfig();
    const intervalMs = config.syncInterval * 60 * 1000;

    Logger.info(`Starting sync daemon (interval: ${config.syncInterval} minutes)`);
    
    this.isRunning = true;
    await this.syncOnce();

    this.intervalId = setInterval(async () => {
      await this.syncOnce();
    }, intervalMs);

    Logger.success('Sync daemon started');
  }

  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isRunning = false;
    Logger.info('Sync daemon stopped');
  }

  private async syncOnce(): Promise<void> {
    try {
      const isBackendRunning = await apiClient.healthCheck();
      if (!isBackendRunning) {
        Logger.warning('Backend not running - skipping sync');
        return;
      }

      const watchList = this.configManager.getWatchList();
      
      for (const item of watchList) {
        await this.syncPath(item.path);
      }

    } catch (error: any) {
      Logger.error(`Sync failed: ${error.message}`);
    }
  }

  private async syncPath(watchedPath: string): Promise<void> {
    if (!fs.existsSync(watchedPath)) {
      await this.handleDeletedPath(watchedPath);
      return;
    }

    const stats = fs.statSync(watchedPath);

    if (stats.isFile()) {
      await this.syncFile(watchedPath);
    } else if (stats.isDirectory()) {
      await this.syncDirectory(watchedPath);
    }
  }

  private async syncFile(filePath: string): Promise<void> {
    const stats = fs.statSync(filePath);
    const currentState: FileState = {
      path: filePath,
      mtime: stats.mtimeMs,
      size: stats.size
    };

    const previousState = this.fileStates.get(filePath);

    if (!previousState || 
        previousState.mtime !== currentState.mtime ||
        previousState.size !== currentState.size) {
      
      try {
        const metadata = apiClient.getLocalFileMetadata(filePath);
        await apiClient.registerFile(metadata);
        this.fileStates.set(filePath, currentState);
      } catch (error: any) {
        Logger.warning(`Failed to sync ${filePath}: ${error.message}`);
      }
    }
  }

  private async syncDirectory(dirPath: string): Promise<void> {
    const globPattern = path.join(dirPath, '**/*');
    const files = globSync(globPattern, { nodir: true });

    for (const file of files) {
      await this.syncFile(file);
    }

    this.cleanupDeletedFiles(dirPath, files);
  }

  private async handleDeletedPath(watchedPath: string): Promise<void> {
    const keysToDelete: string[] = [];
    
    for (const [filePath] of this.fileStates) {
      if (filePath === watchedPath || filePath.startsWith(watchedPath + path.sep)) {
        keysToDelete.push(filePath);
      }
    }

    for (const filePath of keysToDelete) {
      try {
        await apiClient.deleteFileByPath(filePath);
        this.fileStates.delete(filePath);
      } catch (error: any) {
        Logger.warning(`Failed to delete ${filePath}: ${error.message}`);
      }
    }
  }

  private cleanupDeletedFiles(dirPath: string, currentFiles: string[]): void {
    const currentFileSet = new Set(currentFiles);
    const keysToDelete: string[] = [];

    for (const [filePath] of this.fileStates) {
      if (filePath.startsWith(dirPath + path.sep) && !currentFileSet.has(filePath)) {
        keysToDelete.push(filePath);
      }
    }

    for (const filePath of keysToDelete) {
      apiClient.deleteFileByPath(filePath).catch(err => {
        Logger.warning(`Failed to delete ${filePath}: ${err.message}`);
      });
      this.fileStates.delete(filePath);
    }
  }
}

if (require.main === module) {
  const daemon = new SyncDaemon();
  
  daemon.start();

  process.on('SIGINT', () => {
    Logger.info('Received SIGINT, shutting down...');
    daemon.stop();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    Logger.info('Received SIGTERM, shutting down...');
    daemon.stop();
    process.exit(0);
  });
}
