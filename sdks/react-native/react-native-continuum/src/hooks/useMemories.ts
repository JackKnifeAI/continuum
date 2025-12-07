/**
 * Hook for fetching and managing a list of memories
 */

import { useState, useEffect, useCallback } from 'react';
import { useContinuum } from './useContinuum';
import type { Memory, MemoryFilter, UseMemoriesResult } from '../types';

export function useMemories(filter?: MemoryFilter): UseMemoriesResult {
  const client = useContinuum();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);

  const fetchMemories = useCallback(
    async (reset = false) => {
      try {
        setIsLoading(true);
        setError(null);

        const currentOffset = reset ? 0 : offset;
        const result = await client.getMemories({
          ...filter,
          offset: currentOffset,
        });

        if (reset) {
          setMemories(result);
          setOffset(result.length);
        } else {
          setMemories((prev) => [...prev, ...result]);
          setOffset((prev) => prev + result.length);
        }

        setHasMore(result.length === (filter?.limit || 20));
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    },
    [client, filter, offset]
  );

  const refetch = useCallback(async () => {
    await fetchMemories(true);
  }, [fetchMemories]);

  const loadMore = useCallback(async () => {
    if (!isLoading && hasMore) {
      await fetchMemories(false);
    }
  }, [isLoading, hasMore, fetchMemories]);

  useEffect(() => {
    fetchMemories(true);
  }, [filter?.type, filter?.source]); // Only re-fetch on key filter changes

  return {
    memories,
    isLoading,
    error,
    refetch,
    loadMore,
    hasMore,
  };
}
