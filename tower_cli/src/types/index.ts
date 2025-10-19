export interface WatchedItem {
  path: string;
  recursive: boolean;
  exclude: string[];
  tags: string[];
  addedAt: string;
  lastModified?: string;
}

export interface Device {
  id: string;
  name: string;
  addedAt: string;
  lastSeen?: string;
  status: 'online' | 'offline' | 'syncing';
}

export interface SyncHistory {
  timestamp: string;
  filesChanged: number;
  status: 'success' | 'failed' | 'partial';
  details?: string;
}

export interface Config {
  watchList: WatchedItem[];
  devices: Device[];
  syncHistory: SyncHistory[];
  settings: {
    autoSync: boolean;
    syncInterval: number; // in minutes
    conflictResolution: 'latest' | 'manual' | 'keep-both';
    excludePatterns: string[];
  };
}

export interface SearchOptions {
  name?: boolean;
  content?: boolean;
  tags?: string;
  type?: string;
}

export interface WatchOptions {
  recursive?: boolean;
  exclude?: string[];
  tags?: string[];
}
