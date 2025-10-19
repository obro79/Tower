import chalk from 'chalk';
import Table from 'cli-table3';
import { ConfigManager } from '../utils/config.js';
import { Logger } from '../utils/logger.js';
import { apiClient } from '../utils/api-client.js';
import { generateEmbeddingFromText } from '../utils/embedding.js';
import { init } from './init.js';

const configManager = new ConfigManager();

export async function search(query: string, fuzzy: boolean = false): Promise<void> {
  try {
    if (!configManager.isInitialized()) {
      await init();
      if (!configManager.isInitialized()) {
        return;
      }
    }

    const isBackendRunning = await apiClient.healthCheck();
    if (!isBackendRunning) {
      Logger.error('Backend server not running');
      Logger.info('Start backend with: cd backend && uvicorn main:app --reload');
      return;
    }

    const searchMode = fuzzy ? 'fuzzy' : 'wildcard';
    Logger.info(`Searching backend registry for: "${query}" (${searchMode} mode)`);

    const searchQuery = query.includes('*') ? query : `*${query}*`;
    const results = await apiClient.searchFiles(searchQuery, fuzzy);

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

export async function semanticSearch(query: string, k: number = 5): Promise<void> {
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

    Logger.info(`Generating embedding for: "${query}"`);
    const queryEmbedding = await generateEmbeddingFromText(query);

    Logger.info('Performing semantic search...');
    const results = await apiClient.semanticSearch(queryEmbedding, k);

    if (results.length === 0) {
      Logger.info(`No results found for: "${query}"`);
      return;
    }

    const table = new Table({
      head: [
        chalk.cyan('ID'),
        chalk.cyan('File'),
        chalk.cyan('Device'),
        chalk.cyan('Similarity'),
        chalk.cyan('Size'),
        chalk.cyan('Modified')
      ],
      colWidths: [6, 30, 20, 12, 12, 25]
    });

    results.forEach(file => {
      const sizeMB = (file.size / 1024 / 1024).toFixed(2);
      const modified = new Date(file.last_modified_time).toLocaleString();
      const similarity = (file.similarity_score * 100).toFixed(1);

      table.push([
        file.id.toString(),
        file.file_name,
        file.device,
        `${similarity}%`,
        `${sizeMB} MB`,
        modified
      ]);
    });

    console.log(table.toString());
    Logger.success(`Found ${results.length} semantically similar file(s)`);
    Logger.info('Use "tower get <filename>" to download a file');
  } catch (error: any) {
    Logger.error(`Semantic search failed: ${error.message}`);
  }
}
