/**
 * Memory Tree Data Provider
 *
 * Provides the tree view for the Continuum memory explorer sidebar.
 */

import * as vscode from 'vscode';
import { getApiClient } from '../utils/apiClient';
import { EntityItem, MemoryTreeItem } from '../types';

export class MemoryTreeDataProvider
  implements vscode.TreeDataProvider<MemoryTreeItem>
{
  private _onDidChangeTreeData = new vscode.EventEmitter<
    MemoryTreeItem | undefined | null | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private entities: EntityItem[] = [];
  private stats: any = null;

  constructor(private context: vscode.ExtensionContext) {
    this.loadData();
  }

  /**
   * Refresh the tree view
   */
  async refresh(): Promise<void> {
    await this.loadData();
    this._onDidChangeTreeData.fire();
  }

  /**
   * Get tree item for display
   */
  getTreeItem(element: MemoryTreeItem): vscode.TreeItem {
    const treeItem = new vscode.TreeItem(
      element.label,
      element.children
        ? vscode.TreeItemCollapsibleState.Collapsed
        : vscode.TreeItemCollapsibleState.None
    );

    treeItem.description = element.description;
    treeItem.tooltip = element.tooltip;
    treeItem.contextValue = element.contextValue;

    // Add icons
    if (element.contextValue === 'entity') {
      treeItem.iconPath = new vscode.ThemeIcon('symbol-class');
    } else if (element.contextValue === 'category') {
      treeItem.iconPath = new vscode.ThemeIcon('folder');
    } else if (element.contextValue === 'stat') {
      treeItem.iconPath = new vscode.ThemeIcon('graph');
    }

    return treeItem;
  }

  /**
   * Get children for tree item
   */
  async getChildren(element?: MemoryTreeItem): Promise<MemoryTreeItem[]> {
    if (!element) {
      // Root level - show categories
      return this.getRootItems();
    }

    // Return children if specified
    return element.children || [];
  }

  /**
   * Load data from API
   */
  private async loadData(): Promise<void> {
    try {
      const client = getApiClient();

      // Load entities and stats in parallel
      const [entitiesResponse, statsResponse] = await Promise.all([
        client.getEntities(50, 0),
        client.getStats(),
      ]);

      this.entities = entitiesResponse.entities;
      this.stats = statsResponse;
    } catch (error) {
      console.error('Failed to load memory data:', error);
      // Don't throw - allow tree to show error state
    }
  }

  /**
   * Get root level items
   */
  private getRootItems(): MemoryTreeItem[] {
    const items: MemoryTreeItem[] = [];

    // Statistics category
    if (this.stats) {
      items.push({
        label: 'Statistics',
        description: `${this.stats.entities} entities`,
        contextValue: 'category',
        children: this.getStatsItems(),
      });
    }

    // Recent entities
    if (this.entities.length > 0) {
      items.push({
        label: 'Recent Entities',
        description: `${this.entities.length} items`,
        contextValue: 'category',
        children: this.getEntityItems(),
      });
    }

    // If no data, show placeholder
    if (items.length === 0) {
      items.push({
        label: 'No data available',
        description: 'Check connection',
        contextValue: 'placeholder',
      });
    }

    return items;
  }

  /**
   * Get statistics items
   */
  private getStatsItems(): MemoryTreeItem[] {
    if (!this.stats) {
      return [];
    }

    return [
      {
        label: 'Entities',
        description: this.stats.entities.toLocaleString(),
        tooltip: 'Total entities and concepts in memory',
        contextValue: 'stat',
      },
      {
        label: 'Messages',
        description: this.stats.messages.toLocaleString(),
        tooltip: 'Total messages processed',
        contextValue: 'stat',
      },
      {
        label: 'Decisions',
        description: this.stats.decisions.toLocaleString(),
        tooltip: 'Total decisions recorded',
        contextValue: 'stat',
      },
      {
        label: 'Attention Links',
        description: this.stats.attention_links.toLocaleString(),
        tooltip: 'Total graph attention links',
        contextValue: 'stat',
      },
      {
        label: 'Compound Concepts',
        description: this.stats.compound_concepts.toLocaleString(),
        tooltip: 'Total compound concepts',
        contextValue: 'stat',
      },
    ];
  }

  /**
   * Get entity items
   */
  private getEntityItems(): MemoryTreeItem[] {
    return this.entities.map((entity) => ({
      label: entity.name,
      description: entity.type,
      tooltip: entity.description || entity.name,
      contextValue: 'entity',
      entity: entity,
    }));
  }
}
