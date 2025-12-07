/**
 * Native Module Bridge - TypeScript interface to native code
 */

import { NativeModules } from 'react-native';
import type { NativeEmbeddingResult } from '../types';

interface ContinuumNativeModule {
  generateEmbedding(text: string): Promise<NativeEmbeddingResult>;
  secureSet(key: string, value: string): Promise<void>;
  secureGet(key: string): Promise<string | null>;
  secureRemove(key: string): Promise<void>;
  secureClear(): Promise<void>;
  configureBackgroundSync(options: any): Promise<void>;
}

const { ContinuumModule } = NativeModules;

if (!ContinuumModule) {
  throw new Error(
    'CONTINUUM native module not found. Did you forget to run `pod install` (iOS) or rebuild the app (Android)?'
  );
}

export const NativeModule: ContinuumNativeModule = ContinuumModule;

/**
 * Secure Storage API
 */
export const SecureStorage = {
  async set(key: string, value: string): Promise<void> {
    return NativeModule.secureSet(key, value);
  },

  async get(key: string): Promise<string | null> {
    return NativeModule.secureGet(key);
  },

  async remove(key: string): Promise<void> {
    return NativeModule.secureRemove(key);
  },

  async clear(): Promise<void> {
    return NativeModule.secureClear();
  },
};

/**
 * Embedding Generation API
 */
export const EmbeddingGenerator = {
  async generate(text: string): Promise<NativeEmbeddingResult> {
    return NativeModule.generateEmbedding(text);
  },
};
