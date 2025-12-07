/**
 * Mutation hook for creating memories with optimistic updates
 */

import { useState, useCallback } from 'react';
import { useContinuum } from './useContinuum';
import type { CreateMemoryInput, Memory, UseCreateMemoryMutation } from '../types';

export function useCreateMemory(): UseCreateMemoryMutation {
  const client = useContinuum();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createMemory = useCallback(
    async (input: CreateMemoryInput): Promise<Memory> => {
      try {
        setIsLoading(true);
        setError(null);
        const memory = await client.createMemory(input);
        return memory;
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [client]
  );

  const reset = useCallback(() => {
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    createMemory,
    isLoading,
    error,
    reset,
  };
}
