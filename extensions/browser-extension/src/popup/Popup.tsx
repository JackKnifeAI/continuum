/**
 * Popup Component
 * Main popup UI for CONTINUUM extension
 */

import React, { useState, useEffect } from 'react';
import { QuickCapture } from './QuickCapture';
import { RecentMemories } from './RecentMemories';
import { QuickSearch } from './QuickSearch';
import { Stats } from './Stats';
import { sendToBackground } from '../shared/messaging';
import type { Memory, SyncStatus } from '../shared/types';

export const Popup: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'capture' | 'search' | 'recent'>('capture');
  const [recentMemories, setRecentMemories] = useState<Memory[]>([]);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);

      // Load sync status
      const status = await sendToBackground<void, SyncStatus>({
        type: 'SYNC_STATUS',
        payload: undefined,
      });
      setSyncStatus(status);

      // Load recent memories (would come from API)
      // For now, mock data
      setRecentMemories([]);

      setIsLoading(false);
    } catch (error) {
      console.error('Failed to load popup data:', error);
      setIsLoading(false);
    }
  };

  const handleCapture = async (content: string) => {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });

    await sendToBackground({
      type: 'CAPTURE_SELECTION',
      payload: {
        content,
        source: {
          type: 'web',
          url: tab?.url || '',
          title: tab?.title || '',
          domain: tab?.url ? new URL(tab.url).hostname : '',
        },
      },
    });

    // Reload recent memories
    await loadData();
  };

  const handleSearch = async (query: string) => {
    await sendToBackground({
      type: 'QUICK_SEARCH',
      payload: query,
    });
  };

  if (isLoading) {
    return (
      <div className="popup-container loading">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="popup-container">
      <header className="popup-header">
        <div className="logo">
          <span className="logo-icon">∞</span>
          <span className="logo-text">CONTINUUM</span>
        </div>

        {syncStatus && (
          <div className={`sync-indicator ${syncStatus.isOnline ? 'online' : 'offline'}`}>
            <span className="sync-dot" />
            {syncStatus.pendingItems > 0 && (
              <span className="pending-count">{syncStatus.pendingItems}</span>
            )}
          </div>
        )}
      </header>

      <nav className="popup-tabs">
        <button
          className={`tab ${activeTab === 'capture' ? 'active' : ''}`}
          onClick={() => setActiveTab('capture')}
        >
          Capture
        </button>
        <button
          className={`tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          Search
        </button>
        <button
          className={`tab ${activeTab === 'recent' ? 'active' : ''}`}
          onClick={() => setActiveTab('recent')}
        >
          Recent
        </button>
      </nav>

      <main className="popup-content">
        {activeTab === 'capture' && (
          <QuickCapture onCapture={handleCapture} />
        )}

        {activeTab === 'search' && (
          <QuickSearch onSearch={handleSearch} />
        )}

        {activeTab === 'recent' && (
          <RecentMemories memories={recentMemories} />
        )}
      </main>

      <footer className="popup-footer">
        <Stats syncStatus={syncStatus} />

        <button
          className="settings-button"
          onClick={() => browser.runtime.openOptionsPage()}
        >
          Settings
        </button>
      </footer>
    </div>
  );
};
