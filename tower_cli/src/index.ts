#!/usr/bin/env node

import { Command } from 'commander';
import { init } from './commands/init.js';
import { addWatch, removeWatch, listWatch } from './commands/watch.js';
import { search } from './commands/search.js';
import { get } from './commands/get.js';
import { getRemote } from './commands/get-remote.js';

const program = new Command();

program
  .name('tower')
  .description('Cross-device file sync and discovery')
  .version('0.1.0');

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
  .action(() => {
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
    await getRemote();
  });

program.parse(process.argv);
