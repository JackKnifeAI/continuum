/**
 * Hook for fetching concepts
 */

import { useState, useEffect, useCallback } from 'react';
import { useContinuum } from './useContinuum';
import type { Concept, ConceptFilter, UseConceptsResult } from '../types';

export function useConcepts(filter?: ConceptFilter): UseConceptsResult {
  const client = useContinuum();
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchConcepts = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await client.getConcepts(filter);
      setConcepts(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [client, filter]);

  useEffect(() => {
    fetchConcepts();
  }, [fetchConcepts]);

  return {
    concepts,
    isLoading,
    error,
    refetch: fetchConcepts,
  };
}
