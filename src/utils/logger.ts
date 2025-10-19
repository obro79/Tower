import chalk from 'chalk';

export class Logger {
  static success(message: string): void {
    console.log(chalk.green('✓'), message);
  }

  static error(message: string): void {
    console.log(chalk.red('✗'), message);
  }

  static warning(message: string): void {
    console.log(chalk.yellow('⚠'), message);
  }

  static info(message: string): void {
    console.log(chalk.blue('ℹ'), message);
  }

  static log(message: string): void {
    console.log(message);
  }

  static header(message: string): void {
    console.log(chalk.bold.cyan(message));
  }

  static dim(message: string): void {
    console.log(chalk.dim(message));
  }
}
