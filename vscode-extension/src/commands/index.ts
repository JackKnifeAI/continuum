/**
 * Command registration for Continuum extension
 */

import * as vscode from 'vscode';
import { searchCommand } from './search';
import { storeSelectionCommand } from './store';
import { recallCommand } from './recall';
import { syncCommand } from './sync';
import { showStatsCommand } from './stats';
import { configureCommand } from './configure';
import { viewEntityCommand } from './viewEntity';
import { MemoryTreeDataProvider } from '../providers/memoryTreeProvider';
import { StatusBarManager } from '../utils/statusBar';

export function registerCommands(
  context: vscode.ExtensionContext,
  memoryTreeProvider: MemoryTreeDataProvider,
  statusBarManager: StatusBarManager
): void {
  // Search command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.search', () =>
      searchCommand(memoryTreeProvider)
    )
  );

  // Store selection command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.storeSelection', () =>
      storeSelectionCommand()
    )
  );

  // Recall command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.recall', () => recallCommand())
  );

  // Sync command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.sync', () =>
      syncCommand(memoryTreeProvider, statusBarManager)
    )
  );

  // Show stats command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.showStats', () => showStatsCommand())
  );

  // Configure command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.configure', () => configureCommand())
  );

  // Refresh memories command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.refreshMemories', () =>
      memoryTreeProvider.refresh()
    )
  );

  // View entity command
  context.subscriptions.push(
    vscode.commands.registerCommand('continuum.viewEntity', (item) =>
      viewEntityCommand(item)
    )
  );
}
