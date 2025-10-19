import chalk from 'chalk';
import Table from 'cli-table3';
import ora from 'ora';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { SyncHistory } from '../types';

const configManager = new ConfigManager();

export async function sync(options: { force?: boolean; dryRun?: boolean }): Promise<void> {
  const spinner = ora('Syncing files...').start();

  try {
    const watchList = configManager.getWatchList();
    const devices = configManager.getDevices();

    if (watchList.length === 0) {
      spinner.warn('No items in watch list');
      return;
    }

    if (devices.length === 0) {
      spinner.warn('No devices configured. Add devices with: tower devices add');
      return;
    }

    // Simulate sync operation
    await new Promise(resolve => setTimeout(resolve, 2000));

    if (options.dryRun) {
      spinner.succeed('Dry run completed');
      Logger.info(`Would sync ${watchList.length} items to ${devices.length} device(s)`);
      return;
    }

    const history: SyncHistory = {
      timestamp: new Date().toISOString(),
      filesChanged: Math.floor(Math.random() * 10), // Mock data
      status: 'success'
    };

    configManager.addSyncHistory(history);
    spinner.succeed(`Synced ${history.filesChanged} file(s) successfully`);
  } catch (error: any) {
    spinner.fail('Sync failed');
    Logger.error(error.message);

    const history: SyncHistory = {
      timestamp: new Date().toISOString(),
      filesChanged: 0,
      status: 'failed',
      details: error.message
    };
    configManager.addSyncHistory(history);
  }
}

export function syncStatus(): void {
  try {
    const config = configManager.getConfig();
    const watchList = config.watchList;
    const devices = config.devices;
    const settings = config.settings;

    Logger.header('Sync Status');
    console.log();

    console.log(chalk.bold('Watch List:'), `${watchList.length} item(s)`);
    console.log(chalk.bold('Devices:'), `${devices.length} device(s)`);
    console.log(chalk.bold('Auto Sync:'), settings.autoSync ? chalk.green('Enabled') : chalk.red('Disabled'));
    console.log(chalk.bold('Sync Interval:'), `${settings.syncInterval} minutes`);
    console.log();

    // Show device status
    if (devices.length > 0) {
      const table = new Table({
        head: [chalk.cyan('Device'), chalk.cyan('Status'), chalk.cyan('Last Seen')],
        colWidths: [30, 15, 25]
      });

      devices.forEach(device => {
        const statusColor = device.status === 'online' ? chalk.green : chalk.gray;
        const lastSeen = device.lastSeen
          ? new Date(device.lastSeen).toLocaleString()
          : 'Never';
        table.push([device.name, statusColor(device.status), lastSeen]);
      });

      console.log(table.toString());
    }

    // Show last sync
    const history = configManager.getSyncHistory(1);
    if (history.length > 0) {
      const last = history[0];
      console.log();
      console.log(chalk.bold('Last Sync:'));
      console.log('  Time:', new Date(last.timestamp).toLocaleString());
      console.log('  Files:', last.filesChanged);
      console.log('  Status:', last.status === 'success'
        ? chalk.green(last.status)
        : chalk.red(last.status)
      );
    }
  } catch (error: any) {
    Logger.error(`Failed to get status: ${error.message}`);
  }
}

export function syncHistory(limit: number = 10): void {
  try {
    const history = configManager.getSyncHistory(limit);

    if (history.length === 0) {
      Logger.info('No sync history');
      return;
    }

    const table = new Table({
      head: [
        chalk.cyan('Time'),
        chalk.cyan('Files'),
        chalk.cyan('Status'),
        chalk.cyan('Details')
      ],
      colWidths: [25, 10, 12, 30]
    });

    history.forEach(entry => {
      const time = new Date(entry.timestamp).toLocaleString();
      const statusColor = entry.status === 'success' ? chalk.green : chalk.red;

      table.push([
        time,
        entry.filesChanged.toString(),
        statusColor(entry.status),
        entry.details || '-'
      ]);
    });

    console.log(table.toString());
  } catch (error: any) {
    Logger.error(`Failed to get history: ${error.message}`);
  }
}

export function pauseSync(): void {
  try {
    configManager.setSetting('autoSync', false);
    Logger.success('Auto-sync paused');
  } catch (error: any) {
    Logger.error(`Failed to pause sync: ${error.message}`);
  }
}

export function resumeSync(): void {
  try {
    configManager.setSetting('autoSync', true);
    Logger.success('Auto-sync resumed');
  } catch (error: any) {
    Logger.error(`Failed to resume sync: ${error.message}`);
  }
}
