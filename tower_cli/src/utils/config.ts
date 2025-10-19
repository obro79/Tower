import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Config, WatchedItem } from '../types/index.js';

const CONFIG_DIR = path.join(os.homedir(), '.tower');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

export class ConfigManager {
  private config: Config | null = null;

  constructor() {
    this.ensureConfigDir();
    if (fs.existsSync(CONFIG_FILE)) {
      this.config = this.load();
    }
  }

  private ensureConfigDir(): void {
    if (!fs.existsSync(CONFIG_DIR)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }
  }

  private load(): Config {
    try {
      const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      throw new Error('Failed to load config. Run "tower init" first.');
    }
  }

  private save(config: Config): void {
    this.ensureConfigDir();
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
  }

  isInitialized(): boolean {
    return this.config !== null && !!this.config.backendUrl;
  }

  initialize(backendUrl: string, syncInterval: number, deviceName: string, deviceIp: string, deviceUser: string): void {
    this.config = {
      backendUrl,
      syncInterval,
      deviceName,
      deviceIp,
      deviceUser,
      watchList: []
    };
    this.save(this.config);
  }

  getConfig(): Config {
    if (!this.config) {
      throw new Error('Config not initialized. Run "tower init" first.');
    }
    return this.config;
  }

  addWatch(item: WatchedItem): void {
    if (!this.config) {
      throw new Error('Config not initialized. Run "tower init" first.');
    }
    this.config.watchList.push(item);
    this.save(this.config);
  }

  removeWatch(itemPath: string): boolean {
    if (!this.config) {
      throw new Error('Config not initialized. Run "tower init" first.');
    }
    const index = this.config.watchList.findIndex(item => item.path === itemPath);
    if (index !== -1) {
      this.config.watchList.splice(index, 1);
      this.save(this.config);
      return true;
    }
    return false;
  }

  getWatchList(): WatchedItem[] {
    if (!this.config) {
      return [];
    }
    return this.config.watchList;
  }

  clearWatchList(): void {
    if (!this.config) {
      throw new Error('Config not initialized. Run "tower init" first.');
    }
    this.config.watchList = [];
    this.save(this.config);
  }
}
