import * as path from 'path';
import * as os from 'os';
import inquirer from 'inquirer';
import { Logger } from '../utils/logger';
import { apiClient, FileRecord } from '../utils/api-client';

/**
 * Get (search and download) a file from a remote device
 * Two-step process:
 * 1. Search for files matching the filename/pattern
 * 2. User selects which file to download
 * 3. Download the selected file
 */
export async function get(
  filename: string,
  destination?: string
): Promise<void> {
  try {
    // Check if backend is available
    const isBackendRunning = await apiClient.healthCheck();
    if (!isBackendRunning) {
      Logger.error('Backend server not running');
      Logger.info('Start backend with: cd backend && uvicorn main:app --reload');
      return;
    }

    // Step 1: Search for files matching the filename/pattern
    Logger.info(`Searching for files matching "${filename}"...`);
    const results = await apiClient.searchFiles(filename);

    if (results.length === 0) {
      Logger.warning(`No files found matching "${filename}"`);
      return;
    }

    Logger.success(`Found ${results.length} matching file${results.length > 1 ? 's' : ''}`);

    // Step 2: If multiple matches, ask user to select
    let selectedFile: FileRecord;

    if (results.length === 1) {
      // Only one match, use it directly
      selectedFile = results[0];
      Logger.info(`Using: ${selectedFile.file_name} from ${selectedFile.device}`);
    } else {
      // Multiple matches, show interactive selection
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

    // Step 3: Download the selected file
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
