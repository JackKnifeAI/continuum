/**
 * Hover Provider
 *
 * Shows memory context when hovering over code.
 */

import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';

export class HoverProvider implements vscode.HoverProvider {
  /**
   * Provide hover information
   */
  async provideHover(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken
  ): Promise<vscode.Hover | null> {
    // Get the word or phrase at the hover position
    const wordRange = document.getWordRangeAtPosition(position);
    if (!wordRange) {
      return null;
    }

    const word = document.getText(wordRange);
    if (!word || word.length < 3) {
      return null; // Skip very short words
    }

    // Check if this is a significant term (avoid common keywords)
    if (this.isCommonKeyword(word, document.languageId)) {
      return null;
    }

    try {
      // Query memory for context (with shorter timeout for hover)
      const client = getApiClient();
      const result = await Promise.race([
        client.recall(word, 3), // Limit to 3 concepts for hover
        new Promise<null>((resolve) => setTimeout(() => resolve(null), 1000)), // 1 second timeout
      ]);

      if (!result || result.concepts_found === 0) {
        return null;
      }

      // Format context as markdown
      const markdown = new vscode.MarkdownString();
      markdown.isTrusted = true;
      markdown.supportHtml = true;

      markdown.appendMarkdown(`### Continuum Memory\n\n`);
      markdown.appendMarkdown(
        `*Found ${result.concepts_found} related concept(s)*\n\n`
      );

      // Show abbreviated context
      const lines = result.context.split('\n').slice(0, 5);
      markdown.appendMarkdown(lines.join('\n'));

      if (result.context.split('\n').length > 5) {
        markdown.appendMarkdown('\n\n*...(more)*');
      }

      return new vscode.Hover(markdown, wordRange);
    } catch (error) {
      // Silently fail - hover shouldn't be intrusive
      return null;
    }
  }

  /**
   * Check if a word is a common programming keyword
   */
  private isCommonKeyword(word: string, languageId: string): boolean {
    const commonKeywords = new Set([
      // General
      'var',
      'let',
      'const',
      'function',
      'class',
      'if',
      'else',
      'for',
      'while',
      'return',
      'import',
      'export',
      'from',
      'this',
      'self',
      'true',
      'false',
      'null',
      'undefined',
      // Types
      'string',
      'number',
      'boolean',
      'object',
      'array',
      'int',
      'float',
      'void',
      // Python
      'def',
      'class',
      'pass',
      'break',
      'continue',
      'yield',
      // JavaScript/TypeScript
      'async',
      'await',
      'promise',
      'then',
      'catch',
    ]);

    return commonKeywords.has(word.toLowerCase());
  }
}
