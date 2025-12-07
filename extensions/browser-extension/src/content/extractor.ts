/**
 * Page Content Extractor
 * Intelligently extracts content from different page types
 */

import type { ContentExtractionResult } from '../shared/types';

export class PageExtractor {
  /**
   * Extract page content based on page type
   */
  extractPageContent(): ContentExtractionResult {
    const url = window.location.href;
    const hostname = window.location.hostname;

    // Detect page type
    if (hostname.includes('github.com')) {
      return this.extractGitHub();
    } else if (hostname.includes('twitter.com') || hostname.includes('x.com')) {
      return this.extractTwitter();
    } else if (hostname.includes('youtube.com')) {
      return this.extractYouTube();
    } else if (this.isCodePage()) {
      return this.extractCode();
    } else if (this.isArticle()) {
      return this.extractArticle();
    } else {
      return this.extractGeneric();
    }
  }

  /**
   * Extract article content
   */
  private extractArticle(): ContentExtractionResult {
    // Try to find article element
    const article = document.querySelector('article');
    const main = document.querySelector('main');
    const content = article || main || document.body;

    // Extract metadata
    const author = this.getMetaContent('author') ||
      document.querySelector('[rel="author"]')?.textContent ||
      document.querySelector('.author')?.textContent;

    const publishedDate = this.getMetaContent('article:published_time') ||
      this.getMetaContent('publishedDate') ||
      document.querySelector('time')?.getAttribute('datetime');

    const tags = this.extractTags();

    // Extract text content
    const text = this.extractTextContent(content);

    return {
      type: 'article',
      content: text,
      metadata: {
        author: author || undefined,
        publishedDate: publishedDate || undefined,
        tags,
      },
    };
  }

  /**
   * Extract code content
   */
  private extractCode(): ContentExtractionResult {
    const codeBlocks = Array.from(document.querySelectorAll('pre code, pre'));
    const code = codeBlocks.map(block => block.textContent).join('\n\n');

    const language = this.detectLanguage();

    return {
      type: 'code',
      content: code,
      metadata: {
        codeLanguage: language,
      },
    };
  }

  /**
   * Extract GitHub content
   */
  private extractGitHub(): ContentExtractionResult {
    const readme = document.querySelector('.markdown-body');
    const code = document.querySelector('.blob-code');

    const content = readme?.textContent || code?.textContent || '';

    return {
      type: 'github',
      content: content.trim(),
      metadata: {
        codeLanguage: this.detectLanguage(),
      },
    };
  }

  /**
   * Extract Twitter content
   */
  private extractTwitter(): ContentExtractionResult {
    const tweet = document.querySelector('[data-testid="tweetText"]');
    const author = document.querySelector('[data-testid="User-Name"]');

    return {
      type: 'tweet',
      content: tweet?.textContent || '',
      metadata: {
        author: author?.textContent || undefined,
      },
    };
  }

  /**
   * Extract YouTube content
   */
  private extractYouTube(): ContentExtractionResult {
    const title = document.querySelector('h1.ytd-watch-metadata')?.textContent;
    const description = document.querySelector('#description')?.textContent;
    const videoId = new URLSearchParams(window.location.search).get('v');

    return {
      type: 'video',
      content: `${title}\n\n${description}`,
      metadata: {
        videoId: videoId || undefined,
      },
    };
  }

  /**
   * Extract generic page content
   */
  private extractGeneric(): ContentExtractionResult {
    const main = document.querySelector('main') || document.body;
    const text = this.extractTextContent(main);

    return {
      type: 'web',
      content: text,
      metadata: {},
    };
  }

  /**
   * Extract text content from element
   */
  private extractTextContent(element: Element): string {
    // Clone element to avoid modifying DOM
    const clone = element.cloneNode(true) as Element;

    // Remove unwanted elements
    clone.querySelectorAll('script, style, nav, header, footer, aside, .ad, .advertisement')
      .forEach(el => el.remove());

    // Get text content
    const text = clone.textContent || '';

    // Clean up whitespace
    return text
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 10000); // Limit to 10k chars
  }

  /**
   * Get selection context (surrounding text)
   */
  getSelectionContext(selection: string, contextSize = 200): string {
    const fullText = document.body.textContent || '';
    const index = fullText.indexOf(selection);

    if (index === -1) return '';

    const start = Math.max(0, index - contextSize);
    const end = Math.min(fullText.length, index + selection.length + contextSize);

    return fullText.slice(start, end);
  }

  /**
   * Get page summary
   */
  getPageSummary(): string {
    const description = this.getMetaContent('description') ||
      this.getMetaContent('og:description');

    if (description) return description;

    // Extract first paragraph
    const firstP = document.querySelector('p');
    return firstP?.textContent?.slice(0, 300) || '';
  }

  /**
   * Get meta content
   */
  private getMetaContent(name: string): string | null {
    const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    return meta?.getAttribute('content') || null;
  }

  /**
   * Extract tags
   */
  private extractTags(): string[] {
    const keywords = this.getMetaContent('keywords');
    if (keywords) {
      return keywords.split(',').map(k => k.trim());
    }

    const tags = Array.from(document.querySelectorAll('.tag, .label, [class*="tag"]'));
    return tags.map(tag => tag.textContent?.trim() || '').filter(Boolean);
  }

  /**
   * Detect if page is an article
   */
  private isArticle(): boolean {
    return !!(
      document.querySelector('article') ||
      this.getMetaContent('article:published_time') ||
      document.querySelector('.post, .article, .blog-post')
    );
  }

  /**
   * Detect if page contains code
   */
  private isCodePage(): boolean {
    return !!(
      document.querySelector('pre code') ||
      document.querySelector('.hljs') ||
      document.querySelector('.language-')
    );
  }

  /**
   * Detect programming language
   */
  private detectLanguage(): string | undefined {
    const codeBlock = document.querySelector('pre code');
    if (!codeBlock) return undefined;

    // Check class names
    const className = codeBlock.className;
    const match = className.match(/language-(\w+)|lang-(\w+)/);
    if (match) return match[1] || match[2];

    // Detect from file extension in title
    const title = document.title;
    const extMatch = title.match(/\.(\w+)$/);
    if (extMatch) {
      const ext = extMatch[1];
      const langMap: Record<string, string> = {
        js: 'javascript',
        ts: 'typescript',
        py: 'python',
        rb: 'ruby',
        rs: 'rust',
        go: 'go',
        java: 'java',
      };
      return langMap[ext] || ext;
    }

    return undefined;
  }
}
