/**
 * Hook for monitoring sync status
 */

import { useState, useEffect } from 'react';
import { useContinuum } from './useContinuum';
import type { SyncStatus } from '../types';

export function useSyncStatus(): SyncStatus {
  const client = useContinuum();
  const [status, setStatus] = useState<SyncStatus>({
    isSyncing: false,
    pendingOperations: 0,
  });

  useEffect(() => {
    let mounted = true;

    const checkStatus = async () => {
      const syncStatus = await client.getSyncStatus();
      if (mounted) {
        setStatus(syncStatus);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 3000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [client]);

  return status;
}
