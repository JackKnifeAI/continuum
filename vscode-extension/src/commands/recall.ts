/**
 * Recall command - Get relevant context for current work
 */

import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';

export async function recallCommand(): Promise<void> {
  try {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('No active editor');
      return;
    }

    // Get context from current file
    const fileName = editor.document.fileName;
    const language = editor.document.languageId;
    const selection = editor.selection;
    const selectedText = editor.document.getText(selection);

    // Build query from context
    let query: string;
    if (selectedText && selectedText.trim().length > 0) {
      query = selectedText;
    } else {
      // Use file name and prompt user
      const userQuery = await vscode.window.showInputBox({
        prompt: 'What context do you need?',
        placeHolder: `e.g., "How to implement ${language} authentication"`,
      });

      if (!userQuery) {
        return; // User cancelled
      }

      query = userQuery;
    }

    // Show progress
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Recalling from Continuum memory...',
        cancellable: false,
      },
      async () => {
        const client = getApiClient();
        const result = await client.recall(query);

        if (result.concepts_found === 0) {
          vscode.window.showInformationMessage(
            `No relevant memories found for: ${query}`
          );
          return;
        }

        // Show context in new editor with rich formatting
        const doc = await vscode.workspace.openTextDocument({
          content: formatRecallResults(query, result.context, result, fileName),
          language: 'markdown',
        });

        await vscode.window.showTextDocument(doc, {
          preview: true,
          viewColumn: vscode.ViewColumn.Beside,
        });

        vscode.window.showInformationMessage(
          `Found ${result.concepts_found} relevant concepts (${result.query_time_ms.toFixed(0)}ms)`
        );
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(
      `Recall failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

function formatRecallResults(
  query: string,
  context: string,
  result: { concepts_found: number; relationships_found: number; query_time_ms: number },
  fileName: string
): string {
  return `# Continuum Memory Recall

**Context for:** ${fileName}

**Query:** ${query}

**Found:** ${result.concepts_found} concepts, ${result.relationships_found} relationships

---

## Relevant Memories

${context}

---

*Query time: ${result.query_time_ms.toFixed(2)}ms*
`;
}
