/**
 * Hook for manual sync operations
 */

import { useState, useCallback } from 'react';
import { useContinuum } from './useContinuum';
import type { SyncResult, UseSyncMutation } from '../types';

export function useSync(): UseSyncMutation {
  const client = useContinuum();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SyncResult | null>(null);

  const sync = useCallback(async (): Promise<SyncResult> => {
    try {
      setIsLoading(true);
      setError(null);
      const syncResult = await client.sync();
      setResult(syncResult);
      return syncResult;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [client]);

  return {
    sync,
    isLoading,
    error,
    result,
  };
}
