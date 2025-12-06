/**
 * Store Selection command - Store selected text as memory
 */

import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';

export async function storeSelectionCommand(): Promise<void> {
  try {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('No active editor');
      return;
    }

    const selection = editor.selection;
    const selectedText = editor.document.getText(selection);

    if (!selectedText || selectedText.trim().length === 0) {
      vscode.window.showWarningMessage('No text selected');
      return;
    }

    // Get context about the selection
    const fileName = editor.document.fileName;
    const lineNumber = selection.start.line + 1;
    const language = editor.document.languageId;

    // Prompt for additional context
    const userContext = await vscode.window.showInputBox({
      prompt: 'Add context about this selection (optional)',
      placeHolder: 'e.g., "Important implementation detail" or "Bug fix approach"',
    });

    if (userContext === undefined) {
      return; // User cancelled
    }

    // Show progress
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Storing in Continuum memory...',
        cancellable: false,
      },
      async () => {
        const client = getApiClient();

        // Create a structured message
        const userMessage = userContext || 'Code selection stored';
        const aiResponse = `Stored code snippet from ${fileName}:${lineNumber}

\`\`\`${language}
${selectedText}
\`\`\`

Context: ${userContext || 'No additional context provided'}`;

        const result = await client.learn(userMessage, aiResponse, {
          source: 'vscode',
          file: fileName,
          line: lineNumber,
          language: language,
        });

        vscode.window.showInformationMessage(
          `Stored in memory: ${result.concepts_extracted} concepts, ${result.decisions_detected} decisions`
        );
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(
      `Failed to store selection: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}
