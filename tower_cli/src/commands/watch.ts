import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import Table from 'cli-table3';
import inquirer from 'inquirer';
import fileTreeSelection from 'inquirer-file-tree-selection-prompt';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { WatchedItem, WatchOptions } from '../types';
import { apiClient } from '../utils/api-client';
import * as glob from 'glob';

// Register the file tree selection prompt
inquirer.registerPrompt('file-tree-selection', fileTreeSelection);

const configManager = new ConfigManager();

export async function addWatch(
  filePath: string,
  options: WatchOptions
): Promise<void> {
  try {
    // Resolve to absolute path
    const absolutePath = path.resolve(filePath);

    // Check if path exists
    if (!fs.existsSync(absolutePath)) {
      Logger.error(`Path does not exist: ${filePath}`);
      return;
    }

    // Check if already watching
    const watchList = configManager.getWatchList();
    if (watchList.some(item => item.path === absolutePath)) {
      Logger.warning(`Already watching: ${filePath}`);
      return;
    }

    // Get file stats
    const stats = fs.statSync(absolutePath);

    const watchedItem: WatchedItem = {
      path: absolutePath,
      recursive: options.recursive || false,
      exclude: options.exclude || [],
      tags: options.tags || [],
      addedAt: new Date().toISOString(),
      lastModified: stats.mtime.toISOString()
    };

    configManager.addWatch(watchedItem);
    Logger.success(`Added to watch list: ${filePath}`);

    if (stats.isDirectory() && options.recursive) {
      Logger.info(`Watching directory recursively`);
    }

    // Register file(s) with backend
    await registerWithBackend(absolutePath, options);

  } catch (error: any) {
    Logger.error(`Failed to add watch: ${error.message}`);
  }
}

/**
 * Register file(s) with the backend API
 */
async function registerWithBackend(
  filePath: string,
  options: WatchOptions
): Promise<void> {
  try {
    // Check if backend is available
    const isBackendRunning = await apiClient.healthCheck();
    if (!isBackendRunning) {
      Logger.warning('Backend server not running - files not registered for sync');
      Logger.info('Start backend with: cd backend && uvicorn main:app --reload');
      return;
    }

    const stats = fs.statSync(filePath);

    if (stats.isFile()) {
      // Register single file
      const metadata = apiClient.getLocalFileMetadata(filePath);
      const response = await apiClient.registerFile(metadata);
      Logger.success(`✓ Registered with backend: ${response.file_name} (ID: ${response.file_id})`);
    } else if (stats.isDirectory() && options.recursive) {
      // Register all files in directory recursively
      const excludePatterns = options.exclude || [];
      const globPattern = path.join(filePath, '**/*');

      glob.sync(globPattern, {
        nodir: true,  // Only files, not directories
        ignore: excludePatterns.map(pattern => path.join(filePath, '**', pattern))
      }).forEach(async (file) => {
        try {
          const metadata = apiClient.getLocalFileMetadata(file);
          await apiClient.registerFile(metadata);
        } catch (err: any) {
          Logger.warning(`Failed to register ${file}: ${err.message}`);
        }
      });

      Logger.success(`✓ Registered directory contents with backend`);
    }
  } catch (error: any) {
    Logger.warning(`Backend registration failed: ${error.message}`);
    Logger.info('Files added to watch list but not synced to backend');
  }
}

export async function removeWatch(filePath: string): Promise<void> {
  try {
    const absolutePath = path.resolve(filePath);
    const removed = configManager.removeWatch(absolutePath);

    if (removed) {
      Logger.success(`Removed from watch list: ${filePath}`);
    } else {
      Logger.error(`Not in watch list: ${filePath}`);
    }
  } catch (error: any) {
    Logger.error(`Failed to remove watch: ${error.message}`);
  }
}

