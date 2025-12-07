/**
 * React Context for CONTINUUM client
 */

import React, { createContext, useEffect, useState } from 'react';
import type { ContinuumClient } from '../ContinuumClient';

interface ContinuumContextValue {
  client: ContinuumClient;
}

export const ContinuumContext = createContext<ContinuumContextValue | null>(null);

interface ContinuumProviderProps {
  client: ContinuumClient;
  children: React.ReactNode;
}

export function ContinuumProvider({ client, children }: ContinuumProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    client.initialize().then(() => setIsInitialized(true));
  }, [client]);

  if (!isInitialized) {
    return null; // Or render a loading component
  }

  return (
    <ContinuumContext.Provider value={{ client }}>
      {children}
    </ContinuumContext.Provider>
  );
}
