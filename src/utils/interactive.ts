import inquirer from 'inquirer';
import autocomplete from 'inquirer-autocomplete-prompt';
import Fuse from 'fuse.js';
import chalk from 'chalk';
import { showTowerArt } from './help';

inquirer.registerPrompt('autocomplete', autocomplete);

interface Command {
  name: string;
  value: string;
  description: string;
}

const commands: Command[] = [
  // Watch commands
  { name: 'tower watch add <path>', value: 'watch-add', description: 'Add file or directory to watch list' },
  { name: 'tower watch remove <path>', value: 'watch-remove', description: 'Remove from watch list' },
  { name: 'tower watch list', value: 'watch-list', description: 'List all watched items' },
  { name: 'tower watch clear', value: 'watch-clear', description: 'Clear all watched items' },

  // Search
  { name: 'tower search <query>', value: 'search', description: 'Search for files in watch list' },

  // Sync commands
  { name: 'tower sync', value: 'sync', description: 'Manually trigger sync' },
  { name: 'tower sync status', value: 'sync-status', description: 'Show current sync status' },
  { name: 'tower sync history', value: 'sync-history', description: 'Show sync history' },
  { name: 'tower sync pause', value: 'sync-pause', description: 'Pause automatic syncing' },
  { name: 'tower sync resume', value: 'sync-resume', description: 'Resume automatic syncing' },

  // Device commands
  { name: 'tower devices list', value: 'devices-list', description: 'List all connected devices' },
  { name: 'tower devices add', value: 'devices-add', description: 'Add a new device' },
  { name: 'tower devices remove <id>', value: 'devices-remove', description: 'Remove a device' },
  { name: 'tower devices rename <id> <name>', value: 'devices-rename', description: 'Rename a device' },

  // Config commands
  { name: 'tower config list', value: 'config-list', description: 'List all configuration settings' },
  { name: 'tower config get <key>', value: 'config-get', description: 'Get a configuration value' },
  { name: 'tower config set <key> <value>', value: 'config-set', description: 'Set a configuration value' },
  { name: 'tower config reset', value: 'config-reset', description: 'Reset configuration to defaults' },

  // General
  { name: 'tower init', value: 'init', description: 'Initialize Tower with setup wizard' },
  { name: 'tower status', value: 'status', description: 'Show overall status' },
  { name: 'tower download <file-id>', value: 'download', description: 'Download file from remote device' },
  { name: 'tower help', value: 'help', description: 'Show all commands' },
];

const fuse = new Fuse(commands, {
  keys: ['name', 'description'],
  threshold: 0.4,
});

function formatChoice(cmd: Command): string {
  const commandPart = chalk.green(cmd.name);
  const padding = ' '.repeat(Math.max(0, 40 - cmd.name.length));
  const descPart = chalk.gray(cmd.description);
  return `${commandPart}${padding}${descPart}`;
}

function searchCommands(answers: any, input: string = ''): Promise<any[]> {
  return new Promise((resolve) => {
    if (!input || input.trim() === '') {
      // Show all commands
      const choices = commands.map(cmd => ({
        name: formatChoice(cmd),
        value: cmd.value,
        short: cmd.name
      }));
      resolve(choices);
    } else {
      // Fuzzy search
      const results = fuse.search(input);
      const choices = results.map(result => ({
        name: formatChoice(result.item),
        value: result.item.value,
        short: result.item.name
      }));
      resolve(choices.length > 0 ? choices : [
        { name: chalk.gray('No matches found'), value: '', short: '' }
      ]);
    }
  });
}

export async function showInteractivePicker(): Promise<string | null> {
  try {
    showTowerArt();
    console.log(chalk.dim('  Type to search, use arrow keys to navigate, Enter to select\n'));

    const answer = await inquirer.prompt([
      {
        type: 'autocomplete',
        name: 'command',
        message: 'Select a command:',
        source: searchCommands,
        pageSize: 10,
        loop: false,
      }
    ]);

    return answer.command || null;
  } catch (error) {
    // User cancelled (Ctrl+C)
    return null;
  }
}

export function executeCommand(commandValue: string): string[] {
  const commandMap: { [key: string]: string[] } = {
    'watch-add': ['watch', 'add'],
    'watch-remove': ['watch', 'remove'],
    'watch-list': ['watch', 'list'],
    'watch-clear': ['watch', 'clear'],
    'search': ['search'],
    'sync': ['sync'],
    'sync-status': ['sync', 'status'],
    'sync-history': ['sync', 'history'],
    'sync-pause': ['sync', 'pause'],
    'sync-resume': ['sync', 'resume'],
    'devices-list': ['devices', 'list'],
    'devices-add': ['devices', 'add'],
    'devices-remove': ['devices', 'remove'],
    'devices-rename': ['devices', 'rename'],
    'config-list': ['config', 'list'],
    'config-get': ['config', 'get'],
    'config-set': ['config', 'set'],
    'config-reset': ['config', 'reset'],
    'init': ['init'],
    'status': ['status'],
    'download': ['download'],
    'help': ['help'],
  };

  return commandMap[commandValue] || [];
}
