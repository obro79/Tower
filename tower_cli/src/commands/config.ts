import chalk from 'chalk';
import Table from 'cli-table3';
import inquirer from 'inquirer';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';

const configManager = new ConfigManager();

export function getConfig(key: string): void {
  try {
    const value = configManager.getSetting(key);

    if (value !== undefined) {
      console.log(`${chalk.bold(key)}:`, value);
    } else {
      Logger.error(`Setting not found: ${key}`);
    }
  } catch (error: any) {
    Logger.error(`Failed to get config: ${error.message}`);
  }
}

export async function setConfig(key: string, value: string): Promise<void> {
  try {
    // Parse value if it's a boolean or number
    let parsedValue: any = value;

    if (value === 'true') parsedValue = true;
    else if (value === 'false') parsedValue = false;
    else if (!isNaN(Number(value))) parsedValue = Number(value);

    configManager.setSetting(key, parsedValue);
    Logger.success(`Set ${key} = ${parsedValue}`);
  } catch (error: any) {
    Logger.error(`Failed to set config: ${error.message}`);
  }
}

export function listConfig(): void {
  try {
    const settings = configManager.getAllSettings();

    const table = new Table({
      head: [chalk.cyan('Setting'), chalk.cyan('Value')],
      colWidths: [30, 30]
    });

    Object.entries(settings).forEach(([key, value]) => {
      let displayValue: string;

      if (Array.isArray(value)) {
        displayValue = value.join(', ');
      } else if (typeof value === 'object') {
        displayValue = JSON.stringify(value);
      } else {
        displayValue = String(value);
      }

      table.push([key, displayValue]);
    });

    console.log(table.toString());
  } catch (error: any) {
    Logger.error(`Failed to list config: ${error.message}`);
  }
}

export async function resetConfig(): Promise<void> {
  try {
    const { confirm } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'confirm',
        message: 'Are you sure you want to reset all settings to defaults?',
        default: false
      }
    ]);

    if (confirm) {
      configManager.reset();
      Logger.success('Configuration reset to defaults');
    } else {
      Logger.info('Operation cancelled');
    }
  } catch (error: any) {
    Logger.error(`Failed to reset config: ${error.message}`);
  }
}
