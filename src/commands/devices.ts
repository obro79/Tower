import chalk from 'chalk';
import Table from 'cli-table3';
import inquirer from 'inquirer';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { Device } from '../types';

const configManager = new ConfigManager();

export function listDevices(): void {
  try {
    const devices = configManager.getDevices();

    if (devices.length === 0) {
      Logger.info('No devices configured');
      Logger.dim('Add a device with: tower devices add');
      return;
    }

    const table = new Table({
      head: [
        chalk.cyan('ID'),
        chalk.cyan('Name'),
        chalk.cyan('Status'),
        chalk.cyan('Added'),
        chalk.cyan('Last Seen')
      ],
      colWidths: [15, 25, 12, 20, 25]
    });

    devices.forEach(device => {
      const statusColor = device.status === 'online' ? chalk.green :
                         device.status === 'syncing' ? chalk.yellow :
                         chalk.gray;

      table.push([
        device.id,
        device.name,
        statusColor(device.status),
        new Date(device.addedAt).toLocaleDateString(),
        device.lastSeen ? new Date(device.lastSeen).toLocaleString() : 'Never'
      ]);
    });

    console.log(table.toString());
    Logger.info(`Total: ${devices.length} device(s)`);
  } catch (error: any) {
    Logger.error(`Failed to list devices: ${error.message}`);
  }
}

export async function addDevice(): Promise<void> {
  try {
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'name',
        message: 'Device name:',
        validate: (input) => input.length > 0 || 'Name is required'
      },
      {
        type: 'input',
        name: 'id',
        message: 'Device ID (leave blank to generate):',
        default: () => generateDeviceId()
      }
    ]);

    const device: Device = {
      id: answers.id,
      name: answers.name,
      addedAt: new Date().toISOString(),
      status: 'offline'
    };

    configManager.addDevice(device);
    Logger.success(`Device added: ${device.name} (${device.id})`);
  } catch (error: any) {
    if (error.isTtyError || error.name === 'ExitPromptError') {
      Logger.info('Operation cancelled');
    } else {
      Logger.error(`Failed to add device: ${error.message}`);
    }
  }
}

export async function removeDevice(deviceId: string): Promise<void> {
  try {
    const devices = configManager.getDevices();
    const device = devices.find(d => d.id === deviceId);

    if (!device) {
      Logger.error(`Device not found: ${deviceId}`);
      return;
    }

    const { confirm } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'confirm',
        message: `Remove device "${device.name}"?`,
        default: false
      }
    ]);

    if (confirm) {
      configManager.removeDevice(deviceId);
      Logger.success(`Device removed: ${device.name}`);
    } else {
      Logger.info('Operation cancelled');
    }
  } catch (error: any) {
    Logger.error(`Failed to remove device: ${error.message}`);
  }
}

export async function renameDevice(deviceId: string, newName: string): Promise<void> {
  try {
    const updated = configManager.updateDevice(deviceId, { name: newName });

    if (updated) {
      Logger.success(`Device renamed to: ${newName}`);
    } else {
      Logger.error(`Device not found: ${deviceId}`);
    }
  } catch (error: any) {
    Logger.error(`Failed to rename device: ${error.message}`);
  }
}

function generateDeviceId(): string {
  return `dev_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
