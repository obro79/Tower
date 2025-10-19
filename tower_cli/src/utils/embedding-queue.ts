import * as fs from 'fs';
import { EventEmitter } from 'events';
import { Logger } from './logger.js';
import { apiClient } from './api-client.js';
import { generateEmbeddingFromFile } from './embedding.js';

interface QueueItem {
  filePath: string;
  fileId: number;
  retries: number;
}

export class EmbeddingQueue extends EventEmitter {
  private queue: Map<string, QueueItem> = new Map();
  private processing: boolean = false;
  private paused: boolean = false;
  private maxRetries: number = 3;

  constructor() {
    super();
  }

  enqueue(filePath: string, fileId: number): void {
    if (this.queue.has(filePath)) {
      return;
    }

    this.queue.set(filePath, {
      filePath,
      fileId,
      retries: 0,
    });

    if (!this.processing && !this.paused) {
      this.processQueue();
    }
  }

  pause(): void {
    if (this.paused) return;
    
    this.paused = true;
  }

  async resume(): Promise<void> {
    if (!this.paused) return;
    
    this.paused = false;

    if (!this.processing && this.queue.size > 0) {
      await this.processQueue();
    }
  }

  isPaused(): boolean {
    return this.paused;
  }

  isProcessing(): boolean {
    return this.processing;
  }

  getQueueSize(): number {
    return this.queue.size;
  }

  private async processQueue(): Promise<void> {
    if (this.processing || this.paused) return;

    this.processing = true;

    while (this.queue.size > 0 && !this.paused) {
      const entry = this.queue.entries().next().value as [string, QueueItem] | undefined;
      if (!entry) break;
      
      const [filePath, item] = entry;
      this.queue.delete(filePath);

      try {
        await this.processItem(item);
        this.emit('item-processed', item.filePath);
      } catch (error: any) {
        Logger.error(`Failed to process embedding for ${item.filePath}: ${error.message}`);
        
        if (item.retries < this.maxRetries) {
          item.retries++;
          this.queue.set(item.filePath, item);
        } else {
          Logger.error(`Max retries reached for ${item.filePath}, skipping`);
          this.emit('item-failed', item.filePath);
        }
      }
    }

    this.processing = false;
    
    if (this.queue.size === 0) {
      this.emit('queue-empty');
    }
  }

  private async processItem(item: QueueItem): Promise<void> {
    if (!fs.existsSync(item.filePath)) {
      Logger.warning(`File no longer exists: ${item.filePath}`);
      return;
    }

    Logger.info(`Generating embedding for: ${item.filePath}`);
    const embedding = await generateEmbeddingFromFile(item.filePath);
    
    await apiClient.registerEmbedding(item.fileId, embedding);
    Logger.success(`Embedding registered for: ${item.filePath}`);
  }

  async waitForCompletion(): Promise<void> {
    if (!this.processing && this.queue.size === 0) return;

    return new Promise((resolve) => {
      const checkCompletion = () => {
        if (!this.processing && this.queue.size === 0) {
          this.off('item-processed', checkCompletion);
          this.off('item-failed', checkCompletion);
          this.off('queue-empty', checkCompletion);
          resolve();
        }
      };

      this.on('item-processed', checkCompletion);
      this.on('item-failed', checkCompletion);
      this.on('queue-empty', checkCompletion);
    });
  }

  clear(): void {
    this.queue.clear();
  }
}

export const embeddingQueue = new EmbeddingQueue();
