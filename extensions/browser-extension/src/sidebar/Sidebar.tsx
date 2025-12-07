/**
 * Sidebar Component
 * Full-featured sidebar for browsing memories and concepts
 */

import React, { useState, useEffect } from 'react';
import { MemoryBrowser } from './MemoryBrowser';
import { ConceptExplorer } from './ConceptExplorer';
import { PageContext } from './PageContext';
import type { Memory, Concept, PageContext as PageContextType } from '../shared/types';

export const Sidebar: React.FC = () => {
  const [activeView, setActiveView] = useState<'page' | 'memories' | 'concepts'>('page');
  const [pageContext, setPageContext] = useState<PageContextType | null>(null);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

  useEffect(() => {
    loadPageContext();
  }, []);

  const loadPageContext = async () => {
    // Get current tab URL and load context
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    if (tab?.url) {
      // Would load from API
      setPageContext(null);
    }
  };

  return (
    <div className="sidebar-container">
      <header className="sidebar-header">
        <h1 className="sidebar-title">
          <span className="sidebar-logo">∞</span>
          CONTINUUM
        </h1>
      </header>

      <nav className="sidebar-nav">
        <button
          className={`nav-button ${activeView === 'page' ? 'active' : ''}`}
          onClick={() => setActiveView('page')}
        >
          <span className="nav-icon">📄</span>
          This Page
        </button>
        <button
          className={`nav-button ${activeView === 'memories' ? 'active' : ''}`}
          onClick={() => setActiveView('memories')}
        >
          <span className="nav-icon">💭</span>
          All Memories
        </button>
        <button
          className={`nav-button ${activeView === 'concepts' ? 'active' : ''}`}
          onClick={() => setActiveView('concepts')}
        >
          <span className="nav-icon">🔗</span>
          Concepts
        </button>
      </nav>

      <main className="sidebar-content">
        {activeView === 'page' && (
          <PageContext
            context={pageContext}
            onSelectMemory={setSelectedMemory}
          />
        )}

        {activeView === 'memories' && (
          <MemoryBrowser onSelectMemory={setSelectedMemory} />
        )}

        {activeView === 'concepts' && (
          <ConceptExplorer />
        )}
      </main>

      {selectedMemory && (
        <div className="memory-details">
          <div className="memory-details-header">
            <h3>{selectedMemory.source.title}</h3>
            <button onClick={() => setSelectedMemory(null)}>×</button>
          </div>
          <div className="memory-details-content">
            <p>{selectedMemory.content}</p>
          </div>
        </div>
      )}
    </div>
  );
};
