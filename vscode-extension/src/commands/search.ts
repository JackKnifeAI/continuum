/**
 * Search command - Search memory for concepts/entities
 */

import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';
import { MemoryTreeDataProvider } from '../providers/memoryTreeProvider';

export async function searchCommand(
  memoryTreeProvider: MemoryTreeDataProvider
): Promise<void> {
  try {
    // Prompt for search query
    const query = await vscode.window.showInputBox({
      prompt: 'Search Continuum memory',
      placeHolder: 'Enter search query...',
      validateInput: (value) => {
        return value.trim().length === 0 ? 'Query cannot be empty' : undefined;
      },
    });

    if (!query) {
      return; // User cancelled
    }

    // Show progress
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Searching Continuum memory...',
        cancellable: false,
      },
      async () => {
        const client = getApiClient();
        const result = await client.recall(query);

        // Display results
        if (result.concepts_found === 0) {
          vscode.window.showInformationMessage(
            `No memories found for "${query}"`
          );
          return;
        }

        // Show results in new editor
        const doc = await vscode.workspace.openTextDocument({
          content: formatSearchResults(query, result.context, result),
          language: 'markdown',
        });

        await vscode.window.showTextDocument(doc, {
          preview: true,
          viewColumn: vscode.ViewColumn.Beside,
        });

        // Refresh tree view
        await memoryTreeProvider.refresh();
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(
      `Search failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

function formatSearchResults(
  query: string,
  context: string,
  result: { concepts_found: number; relationships_found: number; query_time_ms: number }
): string {
  return `# Continuum Search Results

**Query:** ${query}

**Stats:**
- Concepts found: ${result.concepts_found}
- Relationships found: ${result.relationships_found}
- Query time: ${result.query_time_ms.toFixed(2)}ms

---

## Context

${context}

---

*Results from Continuum Memory API*
`;
}
