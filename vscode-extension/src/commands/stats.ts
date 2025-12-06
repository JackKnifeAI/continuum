/**
 * Show Stats command - Display memory statistics
 */

import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';

export async function showStatsCommand(): Promise<void> {
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Loading Continuum statistics...',
        cancellable: false,
      },
      async () => {
        const client = getApiClient();
        const stats = await client.getStats();

        // Create stats document
        const content = formatStats(stats);
        const doc = await vscode.workspace.openTextDocument({
          content,
          language: 'markdown',
        });

        await vscode.window.showTextDocument(doc, {
          preview: true,
          viewColumn: vscode.ViewColumn.Beside,
        });
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(
      `Failed to load stats: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

function formatStats(stats: {
  tenant_id: string;
  instance_id: string;
  entities: number;
  messages: number;
  decisions: number;
  attention_links: number;
  compound_concepts: number;
}): string {
  return `# Continuum Memory Statistics

**Tenant:** ${stats.tenant_id}
**Instance:** ${stats.instance_id}

---

## Knowledge Graph

- **Entities/Concepts:** ${stats.entities.toLocaleString()}
- **Messages Processed:** ${stats.messages.toLocaleString()}
- **Decisions Recorded:** ${stats.decisions.toLocaleString()}
- **Attention Links:** ${stats.attention_links.toLocaleString()}
- **Compound Concepts:** ${stats.compound_concepts.toLocaleString()}

---

## Total Knowledge Items

**${(
    stats.entities +
    stats.messages +
    stats.decisions +
    stats.attention_links +
    stats.compound_concepts
  ).toLocaleString()}** items in memory

---

*Stats retrieved from Continuum API*
`;
}
