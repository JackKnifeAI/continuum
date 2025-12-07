/**
 * Core hook to access CONTINUUM client from context
 */

import { useContext } from 'react';
import { ContinuumContext } from '../context/ContinuumContext';
import type { ContinuumClient } from '../ContinuumClient';

export function useContinuum(): ContinuumClient {
  const context = useContext(ContinuumContext);

  if (!context) {
    throw new Error('useContinuum must be used within a ContinuumProvider');
  }

  return context.client;
}
