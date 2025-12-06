/**
 * Sync command - Manually sync with Continuum server
 */

import * as vscode from 'vscode';
import { MemoryTreeDataProvider } from '../providers/memoryTreeProvider';
import { StatusBarManager } from '../utils/statusBar';

export async function syncCommand(
  memoryTreeProvider: MemoryTreeDataProvider,
  statusBarManager: StatusBarManager
): Promise<void> {
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Syncing with Continuum...',
        cancellable: false,
      },
      async () => {
        await memoryTreeProvider.refresh();
        statusBarManager.updateLastSync(new Date());
      }
    );

    vscode.window.showInformationMessage('Continuum sync completed successfully');
  } catch (error) {
    vscode.window.showErrorMessage(
      `Sync failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}
