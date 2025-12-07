/**
 * Cross-browser storage wrapper
 */

import browser from 'webextension-polyfill';
import type { StorageData, ContinuumConfig } from './types';

const DEFAULT_CONFIG: ContinuumConfig = {
  apiEndpoint: 'http://localhost:8000',
  apiKey: '',
  autoCapture: false,
  syncInterval: 300000, // 5 minutes
  theme: 'system',
  capturePreferences: {
    saveMetadata: true,
    saveScreenshots: false,
    captureCode: true,
    captureVideos: true,
  },
};

export class Storage {
  /**
   * Get configuration
   */
  static async getConfig(): Promise<ContinuumConfig> {
    const result = await browser.storage.local.get('config');
    return result.config || DEFAULT_CONFIG;
  }

  /**
   * Set configuration
   */
  static async setConfig(config: Partial<ContinuumConfig>): Promise<void> {
    const current = await this.getConfig();
    await browser.storage.local.set({
      config: { ...current, ...config },
    });
  }

  /**
   * Get auth token
   */
  static async getAuthToken(): Promise<string | null> {
    const result = await browser.storage.local.get('authToken');
    return result.authToken || null;
  }

  /**
   * Set auth token
   */
  static async setAuthToken(token: string): Promise<void> {
    await browser.storage.local.set({ authToken: token });
  }

  /**
   * Clear auth token
   */
  static async clearAuthToken(): Promise<void> {
    await browser.storage.local.remove('authToken');
  }

  /**
   * Get all storage data
   */
  static async getAll(): Promise<Partial<StorageData>> {
    return browser.storage.local.get(null);
  }

  /**
   * Clear all storage
   */
  static async clear(): Promise<void> {
    await browser.storage.local.clear();
  }

  /**
   * Get pending captures
   */
  static async getPendingCaptures() {
    const result = await browser.storage.local.get('pendingCaptures');
    return result.pendingCaptures || [];
  }

  /**
   * Add pending capture
   */
  static async addPendingCapture(capture: any): Promise<void> {
    const pending = await this.getPendingCaptures();
    pending.push(capture);
    await browser.storage.local.set({ pendingCaptures: pending });
  }

  /**
   * Clear pending captures
   */
  static async clearPendingCaptures(): Promise<void> {
    await browser.storage.local.set({ pendingCaptures: [] });
  }

  /**
   * Update last sync time
   */
  static async updateSyncTime(): Promise<void> {
    await browser.storage.local.set({ syncedAt: new Date().toISOString() });
  }

  /**
   * Get last sync time
   */
  static async getLastSyncTime(): Promise<string | null> {
    const result = await browser.storage.local.get('syncedAt');
    return result.syncedAt || null;
  }
}

export default Storage;
