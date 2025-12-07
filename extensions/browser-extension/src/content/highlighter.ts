/**
 * Text Highlighter
 * Highlights captured text on web pages
 */

import type { HighlightInfo } from '../shared/types';

export class Highlighter {
  private highlights: Map<string, HighlightInfo[]> = new Map();
  private styleElement: HTMLStyleElement;

  constructor() {
    this.styleElement = this.injectStyles();
  }

  /**
   * Inject highlighter styles
   */
  private injectStyles(): HTMLStyleElement {
    const style = document.createElement('style');
    style.textContent = `
      .continuum-highlight {
        background-color: rgba(124, 58, 237, 0.2);
        border-bottom: 2px solid rgba(124, 58, 237, 0.5);
        cursor: pointer;
        transition: background-color 0.2s;
      }

      .continuum-highlight:hover {
        background-color: rgba(124, 58, 237, 0.3);
      }

      .continuum-highlight-tooltip {
        position: absolute;
        background: #1f2937;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        z-index: 10000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s;
      }

      .continuum-highlight:hover + .continuum-highlight-tooltip {
        opacity: 1;
      }
    `;
    document.head.appendChild(style);
    return style;
  }

  /**
   * Highlight text on page
   */
  highlight(text: string, memoryId: string, color?: string) {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          // Skip script, style, and already highlighted nodes
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;

          const tagName = parent.tagName.toLowerCase();
          if (['script', 'style', 'noscript'].includes(tagName)) {
            return NodeFilter.FILTER_REJECT;
          }

          if (parent.classList.contains('continuum-highlight')) {
            return NodeFilter.FILTER_REJECT;
          }

          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    const textNodes: Text[] = [];
    let node;
    while ((node = walker.nextNode())) {
      textNodes.push(node as Text);
    }

    const highlights: HighlightInfo[] = [];

    textNodes.forEach(textNode => {
      const nodeText = textNode.textContent || '';
      const index = nodeText.indexOf(text);

      if (index === -1) return;

      const range = document.createRange();
      range.setStart(textNode, index);
      range.setEnd(textNode, index + text.length);

      const span = document.createElement('span');
      span.className = 'continuum-highlight';
      span.setAttribute('data-memory-id', memoryId);
      if (color) {
        span.style.backgroundColor = color;
      }

      range.surroundContents(span);

      // Add tooltip
      const tooltip = document.createElement('div');
      tooltip.className = 'continuum-highlight-tooltip';
      tooltip.textContent = 'CONTINUUM Memory';
      span.parentElement?.insertBefore(tooltip, span.nextSibling);

      // Add click handler
      span.addEventListener('click', (event) => {
        event.preventDefault();
        this.handleHighlightClick(memoryId);
      });

      highlights.push({
        memoryId,
        range: {
          startOffset: index,
          endOffset: index + text.length,
          text,
        },
        color: color || 'rgba(124, 58, 237, 0.2)',
      });
    });

    this.highlights.set(memoryId, highlights);
  }

  /**
   * Highlight memory by ID
   */
  highlightMemory(memoryId: string) {
    // Find memory content and highlight
    // This would query the API for memory details
    console.log('Highlighting memory:', memoryId);
  }

  /**
   * Handle highlight click
   */
  private handleHighlightClick(memoryId: string) {
    // Open sidebar with memory details
    window.postMessage({
      type: 'CONTINUUM_SHOW_MEMORY',
      memoryId,
    }, '*');
  }

  /**
   * Remove all highlights
   */
  clearHighlights() {
    document.querySelectorAll('.continuum-highlight').forEach(el => {
      const parent = el.parentNode;
      if (parent) {
        const textNode = document.createTextNode(el.textContent || '');
        parent.replaceChild(textNode, el);
      }
    });

    document.querySelectorAll('.continuum-highlight-tooltip').forEach(el => {
      el.remove();
    });

    this.highlights.clear();
  }

  /**
   * Remove highlights for specific memory
   */
  removeHighlight(memoryId: string) {
    document.querySelectorAll(`[data-memory-id="${memoryId}"]`).forEach(el => {
      const parent = el.parentNode;
      if (parent) {
        const textNode = document.createTextNode(el.textContent || '');
        parent.replaceChild(textNode, el);
      }
    });

    this.highlights.delete(memoryId);
  }

  /**
   * Cleanup
   */
  destroy() {
    this.clearHighlights();
    this.styleElement.remove();
  }
}
