import chalk from 'chalk';

export interface CommandInfo {
  command: string;
  description: string;
  subcommands?: CommandInfo[];
}

export class HelpFormatter {
  private commands: CommandInfo[] = [];

  addCommand(command: string, description: string, subcommands?: CommandInfo[]): void {
    this.commands.push({ command, description, subcommands });
  }

  display(): void {
    console.log();
    console.log(chalk.dim('> tower'));
    console.log();

    this.commands.forEach(cmd => {
      const commandText = chalk.green(cmd.command);
      const descText = chalk.gray(cmd.description);

      // Calculate padding for alignment
      const padding = ' '.repeat(Math.max(0, 35 - cmd.command.length));

      console.log(`  ${commandText}${padding}${descText}`);

      // Show subcommands if they exist
      if (cmd.subcommands && cmd.subcommands.length > 0) {
        cmd.subcommands.forEach(sub => {
          const fullCommand = `${cmd.command} ${sub.command}`;
          const subCommandText = chalk.green(fullCommand);
          const subPadding = ' '.repeat(Math.max(0, 35 - fullCommand.length));
          console.log(`  ${subCommandText}${subPadding}${chalk.gray(sub.description)}`);
        });
      }
    });

    console.log();
  }

  displayCommandHelp(commandName: string, subcommands: CommandInfo[]): void {
    console.log();
    console.log(chalk.dim(`> tower ${commandName}`));
    console.log();

    subcommands.forEach(sub => {
      const fullCommand = `tower ${commandName} ${sub.command}`;
      const commandText = chalk.green(fullCommand);
      const padding = ' '.repeat(Math.max(0, 45 - fullCommand.length));

      console.log(`  ${commandText}${padding}${chalk.gray(sub.description)}`);
    });

    console.log();
  }
}

export function showMainHelp(): void {
  const help = new HelpFormatter();

  // Watch commands
  help.addCommand('tower watch add <path>', 'Add file or directory to watch list');
  help.addCommand('tower watch remove <path>', 'Remove from watch list');
  help.addCommand('tower watch list', 'List all watched items');
  help.addCommand('tower watch clear', 'Clear all watched items');

  console.log();

  // Search
  help.addCommand('tower search <query>', 'Search for files in watch list');

  console.log();

  // Sync commands
  help.addCommand('tower sync', 'Manually trigger sync');
  help.addCommand('tower sync status', 'Show current sync status');
  help.addCommand('tower sync history', 'Show sync history');
  help.addCommand('tower sync pause', 'Pause automatic syncing');
  help.addCommand('tower sync resume', 'Resume automatic syncing');

  console.log();

  // Device commands
  help.addCommand('tower devices list', 'List all connected devices');
  help.addCommand('tower devices add', 'Add a new device');
  help.addCommand('tower devices remove <id>', 'Remove a device');
  help.addCommand('tower devices rename <id> <name>', 'Rename a device');

  console.log();

  // Config commands
  help.addCommand('tower config list', 'List all configuration settings');
  help.addCommand('tower config get <key>', 'Get a configuration value');
  help.addCommand('tower config set <key> <value>', 'Set a configuration value');
  help.addCommand('tower config reset', 'Reset configuration to defaults');

  console.log();

  // General commands
  help.addCommand('tower init', 'Initialize Tower with setup wizard');
  help.addCommand('tower status', 'Show overall status');
  help.addCommand('tower help', 'Show this help message');

  help.display();
}

export function showWatchHelp(): void {
  console.log();
  console.log(chalk.dim('> tower watch'));
  console.log();

  const commands = [
    { command: 'tower watch add <path>', description: 'Add file or directory to watch list' },
    { command: 'tower watch add <path> -r', description: 'Add directory recursively' },
    { command: 'tower watch add <path> --tags <tags>', description: 'Add with tags' },
    { command: 'tower watch add <path> --exclude <patterns>', description: 'Add with exclusions' },
    { command: 'tower watch remove <path>', description: 'Remove from watch list' },
    { command: 'tower watch list', description: 'List all watched items' },
    { command: 'tower watch list --tags <tag>', description: 'Filter by tags' },
    { command: 'tower watch list --sort <field>', description: 'Sort by field (name|modified)' },
    { command: 'tower watch clear', description: 'Clear all watched items' },
  ];

  commands.forEach(cmd => {
    const commandText = chalk.green(cmd.command);
    const padding = ' '.repeat(Math.max(0, 50 - cmd.command.length));
    console.log(`  ${commandText}${padding}${chalk.gray(cmd.description)}`);
  });

  console.log();
}

export function showSyncHelp(): void {
  console.log();
  console.log(chalk.dim('> tower sync'));
  console.log();

  const commands = [
    { command: 'tower sync', description: 'Manually trigger sync' },
    { command: 'tower sync --force', description: 'Force sync even if no changes' },
    { command: 'tower sync --dry-run', description: 'Show what would be synced' },
    { command: 'tower sync status', description: 'Show current sync status' },
    { command: 'tower sync history [n]', description: 'Show sync history (last n items)' },
    { command: 'tower sync pause', description: 'Pause automatic syncing' },
    { command: 'tower sync resume', description: 'Resume automatic syncing' },
  ];

  commands.forEach(cmd => {
    const commandText = chalk.green(cmd.command);
    const padding = ' '.repeat(Math.max(0, 45 - cmd.command.length));
    console.log(`  ${commandText}${padding}${chalk.gray(cmd.description)}`);
  });

  console.log();
}

export function showDevicesHelp(): void {
  console.log();
  console.log(chalk.dim('> tower devices'));
  console.log();

  const commands = [
    { command: 'tower devices list', description: 'List all connected devices' },
    { command: 'tower devices add', description: 'Add a new device (interactive)' },
    { command: 'tower devices remove <device-id>', description: 'Remove a device' },
    { command: 'tower devices rename <device-id> <name>', description: 'Rename a device' },
  ];

  commands.forEach(cmd => {
    const commandText = chalk.green(cmd.command);
    const padding = ' '.repeat(Math.max(0, 50 - cmd.command.length));
    console.log(`  ${commandText}${padding}${chalk.gray(cmd.description)}`);
  });

  console.log();
}

export function showConfigHelp(): void {
  console.log();
  console.log(chalk.dim('> tower config'));
  console.log();

  const commands = [
    { command: 'tower config list', description: 'List all configuration settings' },
    { command: 'tower config get <key>', description: 'Get a configuration value' },
    { command: 'tower config set <key> <value>', description: 'Set a configuration value' },
    { command: 'tower config reset', description: 'Reset configuration to defaults' },
  ];

  commands.forEach(cmd => {
    const commandText = chalk.green(cmd.command);
    const padding = ' '.repeat(Math.max(0, 50 - cmd.command.length));
    console.log(`  ${commandText}${padding}${chalk.gray(cmd.description)}`);
  });

  console.log();
}

export function showSearchHelp(): void {
  console.log();
  console.log(chalk.dim('> tower search'));
  console.log();

  const commands = [
    { command: 'tower search <query>', description: 'Search for files in watch list' },
    { command: 'tower search <query> --name', description: 'Search by filename only' },
    { command: 'tower search <query> --content', description: 'Search file contents' },
    { command: 'tower search <query> --tags <tags>', description: 'Filter by tags' },
    { command: 'tower search <query> --type <ext>', description: 'Filter by file type' },
  ];

  commands.forEach(cmd => {
    const commandText = chalk.green(cmd.command);
    const padding = ' '.repeat(Math.max(0, 50 - cmd.command.length));
    console.log(`  ${commandText}${padding}${chalk.gray(cmd.description)}`);
  });

  console.log();
}
