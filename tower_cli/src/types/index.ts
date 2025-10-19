export interface WatchedItem {
  path: string;
  addedAt: string;
}

export interface Config {
  backendUrl: string;
  syncInterval: number;
  deviceName: string;
  deviceIp: string;
  deviceUser: string;
  watchList: WatchedItem[];
}
