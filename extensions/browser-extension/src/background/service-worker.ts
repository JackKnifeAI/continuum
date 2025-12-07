/**
 * Background Service Worker (Manifest V3)
 * Main background script for CONTINUUM extension
 */

import browser from 'webextension-polyfill';
import { ContinuumAPIClient } from '../shared/api-client';
import { Storage } from '../shared/storage';
import { createMessageHandler, broadcastToContent } from '../shared/messaging';
import type { ExtensionMessage, CaptureRequest, Memory } from '../shared/types';

let apiClient: ContinuumAPIClient | null = null;
let syncIntervalId: number | null = null;

/**
 * Initialize API client
 */
async function initializeAPIClient() {
  const config = await Storage.getConfig();

  if (!config.apiKey) {
    console.warn('No API key configured');
    return null;
  }

  apiClient = new ContinuumAPIClient({
    apiEndpoint: config.apiEndpoint,
    apiKey: config.apiKey,
  });

  return apiClient;
}

/**
 * Setup context menus
 */
async function setupContextMenus() {
  await browser.contextMenus.removeAll();

  browser.contextMenus.create({
    id: 'save-to-continuum',
    title: 'Save to CONTINUUM',
    contexts: ['selection'],
  });

  browser.contextMenus.create({
    id: 'find-related',
    title: 'Find related memories',
    contexts: ['selection'],
  });

  browser.contextMenus.create({
    id: 'capture-page',
    title: 'Capture entire page',
    contexts: ['page'],
  });
}

/**
 * Handle context menu clicks
 */
browser.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab?.id) return;

  switch (info.menuItemId) {
    case 'save-to-continuum':
      if (info.selectionText) {
        await handleCapture({
          content: info.selectionText,
          source: {
            type: 'selection',
            url: tab.url || '',
            title: tab.title || '',
            domain: new URL(tab.url || '').hostname,
          },
        });
      }
      break;

    case 'find-related':
      if (info.selectionText) {
        await handleSearch(info.selectionText);
      }
      break;

    case 'capture-page':
      await browser.tabs.sendMessage(tab.id, {
        type: 'CAPTURE_PAGE',
        payload: {},
      });
      break;
  }
});

/**
 * Handle keyboard commands
 */
browser.commands.onCommand.addListener(async (command) => {
  const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;

  switch (command) {
    case 'capture-selection':
      await browser.tabs.sendMessage(tab.id, {
        type: 'CAPTURE_SELECTION',
        payload: {},
      });
      break;

    case 'quick-search':
      await browser.tabs.sendMessage(tab.id, {
        type: 'QUICK_SEARCH',
        payload: {},
      });
      break;

    case 'toggle-sidebar':
      // Chrome only
      if (browser.sidePanel) {
        await browser.sidePanel.open({ windowId: tab.windowId });
      }
      break;
  }
});

/**
 * Handle capture request
 */
async function handleCapture(request: CaptureRequest): Promise<Memory> {
  if (!apiClient) {
    await initializeAPIClient();
  }

  if (!apiClient) {
    throw new Error('API client not initialized. Please configure API key.');
  }

  try {
    const memory = await apiClient.capture(request);

    // Update badge
    await updateBadge();

    // Show notification
    await browser.notifications.create({
      type: 'basic',
      iconUrl: browser.runtime.getURL('assets/icons/icon48.png'),
      title: 'Memory Captured',
      message: `Saved to CONTINUUM: ${memory.source.title}`,
    });

    // Broadcast to content scripts
    await broadcastToContent({
      type: 'HIGHLIGHT_MEMORIES',
      payload: { memoryId: memory.id },
    });

    return memory;
  } catch (error) {
    console.error('Capture failed:', error);

    // Queue for later if offline
    await Storage.addPendingCapture(request);

    throw error;
  }
}

/**
 * Handle search request
 */
async function handleSearch(query: string) {
  if (!apiClient) {
    await initializeAPIClient();
  }

  if (!apiClient) {
    throw new Error('API client not initialized');
  }

  const results = await apiClient.search(query);

  // Open sidebar with results
  const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    await browser.tabs.sendMessage(tab.id, {
      type: 'SHOW_SEARCH_RESULTS',
      payload: results,
    });
  }

  return results;
}

/**
 * Update badge with memory count
 */
async function updateBadge() {
  if (!apiClient) return;

  try {
    const memories = await apiClient.getRecentMemories(1);
    const count = memories.length > 0 ? '+' : '';

    await browser.action.setBadgeText({ text: count });
    await browser.action.setBadgeBackgroundColor({ color: '#7c3aed' }); // Twilight purple
  } catch (error) {
    console.error('Failed to update badge:', error);
  }
}

/**
 * Sync pending captures
 */
async function syncPendingCaptures() {
  const pending = await Storage.getPendingCaptures();

  if (pending.length === 0) return;

  if (!apiClient) {
    await initializeAPIClient();
  }

  if (!apiClient) return;

  const results = await Promise.allSettled(
    pending.map(capture => apiClient!.capture(capture))
  );

  const succeeded = results.filter(r => r.status === 'fulfilled').length;

  if (succeeded === pending.length) {
    await Storage.clearPendingCaptures();
    await Storage.updateSyncTime();
  }

  console.log(`Synced ${succeeded}/${pending.length} pending captures`);
}

/**
 * Start background sync
 */
async function startSync() {
  if (syncIntervalId) {
    clearInterval(syncIntervalId);
  }

  const config = await Storage.getConfig();

  syncIntervalId = setInterval(
    syncPendingCaptures,
    config.syncInterval
  ) as unknown as number;

  // Initial sync
  await syncPendingCaptures();
}

/**
 * Message handler
 */
const messageHandler = createMessageHandler(async (message: ExtensionMessage) => {
  switch (message.type) {
    case 'CAPTURE_SELECTION':
      return handleCapture(message.payload as CaptureRequest);

    case 'QUICK_SEARCH':
      return handleSearch(message.payload as string);

    case 'GET_PAGE_CONTEXT':
      if (!apiClient) await initializeAPIClient();
      return apiClient?.getPageContext(message.payload as string);

    case 'SYNC_STATUS':
      const lastSync = await Storage.getLastSyncTime();
      const pending = await Storage.getPendingCaptures();
      return {
        lastSync,
        pendingItems: pending.length,
        isOnline: !!apiClient,
        errors: [],
      };

    case 'UPDATE_CONFIG':
      await Storage.setConfig(message.payload as any);
      await initializeAPIClient();
      await startSync();
      return { success: true };

    default:
      throw new Error(`Unknown message type: ${message.type}`);
  }
});

/**
 * Listen for messages
 */
browser.runtime.onMessage.addListener(messageHandler);

/**
 * Handle installation
 */
browser.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    // First install
    await setupContextMenus();
    await browser.tabs.create({
      url: browser.runtime.getURL('build/options.html'),
    });
  } else if (details.reason === 'update') {
    // Update
    await setupContextMenus();
  }
});

/**
 * Handle startup
 */
browser.runtime.onStartup.addListener(async () => {
  await initializeAPIClient();
  await setupContextMenus();
  await startSync();
  await updateBadge();
});

/**
 * Initialize on load
 */
(async () => {
  await initializeAPIClient();
  await setupContextMenus();
  await startSync();
  await updateBadge();
})();

console.log('CONTINUUM background service worker initialized');
