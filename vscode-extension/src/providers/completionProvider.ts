/**
 * Completion Provider (Experimental)
 *
 * Provides memory-aware code completions.
 */

import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';

export class CompletionProvider implements vscode.CompletionItemProvider {
  /**
   * Provide completion items
   */
  async provideCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken,
    context: vscode.CompletionContext
  ): Promise<vscode.CompletionItem[] | null> {
    // Only trigger on manual invocation or specific characters
    if (
      context.triggerKind !== vscode.CompletionTriggerKind.Invoke &&
      context.triggerKind !== vscode.CompletionTriggerKind.TriggerCharacter
    ) {
      return null;
    }

    // Get current line text
    const linePrefix = document
      .lineAt(position)
      .text.substr(0, position.character);

    // Extract meaningful query from line
    const query = this.extractQuery(linePrefix);
    if (!query || query.length < 3) {
      return null;
    }

    try {
      // Query memory with timeout
      const client = getApiClient();
      const result = await Promise.race([
        client.recall(query, 5),
        new Promise<null>((resolve) => setTimeout(() => resolve(null), 500)),
      ]);

      if (!result || result.concepts_found === 0) {
        return null;
      }

      // Create completion items from concepts
      const items: vscode.CompletionItem[] = [];

      // Parse context for potential completions
      const concepts = this.extractConcepts(result.context);

      for (const concept of concepts) {
        const item = new vscode.CompletionItem(
          concept,
          vscode.CompletionItemKind.Reference
        );
        item.detail = 'From Continuum Memory';
        item.documentation = new vscode.MarkdownString(
          `Concept from your knowledge graph`
        );
        item.sortText = `z${concept}`; // Sort after other completions
        items.push(item);
      }

      return items.length > 0 ? items : null;
    } catch (error) {
      // Silently fail
      return null;
    }
  }

  /**
   * Extract query from line prefix
   */
  private extractQuery(linePrefix: string): string {
    // Remove leading whitespace and common prefixes
    const cleaned = linePrefix
      .trim()
      .replace(/^(const|let|var|function|class|import|export)\s+/, '');

    // Get last few words
    const words = cleaned.split(/\s+/);
    return words.slice(-3).join(' ');
  }

  /**
   * Extract potential concepts from context
   */
  private extractConcepts(context: string): string[] {
    // Simple extraction - look for capitalized words or quoted strings
    const concepts = new Set<string>();

    // Match quoted strings
    const quotedMatches = context.match(/"([^"]+)"/g);
    if (quotedMatches) {
      quotedMatches.forEach((match) => {
        const concept = match.replace(/"/g, '');
        if (concept.length > 2) {
          concepts.add(concept);
        }
      });
    }

    // Match capitalized phrases (up to 3 words)
    const capitalizedMatches = context.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b/g);
    if (capitalizedMatches) {
      capitalizedMatches.forEach((match) => {
        if (match.length > 2) {
          concepts.add(match);
        }
      });
    }

    return Array.from(concepts).slice(0, 10); // Limit to 10 concepts
  }
}
