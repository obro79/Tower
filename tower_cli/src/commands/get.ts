import * as path from 'path';
import * as os from 'os';
import inquirer from 'inquirer';
import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';
import { apiClient, FileRecord } from '../utils/api-client';
import { init } from './init';

const configManager = new ConfigManager();

function isNaturalLanguageQuery(query: string): boolean {
  const hasMultipleWords = query.trim().split(/\s+/).length > 1;
  const hasNoWildcards = !query.includes('*');
  const hasNoExtension = !query.includes('.');
  
  return hasMultipleWords && hasNoWildcards && hasNoExtension;
}

export async function get(
  filename?: string,
  destination?: string
): Promise<void> {
  try {
    if (!configManager.isInitialized()) {
      await init();
      if (!configManager.isInitialized()) {
        return;
      }
    }

    if (!filename) {
      Logger.error('Please provide a filename or search query');
      Logger.info('Usage: tower get <filename>');
      Logger.info('       tower get "research paper about AI"  (natural language - not implemented)');
      return;
    }

    if (isNaturalLanguageQuery(filename)) {
      Logger.warning('Natural language search is not yet implemented');
      Logger.info('For now, use filename patterns like: tower get "*.pdf" or tower get "paper"');
      return;
    }

    const isBackendRunning = await apiClient.healthCheck();
    if (!isBackendRunning) {
      Logger.error('Backend server not running');
      Logger.info('Start backend with: cd backend && uvicorn main:app --reload');
      return;
    }

    Logger.info(`Searching for files matching "${filename}"...`);
    const results = await apiClient.searchFiles(filename);

    if (results.length === 0) {
      Logger.warning(`No files found matching "${filename}"`);
      return;
    }

    Logger.success(`Found ${results.length} matching file${results.length > 1 ? 's' : ''}`);

    let selectedFile: FileRecord;

    if (results.length === 1) {
      selectedFile = results[0];
      Logger.info(`Using: ${selectedFile.file_name} from ${selectedFile.device}`);
    } else {
      const choices = results.map((file) => ({
        name: formatFileChoice(file),
        value: file,
      }));

      const answer = await inquirer.prompt([
        {
          type: 'list',
          name: 'selectedFile',
          message: 'Select file to download:',
          choices,
        },
      ]);

      selectedFile = answer.selectedFile;
    }

    await downloadFile(selectedFile, destination);

  } catch (error: any) {
    Logger.error(`Get failed: ${error.message}`);
  }
}

/**
 * Format a file record for display in the selection list
 */
function formatFileChoice(file: FileRecord): string {
  const sizeMB = (file.size / 1024 / 1024).toFixed(2);
  const modified = new Date(file.last_modified_time).toLocaleDateString();
  return `${file.file_name} (${file.device} @ ${file.device_ip}) - ${sizeMB} MB - ${file.absolute_path} - Modified: ${modified}`;
}

/**
 * Download a specific file by its record
 * Helper function that performs the actual download
 */
async function downloadFile(
  fileRecord: FileRecord,
  destination?: string
): Promise<void> {
  Logger.info(`File: ${fileRecord.file_name}`);
  Logger.info(`Location: ${fileRecord.device} (${fileRecord.device_ip})`);
  Logger.info(`Size: ${(fileRecord.size / 1024 / 1024).toFixed(2)} MB`);

  // Determine destination path
  const dest = destination || path.join(os.homedir(), 'Downloads', fileRecord.file_name);

  // Download file via SCP
  Logger.info('Initiating file transfer via SCP...');
  Logger.info(`From: ${fileRecord.device_user}@${fileRecord.device_ip}:${fileRecord.absolute_path}`);
  Logger.info(`To: ${dest}`);

  await apiClient.downloadFile(fileRecord, dest);

  Logger.success(`File downloaded successfully!`);
  Logger.success(`Location: ${dest}`);
}
