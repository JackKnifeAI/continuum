/**
 * View Entity command - Display entity details
 */

import * as vscode from 'vscode';
import { EntityItem } from '../types';

export async function viewEntityCommand(item: any): Promise<void> {
  try {
    if (!item || !item.entity) {
      vscode.window.showWarningMessage('No entity selected');
      return;
    }

    const entity: EntityItem = item.entity;

    // Create entity details document
    const content = formatEntityDetails(entity);
    const doc = await vscode.workspace.openTextDocument({
      content,
      language: 'markdown',
    });

    await vscode.window.showTextDocument(doc, {
      preview: true,
      viewColumn: vscode.ViewColumn.Beside,
    });
  } catch (error) {
    vscode.window.showErrorMessage(
      `Failed to view entity: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

function formatEntityDetails(entity: EntityItem): string {
  return `# ${entity.name}

**Type:** ${entity.type}

${entity.description ? `**Description:** ${entity.description}` : ''}

${entity.created_at ? `**Created:** ${new Date(entity.created_at).toLocaleString()}` : ''}

---

*Entity from Continuum Knowledge Graph*
`;
}
