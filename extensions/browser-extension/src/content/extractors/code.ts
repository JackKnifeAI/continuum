/**
 * Code Snippet Extractor
 */

export class CodeExtractor {
  extract(): { content: string; metadata: Record<string, any> } {
    const codeBlocks = this.findCodeBlocks();
    const content = codeBlocks.map(block => block.textContent).join('\n\n');
    const metadata = {
      language: this.detectLanguage(),
      blockCount: codeBlocks.length,
    };

    return { content, metadata };
  }

  private findCodeBlocks(): Element[] {
    return Array.from(document.querySelectorAll('pre code, pre'));
  }

  private detectLanguage(): string | null {
    const codeBlock = document.querySelector('pre code');
    if (!codeBlock) return null;

    const className = codeBlock.className;
    const match = className.match(/language-(\w+)|lang-(\w+)/);

    return match ? (match[1] || match[2]) : null;
  }
}
