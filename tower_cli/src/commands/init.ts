import * as os from 'os';
import * as dns from 'dns';
import chalk from 'chalk';
import inquirer from 'inquirer';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { sshSetup } from '../utils/ssh-setup';

const configManager = new ConfigManager();

function getLocalIp(): Promise<string> {
  return new Promise((resolve) => {
    dns.lookup(os.hostname(), (err, address) => {
      if (err || !address) {
        resolve('127.0.0.1');
      } else {
        resolve(address);
      }
    });
  });
}

export async function init(): Promise<void> {
  console.log(chalk.bold.cyan('\nWelcome to Tower!\n'));
  console.log('Let\'s set up your file sync configuration.\n');

  try {
    const deviceName = os.hostname();
    const deviceUser = os.userInfo().username;
    const deviceIp = await getLocalIp();

    console.log(chalk.dim('Auto-detected device info:'));
    console.log(chalk.dim(`  Device: ${deviceName}`));
    console.log(chalk.dim(`  User: ${deviceUser}`));
    console.log(chalk.dim(`  IP: ${deviceIp}\n`));

    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'backendUrl',
        message: 'Backend API URL (e.g., http://192.168.1.10:8000):',
        validate: (input) => {
          if (!input) return 'Backend URL is required';
          if (!input.startsWith('http://') && !input.startsWith('https://')) {
            return 'URL must start with http:// or https://';
          }
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

    console.log();
    Logger.info('Setting up SSH access for passwordless file transfers...');
    
    try {
      await sshSetup.setupSSHAccess(answers.backendUrl);
      console.log();
    } catch (error: any) {
      Logger.warning(`SSH setup failed: ${error.message}`);
      Logger.warning('You may need to manually configure SSH keys for file transfers');
      console.log();
    }

    configManager.initialize(
      answers.backendUrl,
      answers.syncInterval,
      deviceName,
      deviceIp,
      deviceUser
    );

    Logger.success('Configuration saved!');
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
