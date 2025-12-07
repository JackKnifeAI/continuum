/**
 * Hook for searching memories with debouncing
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useContinuum } from './useContinuum';
import type { SearchResult, SearchOptions, UseSearchResult } from '../types';

export function useSearch(
  initialQuery = '',
  debounceMs = 300
): UseSearchResult {
  const client = useContinuum();
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [query, setQuery] = useState(initialQuery);
  const debounceTimer = useRef<NodeJS.Timeout>();

  const performSearch = useCallback(
    async (searchQuery: string, options?: SearchOptions) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const searchResults = await client.searchMemories(searchQuery, options);
        setResults(searchResults);
      } catch (err) {
        setError(err as Error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    [client]
  );

  const search = useCallback(
    (searchQuery: string, options?: SearchOptions) => {
      setQuery(searchQuery);

      // Clear existing timer
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }

      // Debounce search
      debounceTimer.current = setTimeout(() => {
        performSearch(searchQuery, options);
      }, debounceMs);
    },
    [performSearch, debounceMs]
  );

  const clear = useCallback(() => {
    setQuery('');
    setResults([]);
    setError(null);
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  return {
    results,
    isLoading,
    error,
    search,
    clear,
  };
}
