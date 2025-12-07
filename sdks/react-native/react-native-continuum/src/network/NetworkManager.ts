/**
 * Network Manager - Handles API requests with retry logic
 */

import NetInfo from '@react-native-community/netinfo';
import type { ConnectionStatus, ContinuumConfig } from '../types';
import { NetworkError, AuthenticationError } from '../types';
import type { Logger } from '../utils/Logger';

export class NetworkManager {
  private config: Required<ContinuumConfig>;
  private logger: Logger;
  private accessToken: string | null = null;

  constructor(config: Required<ContinuumConfig>, logger: Logger) {
    this.config = config;
    this.logger = logger;
  }

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  // ========================================================================
  // HTTP Methods
  // ========================================================================

  async get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  async post<T>(path: string, data?: any): Promise<T> {
    return this.request<T>('POST', path, data);
  }

  async patch<T>(path: string, data?: any): Promise<T> {
    return this.request<T>('PATCH', path, data);
  }

  async delete(path: string): Promise<void> {
    await this.request('DELETE', path);
  }

  // ========================================================================
  // Request Handler
  // ========================================================================

  private async request<T>(
    method: string,
    path: string,
    data?: any
  ): Promise<T> {
    const url = `${this.config.apiUrl}${path}`;

    for (let attempt = 0; attempt <= this.config.retry.maxAttempts; attempt++) {
      try {
        this.logger.debug('API request', { method, path, attempt });

        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          ...this.config.customHeaders,
        };

        if (this.config.apiKey) {
          headers['X-API-Key'] = this.config.apiKey;
        }

        if (this.accessToken) {
          headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(
          () => controller.abort(),
          this.config.timeout
        );

        const response = await fetch(url, {
          method,
          headers,
          body: data ? JSON.stringify(data) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Handle errors
        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({}));

          if (response.status === 401) {
            throw new AuthenticationError(
              errorBody.message || 'Unauthorized',
              errorBody
            );
          }

          throw new NetworkError(
            errorBody.message || `Request failed: ${response.status}`,
            {
              statusCode: response.status,
              ...errorBody,
            }
          );
        }

        // Parse response
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          return await response.json();
        } else {
          return (await response.text()) as any;
        }
      } catch (error: any) {
        this.logger.error('Request failed', {
          method,
          path,
          attempt,
          error: error.message,
        });

        // Don't retry on auth errors
        if (error instanceof AuthenticationError) {
          throw error;
        }

        // Retry logic
        if (attempt < this.config.retry.maxAttempts) {
          const delay = this.calculateRetryDelay(attempt);
          this.logger.debug('Retrying request', { delay, attempt });
          await this.sleep(delay);
        } else {
          throw error;
        }
      }
    }

    throw new NetworkError('Max retry attempts exceeded');
  }

  // ========================================================================
  // Connection Status
  // ========================================================================

  async isOnline(): Promise<boolean> {
    const state = await NetInfo.fetch();
    return state.isConnected ?? false;
  }

  async getConnectionStatus(): Promise<ConnectionStatus> {
    const state = await NetInfo.fetch();

    return {
      isConnected: state.isConnected ?? false,
      isOnline: state.isInternetReachable ?? false,
      type: state.type as any,
      isInternetReachable: state.isInternetReachable ?? undefined,
    };
  }

  // ========================================================================
  // Utilities
  // ========================================================================

  private calculateRetryDelay(attempt: number): number {
    const { backoff, initialDelay } = this.config.retry;

    if (backoff === 'exponential') {
      return initialDelay * Math.pow(2, attempt);
    } else {
      return initialDelay * (attempt + 1);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