export function listWatch(options?: { tags?: string; sort?: string; tree?: boolean }): void {
  try {
    let watchList = configManager.getWatchList();

    if (watchList.length === 0) {
      Logger.info('No items in watch list');
      return;
    }

    // Filter by tags if specified
    if (options?.tags) {
      const filterTags = options.tags.split(',').map(t => t.trim());
      watchList = watchList.filter(item =>
        item.tags.some(tag => filterTags.includes(tag))
      );
    }

    // Sort if specified
    if (options?.sort) {
      watchList.sort((a, b) => {
        switch (options.sort) {
          case 'name':
            return a.path.localeCompare(b.path);
          case 'modified':
            return (b.lastModified || '').localeCompare(a.lastModified || '');
          default:
            return 0;
        }
      });
    }

    // Use interactive tree view if --tree flag is set
    if (options?.tree) {
      listWatchInteractive(watchList);
      return;
    }

    // Create table (default view)
    const table = new Table({
      head: [
        chalk.cyan('Path'),
        chalk.cyan('Type'),
        chalk.cyan('Tags'),
        chalk.cyan('Added')
      ],
      colWidths: [50, 12, 20, 20]
    });

    watchList.forEach(item => {
      const type = item.recursive ? 'Dir (rec)' : fs.statSync(item.path).isDirectory() ? 'Directory' : 'File';
      const tags = item.tags.length > 0 ? item.tags.join(', ') : '-';
      const added = new Date(item.addedAt).toLocaleDateString();

      table.push([item.path, type, tags, added]);
    });

    console.log(table.toString());
    Logger.info(`Total: ${watchList.length} item(s)`);
  } catch (error: any) {
    Logger.error(`Failed to list watches: ${error.message}`);
  }
}

/**
 * Display watch list in an interactive tree view
 */
function listWatchInteractive(watchList: WatchedItem[]): void {
  console.log(chalk.hex('#af5fff').bold('\n📁 Tower Watch List - Interactive Tree View\n'));
  console.log(chalk.gray('Navigate: ↑/↓  Expand: → or Enter  Collapse: ← or Backspace  Exit: Esc\n'));

  // Build tree structure for each watched item
  watchList.forEach((item, index) => {
    const stats = fs.existsSync(item.path) ? fs.statSync(item.path) : null;

    if (!stats) {
      console.log(chalk.red(`✗ ${item.path} ${chalk.gray('(not found)')}`));
      return;
    }

    const isDir = stats.isDirectory();
    const icon = isDir ? '📁' : '📄';
    const tags = item.tags.length > 0 ? chalk.magenta(` [${item.tags.join(', ')}]`) : '';

    console.log(`${icon} ${chalk.cyan(item.path)}${tags}`);

    // If it's a directory and recursive, show the tree structure
    if (isDir && item.recursive) {
      displayDirectoryTree(item.path, item.exclude, '  ');
    }
  });

  console.log(chalk.gray(`\n📊 Total: ${watchList.length} watched item(s)\n`));
}

/**
 * Recursively display directory tree structure
 */
function displayDirectoryTree(
  dirPath: string,
  excludePatterns: string[],
  indent: string = '',
  maxDepth: number = 5,
  currentDepth: number = 0
): void {
  if (currentDepth >= maxDepth) {
    console.log(`${indent}${chalk.gray('...')}`);
    return;
  }

  try {
    const items = fs.readdirSync(dirPath);
    const filteredItems = items.filter(item => {
      // Skip excluded patterns
      return !excludePatterns.some(pattern => {
        if (pattern.includes('*')) {
          // Simple glob matching
          const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
          return regex.test(item);
        }
        return item === pattern || item.startsWith(pattern);
      });
    });

    filteredItems.forEach((item, index) => {
      const itemPath = path.join(dirPath, item);
      const isLast = index === filteredItems.length - 1;
      const prefix = isLast ? '└── ' : '├── ';
      const childIndent = isLast ? '    ' : '│   ';

      try {
        const stats = fs.statSync(itemPath);
        const isDir = stats.isDirectory();
        const icon = isDir ? '📁' : '📄';
        const size = isDir ? '' : chalk.gray(` (${formatBytes(stats.size)})`);

        console.log(`${indent}${prefix}${icon} ${chalk.white(item)}${size}`);

        // Recursively display subdirectories
        if (isDir) {
          displayDirectoryTree(itemPath, excludePatterns, indent + childIndent, maxDepth, currentDepth + 1);
        }
      } catch (err) {
        // Skip items we can't access
        console.log(`${indent}${prefix}${chalk.red('✗')} ${chalk.gray(item)} ${chalk.red('(access denied)')}`);
      }
    });
  } catch (err: any) {
    console.log(`${indent}${chalk.red('Error reading directory: ' + err.message)}`);
  }
}

/**
 * Format bytes into human-readable size
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export async function clearWatch(): Promise<void> {
  try {
    const watchList = configManager.getWatchList();

    if (watchList.length === 0) {
      Logger.info('Watch list is already empty');
      return;
    }

    const { confirm } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'confirm',
        message: `Are you sure you want to remove all ${watchList.length} watched items?`,
        default: false
      }
    ]);

    if (confirm) {
      configManager.clearWatchList();
      Logger.success('Watch list cleared');
    } else {
      Logger.info('Operation cancelled');
    }
  } catch (error: any) {
    Logger.error(`Failed to clear watch list: ${error.message}`);
  }
}
