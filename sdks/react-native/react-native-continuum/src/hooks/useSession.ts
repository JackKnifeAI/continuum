/**
 * Hook for managing user session
 */

import { useState, useEffect, useCallback } from 'react';
import { useContinuum } from './useContinuum';
import type { Session, AuthCredentials, UseSessionResult } from '../types';

export function useSession(): UseSessionResult {
  const client = useContinuum();
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadSession = useCallback(async () => {
    try {
      setIsLoading(true);
      const currentSession = await client.getSession();
      setSession(currentSession);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [client]);

  const signIn = useCallback(
    async (credentials: AuthCredentials) => {
      try {
        setIsLoading(true);
        setError(null);
        await client.signIn(credentials.email, credentials.password);
        const newSession = await client.getSession();
        setSession(newSession);
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [client]
  );

  const signOut = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      await client.signOut();
      setSession(null);
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [client]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  return {
    session,
    isLoading,
    error,
    signIn,
    signOut,
  };
}
