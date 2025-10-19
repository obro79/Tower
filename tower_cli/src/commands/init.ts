import * as os from 'os';
import chalk from 'chalk';
import inquirer from 'inquirer';
import axios from 'axios';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { sshSetup } from '../utils/ssh-setup';

const configManager = new ConfigManager();

async function getDeviceIpFromBackend(backendUrl: string): Promise<string> {
  try {
    const response = await axios.get(`${backendUrl}/client-info`, { timeout: 5000 });
    return response.data.ip;
  } catch (error: any) {
    Logger.warning('Could not auto-detect IP from backend, will prompt user');
    return '';
  }
}

export async function init(): Promise<void> {
  console.log(chalk.bold.cyan('\nWelcome to Tower!\n'));
  console.log('Let\'s set up your file sync configuration.\n');

  try {
    const deviceName = os.hostname();
    const deviceUser = os.userInfo().username;

    console.log(chalk.dim('Auto-detected device info:'));
    console.log(chalk.dim(`  Device: ${deviceName}`));
    console.log(chalk.dim(`  User: ${deviceUser}\n`));

    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'backendIp',
        message: 'Backend IP address (e.g., 192.168.1.10):',
        validate: (input) => {
          if (!input) return 'IP address is required';
          const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
          if (!ipv4Regex.test(input)) return 'Invalid IPv4 address';
          return true;
        }
      },
      {
        type: 'number',
        name: 'syncInterval',
        message: 'Auto-sync interval (minutes):',
        default: 5,
        validate: (input) => input > 0 || 'Must be greater than 0'
      }
    ]);

    const backendUrl = `http://${answers.backendIp}:8000`;

    console.log();
    Logger.info('Detecting device IP address from backend...');

    let deviceIp = await getDeviceIpFromBackend(backendUrl);
    
    if (!deviceIp || deviceIp === 'unknown') {
      Logger.warning('Auto-detection failed');
      const ipAnswer = await inquirer.prompt([
        {
          type: 'input',
          name: 'deviceIp',
          message: 'Enter this device\'s IP address:',
          validate: (input) => {
            if (!input) return 'IP address is required';
            const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
            if (!ipv4Regex.test(input)) return 'Invalid IPv4 address';
            return true;
          }
        }
      ]);
      deviceIp = ipAnswer.deviceIp;
    } else {
      Logger.success(`Detected IP: ${deviceIp}`);
    }

    console.log();
    Logger.info('Setting up SSH access for passwordless file transfers...');

    try {
      await sshSetup.setupSSHAccess(backendUrl);
      console.log();
    } catch (error: any) {
      Logger.warning(`SSH setup failed: ${error.message}`);
      Logger.warning('You may need to manually configure SSH keys for file transfers');
      console.log();
    }

    configManager.initialize(
      backendUrl,
      answers.syncInterval,
      deviceName,
      deviceIp,
      deviceUser
    );

    Logger.success('Configuration saved!');
    console.log();
    console.log(chalk.dim('Configuration summary:'));
    console.log(chalk.dim(`  Backend: ${backendUrl}`));
    console.log(chalk.dim(`  Device IP: ${deviceIp}`));
    console.log(chalk.dim(`  Username: ${deviceUser}`));
    console.log();
    console.log(chalk.dim('Next steps:'));
    console.log(chalk.dim('  - Add files to watch: tower watch <path>'));
    console.log(chalk.dim('  - Search for files: tower search <query>'));
    console.log(chalk.dim('  - Download files: tower get <filename>'));
    console.log();
  } catch (error: any) {
    if (error.isTtyError || error.name === 'ExitPromptError') {
      Logger.info('\nSetup cancelled');
    } else {
      Logger.error(`Setup failed: ${error.message}`);
    }
  }
}
