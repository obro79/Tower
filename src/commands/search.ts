import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import Table from 'cli-table3';
import Fuse from 'fuse.js';
import { globSync } from 'glob';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { SearchOptions } from '../types';

const configManager = new ConfigManager();

export function search(query: string, options: SearchOptions): void {
  try {
    const watchList = configManager.getWatchList();

    if (watchList.length === 0) {
      Logger.info('No items in watch list to search');
      return;
    }

    let results: Array<{ path: string; name: string; type: string; match: string }> = [];

    // Filter by tags first if specified
    let filteredWatch = watchList;
    if (options.tags) {
      const filterTags = options.tags.split(',').map(t => t.trim());
      filteredWatch = watchList.filter(item =>
        item.tags.some(tag => filterTags.includes(tag))
      );
    }

    // Collect all files from watched items
    const allFiles: string[] = [];
    filteredWatch.forEach(item => {
      if (fs.existsSync(item.path)) {
        const stats = fs.statSync(item.path);
        if (stats.isFile()) {
          allFiles.push(item.path);
        } else if (stats.isDirectory()) {
          const pattern = item.recursive
            ? path.join(item.path, '**/*')
            : path.join(item.path, '*');

          const files = globSync(pattern, {
            nodir: true,
            ignore: item.exclude.map(e => path.join(item.path, e))
          });
          allFiles.push(...files);
        }
      }
    });

    // Search by filename
    if (options.name || (!options.name && !options.content)) {
      const fileList = allFiles.map(f => ({
        path: f,
        name: path.basename(f)
      }));

      const fuse = new Fuse(fileList, {
        keys: ['name'],
        threshold: 0.4
      });

      const searchResults = fuse.search(query);
      searchResults.forEach(result => {
        if (!options.type || result.item.path.endsWith(`.${options.type}`)) {
          results.push({
            path: result.item.path,
            name: result.item.name,
            type: path.extname(result.item.path) || 'no ext',
            match: 'filename'
          });
        }
      });
    }

    // Search by content
    if (options.content) {
      allFiles.forEach(file => {
        if (options.type && !file.endsWith(`.${options.type}`)) {
          return;
        }

        try {
          const stats = fs.statSync(file);
          // Skip large files (> 10MB)
          if (stats.size > 10 * 1024 * 1024) {
            return;
          }

          const content = fs.readFileSync(file, 'utf-8');
          if (content.toLowerCase().includes(query.toLowerCase())) {
            results.push({
              path: file,
              name: path.basename(file),
              type: path.extname(file) || 'no ext',
              match: 'content'
            });
          }
        } catch (error) {
          // Skip files that can't be read as text
        }
      });
    }

    // Remove duplicates
    results = results.filter((item, index, self) =>
      index === self.findIndex(t => t.path === item.path)
    );

    if (results.length === 0) {
      Logger.info(`No results found for: "${query}"`);
      return;
    }

    // Display results
    const table = new Table({
      head: [
        chalk.cyan('File'),
        chalk.cyan('Path'),
        chalk.cyan('Type'),
        chalk.cyan('Match')
      ],
      colWidths: [30, 50, 10, 12]
    });

    results.forEach(result => {
      table.push([
        result.name,
        result.path,
        result.type,
        result.match
      ]);
    });

    console.log(table.toString());
    Logger.success(`Found ${results.length} result(s)`);
  } catch (error: any) {
    Logger.error(`Search failed: ${error.message}`);
  }
}
