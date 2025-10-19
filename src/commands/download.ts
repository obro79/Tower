import * as path from 'path';
import * as os from 'os';
import { Logger } from '../utils/logger';
import { apiClient } from '../utils/api-client';

export async function download(
  fileId: number,
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

    // Get file metadata from backend
    Logger.info(`Retrieving file metadata for ID: ${fileId}...`);
    const fileRecord = await apiClient.getFile(fileId);

    Logger.info(`File found: ${fileRecord.file_name}`);
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
  } catch (error: any) {
    Logger.error(`Download failed: ${error.message}`);
  }
}
