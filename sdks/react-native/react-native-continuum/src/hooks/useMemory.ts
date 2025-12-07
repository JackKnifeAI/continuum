/**
 * Hook for fetching a single memory by ID
 */

import { useState, useEffect, useCallback } from 'react';
import { useContinuum } from './useContinuum';
import type { Memory, UseMemoryResult } from '../types';

export function useMemory(id: string): UseMemoryResult {
  const client = useContinuum();
  const [memory, setMemory] = useState<Memory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchMemory = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await client.getMemory(id);
      setMemory(result);
    } catch (err) {
      setError(err as Error);
      setMemory(null);
    } finally {
      setIsLoading(false);
    }
  }, [client, id]);

  useEffect(() => {
    if (id) {
      fetchMemory();
    }
  }, [id, fetchMemory]);

  return {
    memory,
    isLoading,
    error,
    refetch: fetchMemory,
  };
}
