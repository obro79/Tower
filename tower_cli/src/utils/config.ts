import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Config, WatchedItem, Device, SyncHistory } from '../types';

const CONFIG_DIR = path.join(os.homedir(), '.tower');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

const DEFAULT_CONFIG: Config = {
  watchList: [],
  devices: [],
  syncHistory: [],
  settings: {
    autoSync: true,
    syncInterval: 5,
    conflictResolution: 'latest',
    excludePatterns: ['node_modules', '.git', '*.log', '.DS_Store']
  }
};

export class ConfigManager {
  private config: Config;

  constructor() {
    this.config = this.load();
  }

  private ensureConfigDir(): void {
    if (!fs.existsSync(CONFIG_DIR)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }
  }

  private load(): Config {
    this.ensureConfigDir();

    if (!fs.existsSync(CONFIG_FILE)) {
      this.save(DEFAULT_CONFIG);
      return DEFAULT_CONFIG;
    }

    try {
      const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.error('Error loading config, using defaults');
      return DEFAULT_CONFIG;
    }
  }

  private save(config: Config): void {
    this.ensureConfigDir();
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
  }

  // Watch list methods
  addWatch(item: WatchedItem): void {
    this.config.watchList.push(item);
    this.save(this.config);
  }

  removeWatch(itemPath: string): boolean {
    const index = this.config.watchList.findIndex(item => item.path === itemPath);
    if (index !== -1) {
      this.config.watchList.splice(index, 1);
      this.save(this.config);
      return true;
    }
    return false;
  }

  getWatchList(): WatchedItem[] {
    return this.config.watchList;
  }

  clearWatchList(): void {
    this.config.watchList = [];
    this.save(this.config);
  }

  // Device methods
  addDevice(device: Device): void {
    this.config.devices.push(device);
    this.save(this.config);
  }

  removeDevice(deviceId: string): boolean {
    const index = this.config.devices.findIndex(d => d.id === deviceId);
    if (index !== -1) {
      this.config.devices.splice(index, 1);
      this.save(this.config);
      return true;
    }
    return false;
  }

  getDevices(): Device[] {
    return this.config.devices;
  }

  updateDevice(deviceId: string, updates: Partial<Device>): boolean {
    const device = this.config.devices.find(d => d.id === deviceId);
    if (device) {
      Object.assign(device, updates);
      this.save(this.config);
      return true;
    }
    return false;
  }

  // Sync history methods
  addSyncHistory(history: SyncHistory): void {
    this.config.syncHistory.unshift(history);
    // Keep only last 50 entries
    if (this.config.syncHistory.length > 50) {
      this.config.syncHistory = this.config.syncHistory.slice(0, 50);
    }
    this.save(this.config);
  }

  getSyncHistory(limit?: number): SyncHistory[] {
    return limit
      ? this.config.syncHistory.slice(0, limit)
      : this.config.syncHistory;
  }

  // Settings methods
  getSetting(key: string): any {
    return (this.config.settings as any)[key];
  }

  setSetting(key: string, value: any): void {
    (this.config.settings as any)[key] = value;
    this.save(this.config);
  }

  getAllSettings(): any {
    return this.config.settings;
  }

  reset(): void {
    this.config = DEFAULT_CONFIG;
    this.save(this.config);
  }

  getConfig(): Config {
    return this.config;
  }
}
