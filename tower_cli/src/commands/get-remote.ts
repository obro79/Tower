import { ConfigManager } from '../utils/config';
import { Logger } from '../utils/logger';

const configManager = new ConfigManager();

export async function getRemote(): Promise<void> {
  try {
    if (!configManager.isInitialized()) {
      Logger.error('Tower not initialized. Run "tower init" first.');
      return;
    }

    Logger.warning('tower get-remote is not yet implemented');
    Logger.info('This command will list all files registered in the backend across all devices');
    Logger.info('For now, use "tower search *" to see all files');
  } catch (error: any) {
    Logger.error(`get-remote failed: ${error.message}`);
  }
}
