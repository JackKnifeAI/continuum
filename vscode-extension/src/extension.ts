/**
 * Continuum Memory Extension for VS Code
 *
 * Provides AI memory persistence and knowledge graph integration.
 */

import * as vscode from 'vscode';
import { MemoryTreeDataProvider } from './providers/memoryTreeProvider';
import { HoverProvider } from './providers/hoverProvider';
import { CompletionProvider } from './providers/completionProvider';
import { StatusBarManager } from './utils/statusBar';
import { getApiClient, updateApiClient } from './utils/apiClient';
import { registerCommands } from './commands';

let statusBarManager: StatusBarManager;
let memoryTreeProvider: MemoryTreeDataProvider;
let syncInterval: NodeJS.Timeout | undefined;

/**
 * Extension activation
 */
export function activate(context: vscode.ExtensionContext) {
  console.log('Continuum Memory extension is now active');

  // Initialize status bar
  statusBarManager = new StatusBarManager();
  context.subscriptions.push(statusBarManager);

  // Initialize memory tree provider
  memoryTreeProvider = new MemoryTreeDataProvider(context);
  const treeView = vscode.window.createTreeView('continuumMemoryExplorer', {
    treeDataProvider: memoryTreeProvider,
    showCollapseAll: true,
  });
  context.subscriptions.push(treeView);

  // Register all commands
  registerCommands(context, memoryTreeProvider, statusBarManager);

  // Register hover provider if enabled
  const config = vscode.workspace.getConfiguration('continuum');
  if (config.get<boolean>('enableHover', true)) {
    const hoverProvider = new HoverProvider();
    context.subscriptions.push(
      vscode.languages.registerHoverProvider(
        { scheme: 'file', pattern: '**/*' },
        hoverProvider
      )
    );
  }

  // Register completion provider if enabled (experimental)
  if (config.get<boolean>('enableCompletions', false)) {
    const completionProvider = new CompletionProvider();
    context.subscriptions.push(
      vscode.languages.registerCompletionItemProvider(
        { scheme: 'file', pattern: '**/*' },
        completionProvider
      )
    );
  }

  // Setup auto-sync if enabled
  setupAutoSync(context);

  // Listen for configuration changes
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration('continuum')) {
        handleConfigChange();
      }
    })
  );

  // Show welcome message on first activation
  const hasShownWelcome = context.globalState.get<boolean>('hasShownWelcome', false);
  if (!hasShownWelcome) {
    showWelcomeMessage(context);
  }

  // Test connection on activation
  testConnection();

  return {
    // Export API for other extensions
    getApiClient,
    recall: async (message: string) => {
      const client = getApiClient();
      return await client.recall(message);
    },
    learn: async (userMessage: string, aiResponse: string) => {
      const client = getApiClient();
      return await client.learn(userMessage, aiResponse);
    },
  };
}

/**
 * Extension deactivation
 */
export function deactivate() {
  if (syncInterval) {
    clearInterval(syncInterval);
  }
  console.log('Continuum Memory extension deactivated');
}

/**
 * Setup automatic sync
 */
function setupAutoSync(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration('continuum');
  const autoSync = config.get<boolean>('autoSync', true);
  const syncIntervalSeconds = config.get<number>('syncInterval', 300);

  // Clear existing interval
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = undefined;
  }

  if (autoSync && syncIntervalSeconds > 0) {
    syncInterval = setInterval(async () => {
      try {
        await memoryTreeProvider.refresh();
        statusBarManager.updateLastSync(new Date());
      } catch (error) {
        console.error('Auto-sync failed:', error);
      }
    }, syncIntervalSeconds * 1000);

    context.subscriptions.push({
      dispose: () => {
        if (syncInterval) {
          clearInterval(syncInterval);
        }
      },
    });
  }

  // Sync on file save if auto-sync enabled
  if (autoSync) {
    context.subscriptions.push(
      vscode.workspace.onDidSaveTextDocument(async () => {
        await memoryTreeProvider.refresh();
      })
    );
  }
}

/**
 * Handle configuration changes
 */
function handleConfigChange() {
  const config = vscode.workspace.getConfiguration('continuum');

  // Update API client config
  updateApiClient({
    apiUrl: config.get<string>('apiUrl', 'http://localhost:8000'),
    apiKey: config.get<string>('apiKey', ''),
    tenantId: config.get<string>('tenantId', 'vscode'),
    maxConcepts: config.get<number>('maxConcepts', 10),
  });

  // Refresh tree view
  memoryTreeProvider.refresh();

  // Test new connection
  testConnection();

  vscode.window.showInformationMessage('Continuum configuration updated');
}

/**
 * Test API connection
 */
async function testConnection() {
  try {
    const client = getApiClient();
    const isConnected = await client.testConnection();

    if (isConnected) {
      statusBarManager.setConnected(true);
    } else {
      statusBarManager.setConnected(false);
      vscode.window.showWarningMessage(
        'Continuum: Unable to connect to API server. Please check your configuration.'
      );
    }
  } catch (error) {
    statusBarManager.setConnected(false);
    console.error('Connection test failed:', error);
  }
}

/**
 * Show welcome message on first activation
 */
async function showWelcomeMessage(context: vscode.ExtensionContext) {
  const action = await vscode.window.showInformationMessage(
    'Welcome to Continuum Memory! Would you like to configure your connection?',
    'Configure',
    'Later'
  );

  if (action === 'Configure') {
    vscode.commands.executeCommand('continuum.configure');
  }

  await context.globalState.update('hasShownWelcome', true);
}
