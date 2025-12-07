/**
 * Sync Manager - Handles background synchronization and conflict resolution
 */

import BackgroundFetch from 'react-native-background-fetch';
import type {
  SyncResult,
  OfflineOperation,
  SyncConflict,
  ContinuumConfig,
} from '../types';
import type { StorageManager } from '../storage/StorageManager';
import type { NetworkManager } from '../network/NetworkManager';
import type { Logger } from '../utils/Logger';

export class SyncManager {
  private config: Required<ContinuumConfig>;
  private storageManager: StorageManager;
  private networkManager: NetworkManager;
  private logger: Logger;
  private syncQueue: OfflineOperation[] = [];
  private isSyncing = false;
  private lastSyncTime: Date | null = null;

  constructor(
    config: Required<ContinuumConfig>,
    storageManager: StorageManager,
    networkManager: NetworkManager,
    logger: Logger
  ) {
    this.config = config;
    this.storageManager = storageManager;
    this.networkManager = networkManager;
    this.logger = logger;
  }

  async initialize(): Promise<void> {
    try {
      this.logger.info('Initializing sync manager');
      await this.loadQueue();
      this.logger.info('Sync manager initialized');
    } catch (error) {
      this.logger.error('Failed to initialize sync manager', error);
      throw error;
    }
  }

  // ========================================================================
  // Background Sync
  // ========================================================================

  async startBackgroundSync(): Promise<void> {
    try {
      this.logger.info('Starting background sync');

      const status = await BackgroundFetch.configure(
        {
          minimumFetchInterval: Math.floor(this.config.syncInterval / 60000), // Convert to minutes
          stopOnTerminate: false,
          startOnBoot: true,
          enableHeadless: true,
          requiresNetworkConnectivity: true,
        },
        async (taskId) => {
          this.logger.debug('Background fetch triggered', { taskId });

          try {
            await this.sync();
            BackgroundFetch.finish(taskId);
          } catch (error) {
            this.logger.error('Background sync failed', error);
            BackgroundFetch.finish(taskId);
          }
        },
        (taskId) => {
          this.logger.warn('Background fetch timeout', { taskId });
          BackgroundFetch.finish(taskId);
        }
      );

      this.logger.info('Background sync configured', { status });
    } catch (error) {
      this.logger.error('Failed to start background sync', error);
      throw error;
    }
  }

  async stopBackgroundSync(): Promise<void> {
    try {
      await BackgroundFetch.stop();
      this.logger.info('Background sync stopped');
    } catch (error) {
      this.logger.error('Failed to stop background sync', error);
    }
  }

  // ========================================================================
  // Sync Operations
  // ========================================================================

  async sync(): Promise<SyncResult> {
    if (this.isSyncing) {
      this.logger.warn('Sync already in progress');
      throw new Error('Sync already in progress');
    }

    if (!(await this.networkManager.isOnline())) {
      this.logger.warn('Cannot sync: offline');
      throw new Error('Cannot sync while offline');
    }

    try {
      this.isSyncing = true;
      this.logger.info('Starting sync', { queueSize: this.syncQueue.length });

      let memoriesSynced = 0;
      let conceptsSynced = 0;
      const conflicts: SyncConflict[] = [];

      // Process each operation in queue
      for (const operation of this.syncQueue) {
        try {
          await this.processOperation(operation);

          if (operation.resource === 'memory') {
            memoriesSynced++;
          } else if (operation.resource === 'concept') {
            conceptsSynced++;
          }

          // Remove from queue
          this.syncQueue = this.syncQueue.filter((op) => op.id !== operation.id);
        } catch (error: any) {
          this.logger.error('Failed to process operation', {
            operation,
            error,
          });

          // Check for conflicts
          if (error.statusCode === 409) {
            conflicts.push({
              id: operation.id,
              type: operation.resource,
              localVersion: operation.data,
              remoteVersion: error.details,
            });
          }

          // Increment retry count
          operation.retries++;
          operation.status = 'failed';
        }
      }

      // Save updated queue
      await this.saveQueue();

      this.lastSyncTime = new Date();

      const result: SyncResult = {
        success: conflicts.length === 0,
        memoriesSynced,
        conceptsSynced,
        conflicts,
        lastSyncTime: this.lastSyncTime.toISOString(),
        nextSyncTime: new Date(
          Date.now() + this.config.syncInterval
        ).toISOString(),
      };

      this.logger.info('Sync complete', result);
      return result;
    } catch (error) {
      this.logger.error('Sync failed', error);
      throw error;
    } finally {
      this.isSyncing = false;
    }
  }

  private async processOperation(operation: OfflineOperation): Promise<void> {
    this.logger.debug('Processing operation', operation);

    const { type, resource, data } = operation;

    if (resource === 'memory') {
      if (type === 'create') {
        await this.networkManager.post('/memories', data);
      } else if (type === 'update') {
        await this.networkManager.patch(`/memories/${data.id}`, data);
      } else if (type === 'delete') {
        await this.networkManager.delete(`/memories/${data.id}`);
      }
    } else if (resource === 'concept') {
      // Handle concept operations
      this.logger.warn('Concept sync not implemented yet');
    }
  }

  // ========================================================================
  // Queue Management
  // ========================================================================

  async queueOperation(
    operation: Omit<OfflineOperation, 'id' | 'timestamp' | 'retries' | 'status'>
  ): Promise<void> {
    const queuedOperation: OfflineOperation = {
      id: `op-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      retries: 0,
      status: 'pending',
      ...operation,
    };

    this.syncQueue.push(queuedOperation);
    await this.saveQueue();

    this.logger.debug('Operation queued', queuedOperation);

    // Try to sync immediately if online
    if (await this.networkManager.isOnline()) {
      this.sync().catch((error) => {
        this.logger.warn('Auto-sync failed', error);
      });
    }
  }

  async getQueue(): Promise<OfflineOperation[]> {
    return [...this.syncQueue];
  }

  private async loadQueue(): Promise<void> {
    try {
      // Load from storage (implement based on storage solution)
      this.syncQueue = [];
    } catch (error) {
      this.logger.error('Failed to load queue', error);
      this.syncQueue = [];
    }
  }

  private async saveQueue(): Promise<void> {
    try {
      // Save to storage (implement based on storage solution)
      this.logger.debug('Queue saved', { size: this.syncQueue.length });
    } catch (error) {
      this.logger.error('Failed to save queue', error);
    }
  }

  // ========================================================================
  // Status
  // ========================================================================

  async getStatus(): Promise<{
    isSyncing: boolean;
    lastSyncTime?: Date;
    pendingOperations: number;
  }> {
    return {
      isSyncing: this.isSyncing,
      lastSyncTime: this.lastSyncTime || undefined,
      pendingOperations: this.syncQueue.length,
    };
  }

  async getLastSyncTime(): Promise<Date | null> {
    return this.lastSyncTime;
  }
}
