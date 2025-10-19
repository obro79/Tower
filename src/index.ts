#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { addWatch, removeWatch, listWatch, clearWatch } from './commands/watch';
import { search } from './commands/search';
import { sync, syncStatus, syncHistory, pauseSync, resumeSync } from './commands/sync';
import { listDevices, addDevice, removeDevice, renameDevice } from './commands/devices';
import { getConfig, setConfig, listConfig, resetConfig } from './commands/config';
import { init } from './commands/init';
import { ConfigManager } from './utils/config';
import { Logger } from './utils/logger';

const program = new Command();
const configManager = new ConfigManager();

program
  .name('tower')
  .description('A CLI tool to help you keep your files synced across devices')
  .version('0.1.0');

// Watch commands
const watchCmd = program
  .command('watch')
  .description('Manage watched files and directories');

watchCmd
  .command('add <path>')
  .description('Add a file or directory to the watch list')
  .option('-r, --recursive', 'Watch directory recursively')
  .option('-e, --exclude <patterns...>', 'Exclude patterns')
  .option('-t, --tags <tags...>', 'Add tags')
  .action(async (path, options) => {
    await addWatch(path, {
      recursive: options.recursive,
      exclude: options.exclude || [],
      tags: options.tags || []
    });
  });

watchCmd
  .command('remove <path>')
  .description('Remove a file or directory from the watch list')
  .action(async (path) => {
    await removeWatch(path);
  });

watchCmd
  .command('list')
  .description('List all watched items')
  .option('--tags <tags>', 'Filter by tags (comma-separated)')
  .option('--sort <field>', 'Sort by field (name|modified)')
  .action((options) => {
    listWatch(options);
  });

watchCmd
  .command('clear')
  .description('Remove all watched items')
  .action(async () => {
    await clearWatch();
  });

// Search command
program
  .command('search <query>')
  .description('Search for files in the watch list')
  .option('-n, --name', 'Search by filename only')
  .option('-c, --content', 'Search file contents')
  .option('--tags <tags>', 'Filter by tags (comma-separated)')
  .option('--type <extension>', 'Filter by file type (e.g., js, md)')
  .action((query, options) => {
    search(query, {
      name: options.name,
      content: options.content,
      tags: options.tags,
      type: options.type
    });
  });

// Sync commands
const syncCmd = program
  .command('sync')
  .description('Sync operations');

syncCmd
  .description('Manually trigger a sync')
  .option('-f, --force', 'Force sync even if no changes')
  .option('--dry-run', 'Show what would be synced without syncing')
  .action(async (options) => {
    await sync(options);
  });

syncCmd
  .command('status')
  .description('Show current sync status')
  .action(() => {
    syncStatus();
  });

syncCmd
  .command('history [n]')
  .description('Show sync history')
  .action((n) => {
    syncHistory(n ? parseInt(n) : 10);
  });

syncCmd
  .command('pause')
  .description('Pause automatic syncing')
  .action(() => {
    pauseSync();
  });

syncCmd
  .command('resume')
  .description('Resume automatic syncing')
  .action(() => {
    resumeSync();
  });

// Devices commands
const devicesCmd = program
  .command('devices')
  .description('Manage connected devices');

devicesCmd
  .command('list')
  .description('List all connected devices')
  .action(() => {
    listDevices();
  });

devicesCmd
  .command('add')
  .description('Add a new device')
  .action(async () => {
    await addDevice();
  });

devicesCmd
  .command('remove <device-id>')
  .description('Remove a device')
  .action(async (deviceId) => {
    await removeDevice(deviceId);
  });

devicesCmd
  .command('rename <device-id> <name>')
  .description('Rename a device')
  .action(async (deviceId, name) => {
    await renameDevice(deviceId, name);
  });

// Config commands
const configCmd = program
  .command('config')
  .description('Manage configuration');

configCmd
  .command('get <key>')
  .description('Get a configuration value')
  .action((key) => {
    getConfig(key);
  });

configCmd
  .command('set <key> <value>')
  .description('Set a configuration value')
  .action(async (key, value) => {
    await setConfig(key, value);
  });

configCmd
  .command('list')
  .description('List all configuration settings')
  .action(() => {
    listConfig();
  });

configCmd
  .command('reset')
  .description('Reset configuration to defaults')
  .action(async () => {
    await resetConfig();
  });

// Init command
program
  .command('init')
  .description('Initialize Tower with a setup wizard')
  .action(async () => {
    await init();
  });

// Status command
program
  .command('status')
  .description('Show overall status')
  .action(() => {
    syncStatus();
  });

// Error handling
program.exitOverride();

try {
  program.parse(process.argv);

  // Show help if no command provided
  if (process.argv.length === 2) {
    program.outputHelp();
  }
} catch (error: any) {
  if (error.code !== 'commander.help' && error.code !== 'commander.helpDisplayed') {
    Logger.error(error.message);
    process.exit(1);
  }
}
