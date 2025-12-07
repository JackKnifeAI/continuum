/**
 * GitHub Content Extractor
 */

export class GitHubExtractor {
  extract(): { content: string; metadata: Record<string, any> } {
    const url = window.location.href;

    if (url.includes('/blob/')) {
      return this.extractFileContent();
    } else if (url.includes('/issues/') || url.includes('/pull/')) {
      return this.extractIssueContent();
    } else {
      return this.extractReadme();
    }
  }

  private extractFileContent() {
    const code = document.querySelector('.blob-code')?.textContent || '';
    const language = this.detectLanguage();

    return {
      content: code,
      metadata: { type: 'code', language },
    };
  }

  private extractIssueContent() {
    const title = document.querySelector('.js-issue-title')?.textContent || '';
    const body = document.querySelector('.comment-body')?.textContent || '';

    return {
      content: `${title}\n\n${body}`,
      metadata: { type: 'issue' },
    };
  }

  private extractReadme() {
    const readme = document.querySelector('.markdown-body')?.textContent || '';

    return {
      content: readme,
      metadata: { type: 'readme' },
    };
  }

  private detectLanguage(): string | null {
    const langSpan = document.querySelector('[data-code-language]');
    return langSpan?.getAttribute('data-code-language') || null;
  }
}
