import chalk from 'chalk';
import inquirer from 'inquirer';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { Device } from '../types';

const configManager = new ConfigManager();

export async function init(): Promise<void> {
  console.log(chalk.bold.cyan('\nWelcome to Tower!\n'));
  console.log('Let\'s set up your file sync configuration.\n');

  try {
    const answers = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'autoSync',
        message: 'Enable automatic syncing?',
        default: true
      },
      {
        type: 'number',
        name: 'syncInterval',
        message: 'Sync interval (minutes):',
        default: 5,
        validate: (input) => input > 0 || 'Must be greater than 0'
      },
      {
        type: 'list',
        name: 'conflictResolution',
        message: 'How should conflicts be handled?',
        choices: [
          { name: 'Use latest version', value: 'latest' },
          { name: 'Manual resolution', value: 'manual' },
          { name: 'Keep both versions', value: 'keep-both' }
        ],
        default: 'latest'
      },
      {
        type: 'confirm',
        name: 'addDevice',
        message: 'Would you like to add this device now?',
        default: true
      }
    ]);

    // Update settings
    configManager.setSetting('autoSync', answers.autoSync);
    configManager.setSetting('syncInterval', answers.syncInterval);
    configManager.setSetting('conflictResolution', answers.conflictResolution);

    Logger.success('Settings configured');

    // Add device if requested
    if (answers.addDevice) {
      const deviceAnswers = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Device name:',
          default: require('os').hostname(),
          validate: (input) => input.length > 0 || 'Name is required'
        }
      ]);

      const device: Device = {
        id: `dev_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: deviceAnswers.name,
        addedAt: new Date().toISOString(),
        status: 'online'
      };

      configManager.addDevice(device);
      Logger.success(`Device added: ${device.name}`);
    }

    console.log();
    Logger.success('Tower is ready to use!');
    console.log();
    console.log(chalk.dim('Next steps:'));
    console.log(chalk.dim('  - Add files to watch: tower watch add <path>'));
    console.log(chalk.dim('  - Start syncing: tower sync'));
    console.log(chalk.dim('  - View status: tower status'));
    console.log();
  } catch (error: any) {
    if (error.isTtyError || error.name === 'ExitPromptError') {
      Logger.info('\nSetup cancelled');
    } else {
      Logger.error(`Setup failed: ${error.message}`);
    }
  }
}
