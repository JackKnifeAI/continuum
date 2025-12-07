/**
 * Hook for accessing current user
 */

import { useSession } from './useSession';
import type { UseUserResult } from '../types';

export function useUser(): UseUserResult {
  const { session, isLoading, error } = useSession();

  return {
    user: session?.user || null,
    isLoading,
    error,
  };
}
