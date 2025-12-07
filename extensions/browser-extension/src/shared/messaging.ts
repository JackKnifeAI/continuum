/**
 * Cross-script messaging utilities
 */

import browser from 'webextension-polyfill';
import type { ExtensionMessage, ExtensionResponse } from './types';

/**
 * Send message to background script
 */
export async function sendToBackground<T = unknown, R = unknown>(
  message: ExtensionMessage<T>
): Promise<R> {
  const response = await browser.runtime.sendMessage(message) as ExtensionResponse<R>;

  if (!response.success && response.error) {
    throw new Error(response.error);
  }

  return response.data as R;
}

/**
 * Send message to content script
 */
export async function sendToContent<T = unknown, R = unknown>(
  tabId: number,
  message: ExtensionMessage<T>
): Promise<R> {
  const response = await browser.tabs.sendMessage(tabId, message) as ExtensionResponse<R>;

  if (!response.success && response.error) {
    throw new Error(response.error);
  }

  return response.data as R;
}

/**
 * Send message to all content scripts
 */
export async function broadcastToContent<T = unknown>(
  message: ExtensionMessage<T>
): Promise<void> {
  const tabs = await browser.tabs.query({});

  await Promise.allSettled(
    tabs.map(tab =>
      tab.id ? browser.tabs.sendMessage(tab.id, message) : Promise.resolve()
    )
  );
}

/**
 * Create message handler
 */
export function createMessageHandler<T = unknown, R = unknown>(
  handler: (message: ExtensionMessage<T>) => Promise<R> | R
): (message: any, sender: browser.Runtime.MessageSender) => Promise<ExtensionResponse<R>> {
  return async (message: ExtensionMessage<T>, sender) => {
    try {
      const data = await handler(message);
      return {
        success: true,
        data,
        requestId: message.requestId,
      };
    } catch (error) {
      console.error('Message handler error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        requestId: message.requestId,
      };
    }
  };
}

/**
 * Generate unique request ID
 */
export function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
