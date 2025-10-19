import chalk from 'chalk';
import { showWelcome } from './help';

/**
 * Show interactive picker when no command is provided
 */
export async function showInteractivePicker(): Promise<string | null> {
  // Show welcome screen with Tower ASCII art and hints
  showWelcome();
  return null;
}

/**
 * Execute a selected command and return arguments
 */
export function executeCommand(command: string): string[] {
  // This function converts a command selection into arguments
  // For now, it just returns the command as an array
  return command ? [command] : [];
}
