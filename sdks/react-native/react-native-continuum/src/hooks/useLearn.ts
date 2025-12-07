/**
 * Mutation hook for learning from conversations
 */

import { useState, useCallback } from 'react';
import { useContinuum } from './useContinuum';
import type { Message, LearnResult, UseLearnMutation } from '../types';

export function useLearn(): UseLearnMutation {
  const client = useContinuum();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<LearnResult | null>(null);

  const learn = useCallback(
    async (conversation: Message[]): Promise<LearnResult> => {
      try {
        setIsLoading(true);
        setError(null);
        const learnResult = await client.learn(conversation);
        setResult(learnResult);
        return learnResult;
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
    setResult(null);
    setIsLoading(false);
  }, []);

  return {
    learn,
    isLoading,
    error,
    result,
    reset,
  };
}
