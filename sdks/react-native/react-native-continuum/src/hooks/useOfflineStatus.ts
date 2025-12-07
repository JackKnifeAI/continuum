/**
 * Hook for monitoring offline status
 */

import { useState, useEffect } from 'react';
import { useContinuum } from './useContinuum';

export function useOfflineStatus(): boolean {
  const client = useContinuum();
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    let mounted = true;

    const checkStatus = async () => {
      const status = await client.getConnectionStatus();
      if (mounted) {
        setIsOffline(!status.isConnected);
      }
    };

    // Check initially
    checkStatus();

    // Poll every 5 seconds
    const interval = setInterval(checkStatus, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [client]);

  return isOffline;
}
