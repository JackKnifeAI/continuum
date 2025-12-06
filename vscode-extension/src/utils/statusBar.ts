/**
 * Status Bar Manager
 *
 * Manages the Continuum status bar item.
 */

import * as vscode from 'vscode';
import { SyncStatus } from '../types';

export class StatusBarManager {
  private statusBarItem: vscode.StatusBarItem;
  private syncStatus: SyncStatus = SyncStatus.Idle;
  private lastSync?: Date;
  private isConnected: boolean = false;

  constructor() {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.statusBarItem.command = 'continuum.showStats';
    this.updateDisplay();
    this.statusBarItem.show();
  }

  /**
   * Set connection status
   */
  setConnected(connected: boolean): void {
    this.isConnected = connected;
    this.updateDisplay();
  }

  /**
   * Update last sync time
   */
  updateLastSync(date: Date): void {
    this.lastSync = date;
    this.syncStatus = SyncStatus.Success;
    this.updateDisplay();

    // Reset to idle after a delay
    setTimeout(() => {
      this.syncStatus = SyncStatus.Idle;
      this.updateDisplay();
    }, 2000);
  }

  /**
   * Set sync status
   */
  setSyncStatus(status: SyncStatus): void {
    this.syncStatus = status;
    this.updateDisplay();
  }

  /**
   * Update status bar display
   */
  private updateDisplay(): void {
    const icon = this.getStatusIcon();
    const text = this.getStatusText();
    const tooltip = this.getTooltip();

    this.statusBarItem.text = `$(${icon}) ${text}`;
    this.statusBarItem.tooltip = tooltip;

    // Set color based on status
    if (!this.isConnected) {
      this.statusBarItem.backgroundColor = new vscode.ThemeColor(
        'statusBarItem.warningBackground'
      );
    } else if (this.syncStatus === SyncStatus.Error) {
      this.statusBarItem.backgroundColor = new vscode.ThemeColor(
        'statusBarItem.errorBackground'
      );
    } else {
      this.statusBarItem.backgroundColor = undefined;
    }
  }

  /**
   * Get status icon
   */
  private getStatusIcon(): string {
    if (!this.isConnected) {
      return 'debug-disconnect';
    }

    switch (this.syncStatus) {
      case SyncStatus.Syncing:
        return 'sync~spin';
      case SyncStatus.Success:
        return 'check';
      case SyncStatus.Error:
        return 'error';
      default:
        return 'database';
    }
  }

  /**
   * Get status text
   */
  private getStatusText(): string {
    if (!this.isConnected) {
      return 'Continuum: Disconnected';
    }

    switch (this.syncStatus) {
      case SyncStatus.Syncing:
        return 'Continuum: Syncing...';
      case SyncStatus.Success:
        return 'Continuum: Synced';
      case SyncStatus.Error:
        return 'Continuum: Error';
      default:
        return 'Continuum';
    }
  }

  /**
   * Get tooltip text
   */
  private getTooltip(): string {
    if (!this.isConnected) {
      return 'Continuum: Not connected to API server\nClick to view stats';
    }

    let tooltip = 'Continuum Memory\n';

    if (this.lastSync) {
      const timeAgo = this.getTimeAgo(this.lastSync);
      tooltip += `Last sync: ${timeAgo}\n`;
    }

    tooltip += '\nClick to view statistics';

    return tooltip;
  }

  /**
   * Get time ago string
   */
  private getTimeAgo(date: Date): string {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

    if (seconds < 60) {
      return 'just now';
    }

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
      return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    }

    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    }

    const days = Math.floor(hours / 24);
    return `${days} day${days === 1 ? '' : 's'} ago`;
  }

  /**
   * Dispose of status bar item
   */
  dispose(): void {
    this.statusBarItem.dispose();
  }
}
