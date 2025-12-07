/**
 * Overlay UI
 * Displays inline UI elements on web pages
 */

import type { SearchResult } from '../shared/types';

export class OverlayUI {
  private container: HTMLDivElement | null = null;
  private styleElement: HTMLStyleElement;

  constructor() {
    this.styleElement = this.injectStyles();
  }

  /**
   * Inject overlay styles
   */
  private injectStyles(): HTMLStyleElement {
    const style = document.createElement('style');
    style.textContent = `
      .continuum-overlay {
        position: absolute;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 14px;
      }

      .continuum-quick-capture {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        display: flex;
        gap: 8px;
        align-items: center;
      }

      .continuum-button {
        background: rgba(255, 255, 255, 0.2);
        border: none;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        transition: background 0.2s;
      }

      .continuum-button:hover {
        background: rgba(255, 255, 255, 0.3);
      }

      .continuum-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: continuum-slide-in 0.3s ease;
      }

      .continuum-notification.success {
        background: #10b981;
        color: white;
      }

      .continuum-notification.error {
        background: #ef4444;
        color: white;
      }

      .continuum-notification.info {
        background: #3b82f6;
        color: white;
      }

      @keyframes continuum-slide-in {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }

      .continuum-loading {
        background: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .continuum-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #e5e7eb;
        border-top-color: #7c3aed;
        border-radius: 50%;
        animation: continuum-spin 0.8s linear infinite;
      }

      @keyframes continuum-spin {
        to { transform: rotate(360deg); }
      }

      .continuum-badge {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #7c3aed;
        color: white;
        padding: 12px 16px;
        border-radius: 50%;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
        cursor: pointer;
        transition: transform 0.2s;
      }

      .continuum-badge:hover {
        transform: scale(1.1);
      }

      .continuum-search-box {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        min-width: 400px;
      }

      .continuum-search-input {
        width: 100%;
        padding: 12px;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        font-size: 14px;
        outline: none;
      }

      .continuum-search-input:focus {
        border-color: #7c3aed;
      }

      .continuum-search-results {
        max-height: 400px;
        overflow-y: auto;
        margin-top: 12px;
      }

      .continuum-search-result {
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.2s;
      }

      .continuum-search-result:hover {
        background: #f3f4f6;
      }
    `;
    document.head.appendChild(style);
    return style;
  }

  /**
   * Show quick capture button
   */
  showQuickCapture(options: {
    x: number;
    y: number;
    text: string;
    onCapture: () => void;
    onSearch: () => void;
  }) {
    this.hide();

    const container = document.createElement('div');
    container.className = 'continuum-overlay continuum-quick-capture';
    container.style.left = `${options.x}px`;
    container.style.top = `${options.y}px`;
    container.style.transform = 'translate(-50%, -100%)';

    const captureBtn = document.createElement('button');
    captureBtn.className = 'continuum-button';
    captureBtn.textContent = 'Save';
    captureBtn.onclick = options.onCapture;

    const searchBtn = document.createElement('button');
    searchBtn.className = 'continuum-button';
    searchBtn.textContent = 'Search';
    searchBtn.onclick = options.onSearch;

    container.appendChild(captureBtn);
    container.appendChild(searchBtn);

    document.body.appendChild(container);
    this.container = container;
  }

  /**
   * Show notification
   */
  showNotification(message: string, type: 'success' | 'error' | 'info') {
    const notification = document.createElement('div');
    notification.className = `continuum-overlay continuum-notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  /**
   * Show loading indicator
   */
  showLoading(message: string) {
    this.hide();

    const container = document.createElement('div');
    container.className = 'continuum-overlay continuum-loading';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.left = '50%';
    container.style.transform = 'translateX(-50%)';

    const spinner = document.createElement('div');
    spinner.className = 'continuum-spinner';

    const text = document.createElement('span');
    text.textContent = message;

    container.appendChild(spinner);
    container.appendChild(text);

    document.body.appendChild(container);
    this.container = container;
  }

  /**
   * Show badge with memory count
   */
  showBadge(count: number) {
    const badge = document.createElement('div');
    badge.className = 'continuum-overlay continuum-badge';
    badge.textContent = count.toString();
    badge.title = `${count} related memories`;

    badge.onclick = () => {
      window.postMessage({ type: 'CONTINUUM_OPEN_SIDEBAR' }, '*');
    };

    document.body.appendChild(badge);
  }

  /**
   * Show search box
   */
  showSearchBox() {
    this.hide();

    const container = document.createElement('div');
    container.className = 'continuum-overlay continuum-search-box';

    const input = document.createElement('input');
    input.className = 'continuum-search-input';
    input.placeholder = 'Search your memories...';
    input.type = 'text';

    const results = document.createElement('div');
    results.className = 'continuum-search-results';

    container.appendChild(input);
    container.appendChild(results);

    // Close on escape
    input.onkeydown = (e) => {
      if (e.key === 'Escape') {
        this.hide();
      }
    };

    document.body.appendChild(container);
    this.container = container;

    // Focus input
    setTimeout(() => input.focus(), 0);
  }

  /**
   * Show search results
   */
  showSearchResults(results: SearchResult[]) {
    if (!this.container) {
      this.showSearchBox();
    }

    const resultsContainer = this.container?.querySelector('.continuum-search-results');
    if (!resultsContainer) return;

    resultsContainer.innerHTML = '';

    results.forEach(result => {
      const item = document.createElement('div');
      item.className = 'continuum-search-result';

      const title = document.createElement('div');
      title.style.fontWeight = 'bold';
      title.textContent = result.memory.source.title;

      const preview = document.createElement('div');
      preview.style.color = '#6b7280';
      preview.style.fontSize = '12px';
      preview.textContent = result.memory.content.slice(0, 100) + '...';

      item.appendChild(title);
      item.appendChild(preview);

      item.onclick = () => {
        window.postMessage({
          type: 'CONTINUUM_SHOW_MEMORY',
          memoryId: result.memory.id,
        }, '*');
        this.hide();
      };

      resultsContainer.appendChild(item);
    });
  }

  /**
   * Hide overlay
   */
  hide() {
    if (this.container) {
      this.container.remove();
      this.container = null;
    }
  }

  /**
   * Cleanup
   */
  destroy() {
    this.hide();
    this.styleElement.remove();
  }
}
