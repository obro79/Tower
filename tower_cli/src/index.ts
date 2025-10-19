#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import inquirer from 'inquirer';
import { init } from './commands/init';
import { addWatch, removeWatch, listWatch } from './commands/watch';
import { search } from './commands/search';
import { get } from './commands/get';
import { getRemote } from './commands/get-remote';
import { ConfigManager } from './utils/config';
import { displayLogo } from './utils/logo';

// Display logo on every run
displayLogo();

const program = new Command();
const configManager = new ConfigManager();

// Configure custom help formatting with purple commands and dimmed descriptions
const purple = chalk.rgb(135, 95, 215);
program.configureHelp({
  subcommandTerm: (cmd) => purple(cmd.name()),
  commandUsage: (cmd) => purple(cmd.name()) + ' ' + cmd.usage(),
  subcommandDescription: (cmd) => chalk.dim(cmd.description()),
  optionTerm: (option) => purple(option.flags),
  optionDescription: (option) => chalk.dim(option.description),
});

/**
 * Show interactive menu for command selection
 */
async function showInteractiveMenu(): Promise<void> {
  const choices = [
    { name: purple('init') + chalk.dim(' - Initialize Tower configuration'), value: 'init' },
    { name: purple('watch') + chalk.dim(' - Add a file or directory to watch list'), value: 'watch' },
    { name: purple('watch-list') + chalk.dim(' - List all watched items'), value: 'watch-list' },
    { name: purple('search') + chalk.dim(' - Search for files across all devices'), value: 'search' },
    { name: purple('get') + chalk.dim(' - Download a file from network'), value: 'get' },
    { name: purple('get-remote') + chalk.dim(' - List all files in backend registry'), value: 'get-remote' },
    { name: chalk.gray('Exit'), value: 'exit' },
  ];

  const { command } = await inquirer.prompt([
    {
      type: 'list',
      name: 'command',
      message: purple('Select a command:'),
      choices,
    },
  ]);

  // Handle the selected command
  switch (command) {
    case 'init':
      await init();
      break;

    case 'watch':
      const { watchPath } = await inquirer.prompt([
        {
          type: 'input',
          name: 'watchPath',
          message: purple('Enter file or directory path to watch:'),
        },
      ]);
      if (watchPath) {
        await addWatch(watchPath);
      }
      break;

    case 'watch-list':
      if (!configManager.isInitialized()) {
        await init();
        if (!configManager.isInitialized()) {
          return;
        }
      }
      listWatch();
      break;

    case 'search':
      const { query } = await inquirer.prompt([
        {
          type: 'input',
          name: 'query',
          message: purple('Enter search query:'),
        },
      ]);
      if (query) {
        await search(query);
      }
      break;

    case 'get':
      const { filename } = await inquirer.prompt([
        {
          type: 'input',
          name: 'filename',
          message: purple('Enter filename (leave empty to see all files):'),
        },
      ]);
      const { destination } = await inquirer.prompt([
        {
          type: 'input',
          name: 'destination',
          message: purple('Enter destination path (leave empty for current directory):'),
        },
      ]);
      await get(filename || undefined, destination || undefined);
      break;

    case 'get-remote':
      if (!configManager.isInitialized()) {
        await init();
        if (!configManager.isInitialized()) {
          return;
        }
      }
      await getRemote();
      break;

    case 'exit':
      console.log(chalk.dim('Goodbye!'));
      process.exit(0);
      break;
  }
}

program
  .name('tower')
  .description('Cross-device file sync and discovery')
  .version('0.1.0')
  .showHelpAfterError(false)
  .exitOverride();

program
  .command('init')
  .description('Initialize Tower configuration')
  .action(async () => {
    await init();
  });

program
  .command('watch <path>')
  .description('Add a file or directory to watch list')
  .option('--remove', 'Remove from watch list')
  .option('--list', 'List all watched items')
  .action(async (path, options) => {
    if (options.list) {
      listWatch();
    } else if (options.remove) {
      await removeWatch(path);
    } else {
      await addWatch(path);
    }
  });

program
  .command('watch-list')
  .description('List all watched items')
  .action(async () => {
    if (!configManager.isInitialized()) {
      await init();
      if (!configManager.isInitialized()) {
        return;
      }
    }
    listWatch();
  });

program
  .command('search <query>')
  .description('Search for files across all devices')
  .action(async (query) => {
    await search(query);
  });

program
  .command('get [filename]')
  .description('Download a file from network')
  .option('-d, --destination <path>', 'Destination path')
  .action(async (filename, options) => {
    await get(filename, options.destination);
  });

program
  .command('get-remote')
  .description('List all files in backend registry (coming soon)')
  .action(async () => {
    if (!configManager.isInitialized()) {
      await init();
      if (!configManager.isInitialized()) {
        return;
      }
    }
    await getRemote();
  });

// If no command provided, check if initialized and show interactive menu
(async () => {
  if (process.argv.length <= 2) {
    if (!configManager.isInitialized()) {
      await init();
      process.exit(0);
    } else {
      // Show interactive menu when no command is provided
      await showInteractiveMenu();
      process.exit(0);
    }
  } else {
    program.parse(process.argv);
  }
})();
