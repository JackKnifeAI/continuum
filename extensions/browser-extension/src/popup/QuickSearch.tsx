/**
 * Quick Search Component
 */

import React, { useState, useEffect } from 'react';
import type { SearchResult } from '../shared/types';

interface QuickSearchProps {
  onSearch: (query: string) => Promise<void>;
}

export const QuickSearch: React.FC<QuickSearchProps> = ({ onSearch }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const timeoutId = setTimeout(() => {
      performSearch();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  const performSearch = async () => {
    try {
      setIsSearching(true);
      await onSearch(query);
      // Results would be received via message
      setIsSearching(false);
    } catch (error) {
      console.error('Search error:', error);
      setIsSearching(false);
    }
  };

  return (
    <div className="quick-search">
      <div className="search-box">
        <input
          type="text"
          className="search-input"
          placeholder="Search your memories..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />

        {isSearching && <div className="search-spinner" />}
      </div>

      <div className="search-results">
        {results.length === 0 && query.length >= 2 && (
          <div className="no-results">
            No memories found for "{query}"
          </div>
        )}

        {results.map((result) => (
          <div
            key={result.memory.id}
            className="search-result"
            onClick={() => {
              // Open memory details
              window.open(result.memory.source.url, '_blank');
            }}
          >
            <div className="result-title">{result.memory.source.title}</div>
            <div className="result-preview">
              {result.highlights.length > 0
                ? result.highlights[0]
                : result.memory.content.slice(0, 150)}
            </div>
            <div className="result-meta">
              <span className="result-domain">{result.memory.source.domain}</span>
              <span className="result-score">{Math.round(result.score * 100)}% match</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
