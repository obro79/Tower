import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import Table from 'cli-table3';
import inquirer from 'inquirer';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { WatchedItem } from '../types';
import { apiClient } from '../utils/api-client';
import { globSync } from 'glob';
import { init } from './init';

const configManager = new ConfigManager();

export async function addWatch(filePath: string): Promise<void> {
  try {
    if (!configManager.isInitialized()) {
      await init();
      if (!configManager.isInitialized()) {
        return;
      }
    }

    const absolutePath = path.resolve(filePath);

    if (!fs.existsSync(absolutePath)) {
      Logger.error(`Path does not exist: ${filePath}`);
      return;
    }

    const watchList = configManager.getWatchList();
    if (watchList.some(item => item.path === absolutePath)) {
      Logger.warning(`Already watching: ${filePath}`);
      return;
    }

    const watchedItem: WatchedItem = {
      path: absolutePath,
      addedAt: new Date().toISOString()
    };

    configManager.addWatch(watchedItem);
    Logger.success(`Added to watch list: ${filePath}`);

    await registerWithBackend(absolutePath);

  } catch (error: any) {
    Logger.error(`Failed to add watch: ${error.message}`);
  }
}

async function registerWithBackend(filePath: string): Promise<void> {
  try {
    const isBackendRunning = await apiClient.healthCheck();
    if (!isBackendRunning) {
      Logger.warning('Backend server not running - files not registered for sync');
      Logger.info('Files will sync when daemon starts and backend is available');
      return;
    }

    const stats = fs.statSync(filePath);

    if (stats.isFile()) {
      const metadata = apiClient.getLocalFileMetadata(filePath);
      const response = await apiClient.registerFile(metadata);
      Logger.success(`Registered with backend: ${response.file_name} (ID: ${response.file_id})`);
    } else if (stats.isDirectory()) {
      const globPattern = path.join(filePath, '**/*');
      const files = globSync(globPattern, { nodir: true });
      
      let registered = 0;
      for (const file of files) {
        try {
          const metadata = apiClient.getLocalFileMetadata(file);
          await apiClient.registerFile(metadata);
          registered++;
        } catch (err: any) {
          Logger.warning(`Failed to register ${file}: ${err.message}`);
        }
      }
      
      Logger.success(`Registered ${registered} file(s) from directory with backend`);
    }
  } catch (error: any) {
    Logger.warning(`Backend registration failed: ${error.message}`);
    Logger.info('Files added to watch list but not synced to backend');
  }
}

export async function removeWatch(filePath: string): Promise<void> {
  try {
    if (!configManager.isInitialized()) {
      await init();
      if (!configManager.isInitialized()) {
        return;
      }
    }

    const absolutePath = path.resolve(filePath);
    const removed = configManager.removeWatch(absolutePath);

    if (!removed) {
      Logger.error(`Not in watch list: ${filePath}`);
      return;
    }

    Logger.success(`Removed from watch list: ${filePath}`);

    await deleteFromBackend(absolutePath);

  } catch (error: any) {
    Logger.error(`Failed to remove watch: ${error.message}`);
  }
}

async function deleteFromBackend(filePath: string): Promise<void> {
  try {
    const isBackendRunning = await apiClient.healthCheck();
    if (!isBackendRunning) {
      Logger.warning('Backend server not running - files not deleted from registry');
      return;
    }

    const stats = fs.existsSync(filePath) ? fs.statSync(filePath) : null;

    if (stats && stats.isFile()) {
      await apiClient.deleteFileByPath(filePath);
      Logger.success('Removed file from backend registry');
    } else if (stats && stats.isDirectory()) {
      const globPattern = path.join(filePath, '**/*');
      const files = globSync(globPattern, { nodir: true });
      
      let deleted = 0;
      for (const file of files) {
        try {
          await apiClient.deleteFileByPath(file);
          deleted++;
        } catch (err: any) {
          Logger.warning(`Failed to delete ${file}: ${err.message}`);
        }
      }
      
      Logger.success(`Removed ${deleted} file(s) from backend registry`);
    } else {
      await apiClient.deleteFileByPath(filePath);
      Logger.success('Removed from backend registry');
    }
  } catch (error: any) {
    Logger.warning(`Backend deletion failed: ${error.message}`);
  }
}

export function listWatch(): void {
  try {
    const watchList = configManager.getWatchList();

    if (watchList.length === 0) {
      Logger.info('No items in watch list');
      return;
    }

    const table = new Table({
      head: [
        chalk.cyan('Path'),
        chalk.cyan('Type'),
        chalk.cyan('Added')
      ],
      colWidths: [60, 12, 25]
    });

    watchList.forEach(item => {
      const exists = fs.existsSync(item.path);
      const type = exists 
        ? (fs.statSync(item.path).isDirectory() ? 'Directory' : 'File')
        : 'Missing';
      const added = new Date(item.addedAt).toLocaleString();

      table.push([
        exists ? item.path : chalk.red(item.path),
        type,
        added
      ]);
    });

    console.log(table.toString());
    Logger.info(`Total: ${watchList.length} item(s)`);
  } catch (error: any) {
    Logger.error(`Failed to list watches: ${error.message}`);
  }
}


