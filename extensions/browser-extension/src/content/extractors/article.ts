/**
 * Article Content Extractor
 * Extracts main article content from web pages
 */

export class ArticleExtractor {
  extract(): { content: string; metadata: Record<string, any> } {
    const article = this.findArticleElement();
    const content = this.extractContent(article);
    const metadata = this.extractMetadata();

    return { content, metadata };
  }

  private findArticleElement(): Element {
    // Try common article selectors
    const selectors = [
      'article',
      '[role="article"]',
      '.article-content',
      '.post-content',
      'main article',
      '#article',
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) return element;
    }

    // Fallback to main
    return document.querySelector('main') || document.body;
  }

  private extractContent(element: Element): string {
    const clone = element.cloneNode(true) as Element;

    // Remove unwanted elements
    clone.querySelectorAll('script, style, nav, header, footer, aside, .ad').forEach(el => el.remove());

    return clone.textContent?.trim().slice(0, 50000) || '';
  }

  private extractMetadata() {
    return {
      author: this.getMeta('author'),
      publishedDate: this.getMeta('article:published_time'),
      modifiedDate: this.getMeta('article:modified_time'),
      section: this.getMeta('article:section'),
    };
  }

  private getMeta(name: string): string | null {
    const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    return meta?.getAttribute('content') || null;
  }
}
