/**
 * Configure command - Setup Continuum connection
 */

import * as vscode from 'vscode';
import { getApiClient, updateApiClient } from '../utils/apiClient';

export async function configureCommand(): Promise<void> {
  try {
    const config = vscode.workspace.getConfiguration('continuum');

    // Get API URL
    const apiUrl = await vscode.window.showInputBox({
      prompt: 'Continuum API Server URL',
      value: config.get<string>('apiUrl', 'http://localhost:8000'),
      placeHolder: 'http://localhost:8000',
      validateInput: (value) => {
        try {
          new URL(value);
          return undefined;
        } catch {
          return 'Invalid URL';
        }
      },
    });

    if (!apiUrl) {
      return; // User cancelled
    }

    // Get tenant ID
    const tenantId = await vscode.window.showInputBox({
      prompt: 'Tenant ID',
      value: config.get<string>('tenantId', 'vscode'),
      placeHolder: 'vscode',
      validateInput: (value) => {
        return value.trim().length === 0 ? 'Tenant ID cannot be empty' : undefined;
      },
    });

    if (!tenantId) {
      return; // User cancelled
    }

    // Get API key
    const apiKeyOption = await vscode.window.showQuickPick(
      ['Enter API key now', 'Configure later'],
      {
        placeHolder: 'API Key Configuration',
      }
    );

    let apiKey = '';
    if (apiKeyOption === 'Enter API key now') {
      const key = await vscode.window.showInputBox({
        prompt: 'API Key (will be stored in VS Code settings)',
        password: true,
        placeHolder: 'cm_...',
        validateInput: (value) => {
          if (value.trim().length === 0) {
            return 'API key cannot be empty';
          }
          if (!value.startsWith('cm_')) {
            return 'API key should start with "cm_"';
          }
          return undefined;
        },
      });

      if (key) {
        apiKey = key;
      }
    }

    // Update configuration
    await config.update('apiUrl', apiUrl, vscode.ConfigurationTarget.Global);
    await config.update('tenantId', tenantId, vscode.ConfigurationTarget.Global);
    if (apiKey) {
      await config.update('apiKey', apiKey, vscode.ConfigurationTarget.Global);
    }

    // Update API client
    updateApiClient({
      apiUrl,
      tenantId,
      apiKey,
    });

    // Test connection
    vscode.window.showInformationMessage('Testing connection...');
    const client = getApiClient();
    const isConnected = await client.testConnection();

    if (isConnected) {
      vscode.window.showInformationMessage(
        'Continuum configured successfully! Connection verified.'
      );
    } else {
      vscode.window.showWarningMessage(
        'Configuration saved, but unable to connect to server. Please check your settings.'
      );
    }
  } catch (error) {
    vscode.window.showErrorMessage(
      `Configuration failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}
