/**
 * Hook for monitoring connection status
 */

import { useState, useEffect } from 'react';
import { useContinuum } from './useContinuum';
import type { ConnectionStatus } from '../types';

export function useConnectionStatus(): ConnectionStatus {
  const client = useContinuum();
  const [status, setStatus] = useState<ConnectionStatus>({
    isConnected: true,
    isOnline: true,
  });

  useEffect(() => {
    let mounted = true;

    const checkStatus = async () => {
      const connectionStatus = await client.getConnectionStatus();
      if (mounted) {
        setStatus(connectionStatus);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [client]);

  return status;
}
