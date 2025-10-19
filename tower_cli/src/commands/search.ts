import chalk from 'chalk';
import Table from 'cli-table3';
import { ConfigManager } from '../utils/config.js';
import { Logger } from '../utils/logger.js';
import { apiClient } from '../utils/api-client.js';

const configManager = new ConfigManager();

export async function search(query: string): Promise<void> {
  try {
    if (!configManager.isInitialized()) {
      Logger.error('Tower not initialized. Run "tower init" first.');
      return;
    }

    const isBackendRunning = await apiClient.healthCheck();
    if (!isBackendRunning) {
      Logger.error('Backend server not running');
      Logger.info('Start backend with: cd backend && uvicorn main:app --reload');
      return;
    }

    Logger.info(`Searching backend registry for: "${query}"`);

    const searchQuery = query.includes('*') ? query : `*${query}*`;
    const results = await apiClient.searchFiles(searchQuery);

    if (results.length === 0) {
      Logger.info(`No results found for: "${query}"`);
      return;
    }

    const table = new Table({
      head: [
        chalk.cyan('ID'),
        chalk.cyan('File'),
        chalk.cyan('Device'),
        chalk.cyan('Size'),
        chalk.cyan('Modified')
      ],
      colWidths: [6, 30, 20, 12, 25]
    });

    results.forEach(file => {
      const sizeMB = (file.size / 1024 / 1024).toFixed(2);
      const modified = new Date(file.last_modified_time).toLocaleString();

      table.push([
        file.id.toString(),
        file.file_name,
        file.device,
        `${sizeMB} MB`,
        modified
      ]);
    });

    console.log(table.toString());
    Logger.success(`Found ${results.length} file(s) across all devices`);
    Logger.info('Use "tower get <filename>" to download a file');
  } catch (error: any) {
    Logger.error(`Search failed: ${error.message}`);
  }
}
