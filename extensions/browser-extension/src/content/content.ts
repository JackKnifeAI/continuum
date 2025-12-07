/**
 * Content Script
 * Runs on all web pages to enable capture and highlighting
 */

import browser from 'webextension-polyfill';
import { Highlighter } from './highlighter';
import { PageExtractor } from './extractor';
import { OverlayUI } from './overlay';
import { sendToBackground } from '../shared/messaging';
import type { ExtensionMessage, CaptureRequest, Memory } from '../shared/types';

let highlighter: Highlighter;
let extractor: PageExtractor;
let overlay: OverlayUI;

/**
 * Initialize content script
 */
function initialize() {
  highlighter = new Highlighter();
  extractor = new PageExtractor();
  overlay = new OverlayUI();

  setupSelectionListener();
  setupMessageListener();
  loadPageContext();
}

/**
 * Setup text selection listener
 */
function setupSelectionListener() {
  document.addEventListener('mouseup', async (event) => {
    const selection = window.getSelection();
    if (!selection || selection.toString().trim().length === 0) {
      overlay.hide();
      return;
    }

    const text = selection.toString().trim();
    if (text.length < 10) return; // Ignore very short selections

    // Show quick capture button
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    overlay.showQuickCapture({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
      text,
      onCapture: () => captureSelection(text),
      onSearch: () => searchSelection(text),
    });
  });

  // Hide on click outside
  document.addEventListener('mousedown', (event) => {
    if (!(event.target as HTMLElement).closest('.continuum-overlay')) {
      overlay.hide();
    }
  });
}

/**
 * Setup message listener
 */
function setupMessageListener() {
  browser.runtime.onMessage.addListener((message: ExtensionMessage) => {
    switch (message.type) {
      case 'CAPTURE_SELECTION':
        handleCaptureSelection();
        break;

      case 'QUICK_SEARCH':
        handleQuickSearch();
        break;

      case 'CAPTURE_PAGE':
        handleCapturePage();
        break;

      case 'HIGHLIGHT_MEMORIES':
        highlighter.highlightMemory(message.payload.memoryId);
        break;

      case 'SHOW_SEARCH_RESULTS':
        overlay.showSearchResults(message.payload);
        break;
    }

    return Promise.resolve({ success: true });
  });
}

/**
 * Capture current selection
 */
async function captureSelection(text?: string) {
  const selection = text || window.getSelection()?.toString().trim();
  if (!selection) {
    showNotification('No text selected', 'error');
    return;
  }

  const request: CaptureRequest = {
    content: selection,
    source: {
      type: 'selection',
      url: window.location.href,
      title: document.title,
      domain: window.location.hostname,
    },
    metadata: {
      selectionContext: extractor.getSelectionContext(selection),
      pageContext: extractor.getPageSummary(),
    },
  };

  try {
    overlay.showLoading('Capturing to CONTINUUM...');

    const memory = await sendToBackground<CaptureRequest, Memory>({
      type: 'CAPTURE_SELECTION',
      payload: request,
    });

    overlay.hide();
    showNotification('Captured to CONTINUUM!', 'success');

    // Highlight the captured text
    highlighter.highlight(selection, memory.id);
  } catch (error) {
    overlay.hide();
    showNotification('Failed to capture', 'error');
    console.error('Capture error:', error);
  }
}

/**
 * Search for selected text
 */
async function searchSelection(text?: string) {
  const query = text || window.getSelection()?.toString().trim();
  if (!query) return;

  try {
    overlay.showLoading('Searching memories...');

    await sendToBackground({
      type: 'QUICK_SEARCH',
      payload: query,
    });

    // Results will be shown via message
  } catch (error) {
    overlay.hide();
    showNotification('Search failed', 'error');
    console.error('Search error:', error);
  }
}

/**
 * Load page context (related memories)
 */
async function loadPageContext() {
  try {
    const context = await sendToBackground({
      type: 'GET_PAGE_CONTEXT',
      payload: window.location.href,
    });

    // Highlight related memories on page
    if (context.relatedMemories?.length > 0) {
      context.relatedMemories.forEach(memory => {
        highlighter.highlightMemory(memory.id);
      });

      // Show badge
      overlay.showBadge(context.relatedMemories.length);
    }
  } catch (error) {
    console.error('Failed to load page context:', error);
  }
}

/**
 * Handle capture selection command
 */
function handleCaptureSelection() {
  const selection = window.getSelection()?.toString().trim();
  if (selection) {
    captureSelection(selection);
  } else {
    showNotification('Please select some text first', 'error');
  }
}

/**
 * Handle quick search command
 */
function handleQuickSearch() {
  const selection = window.getSelection()?.toString().trim();
  if (selection) {
    searchSelection(selection);
  } else {
    overlay.showSearchBox();
  }
}

/**
 * Handle capture page command
 */
async function handleCapturePage() {
  const content = extractor.extractPageContent();

  if (!content.content) {
    showNotification('Could not extract page content', 'error');
    return;
  }

  const request: CaptureRequest = {
    content: content.content,
    source: {
      type: content.type,
      url: window.location.href,
      title: document.title,
      domain: window.location.hostname,
      author: content.metadata.author,
      publishedDate: content.metadata.publishedDate,
    },
    metadata: {
      tags: content.metadata.tags,
    },
  };

  try {
    overlay.showLoading('Capturing page...');

    await sendToBackground<CaptureRequest, Memory>({
      type: 'CAPTURE_SELECTION',
      payload: request,
    });

    overlay.hide();
    showNotification('Page captured!', 'success');
  } catch (error) {
    overlay.hide();
    showNotification('Failed to capture page', 'error');
    console.error('Capture error:', error);
  }
}

/**
 * Show notification
 */
function showNotification(message: string, type: 'success' | 'error' | 'info') {
  overlay.showNotification(message, type);
}

/**
 * Initialize on load
 */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

console.log('CONTINUUM content script initialized');
