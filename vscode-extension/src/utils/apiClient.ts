/**
 * Continuum API Client
 *
 * Handles all communication with the Continuum memory API.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import * as vscode from 'vscode';
import {
  ContinuumConfig,
  RecallRequest,
  RecallResponse,
  LearnRequest,
  LearnResponse,
  TurnRequest,
  TurnResponse,
  StatsResponse,
  EntitiesResponse,
  HealthResponse,
} from '../types';

export class ContinuumApiClient {
  private client: AxiosInstance;
  private config: ContinuumConfig;

  constructor(config: ContinuumConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.apiUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': config.apiKey,
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        return this.handleError(error);
      }
    );
  }

  /**
   * Update configuration and recreate client
   */
  updateConfig(config: Partial<ContinuumConfig>): void {
    this.config = { ...this.config, ...config };
    this.client = axios.create({
      baseURL: this.config.apiUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.config.apiKey,
      },
    });
  }

  /**
   * Health check - verify API connectivity
   */
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * Recall - query memory for relevant context
   */
  async recall(message: string, maxConcepts?: number): Promise<RecallResponse> {
    const request: RecallRequest = {
      message,
      max_concepts: maxConcepts || this.config.maxConcepts,
    };

    const response = await this.client.post<RecallResponse>('/recall', request);
    return response.data;
  }

  /**
   * Learn - store a message exchange in memory
   */
  async learn(
    userMessage: string,
    aiResponse: string,
    metadata?: Record<string, any>
  ): Promise<LearnResponse> {
    const request: LearnRequest = {
      user_message: userMessage,
      ai_response: aiResponse,
      metadata,
    };

    const response = await this.client.post<LearnResponse>('/learn', request);
    return response.data;
  }

  /**
   * Process a complete turn (recall + learn)
   */
  async processTurn(
    userMessage: string,
    aiResponse: string,
    maxConcepts?: number,
    metadata?: Record<string, any>
  ): Promise<TurnResponse> {
    const request: TurnRequest = {
      user_message: userMessage,
      ai_response: aiResponse,
      max_concepts: maxConcepts || this.config.maxConcepts,
      metadata,
    };

    const response = await this.client.post<TurnResponse>('/turn', request);
    return response.data;
  }

  /**
   * Get memory statistics
   */
  async getStats(): Promise<StatsResponse> {
    const response = await this.client.get<StatsResponse>('/stats');
    return response.data;
  }

  /**
   * Get entities/concepts from knowledge graph
   */
  async getEntities(
    limit: number = 100,
    offset: number = 0,
    entityType?: string
  ): Promise<EntitiesResponse> {
    const params: any = { limit, offset };
    if (entityType) {
      params.entity_type = entityType;
    }

    const response = await this.client.get<EntitiesResponse>('/entities', { params });
    return response.data;
  }

  /**
   * Handle API errors
   */
  private handleError(error: AxiosError): Promise<never> {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = (error.response.data as any)?.detail || error.message;

      if (status === 401 || status === 403) {
        vscode.window.showErrorMessage(
          'Continuum: Authentication failed. Please check your API key.'
        );
      } else if (status === 404) {
        vscode.window.showErrorMessage(
          'Continuum: API endpoint not found. Please check your server URL.'
        );
      } else if (status >= 500) {
        vscode.window.showErrorMessage(
          `Continuum: Server error (${status}). Please try again later.`
        );
      } else {
        vscode.window.showErrorMessage(`Continuum API Error: ${message}`);
      }

      throw new Error(`API Error ${status}: ${message}`);
    } else if (error.request) {
      // Request made but no response received
      vscode.window.showErrorMessage(
        'Continuum: Unable to connect to server. Please check your API URL and network connection.'
      );
      throw new Error('Connection failed: No response from server');
    } else {
      // Error setting up the request
      vscode.window.showErrorMessage(`Continuum: ${error.message}`);
      throw error;
    }
  }

  /**
   * Test connection to API
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.health();
      return true;
    } catch (error) {
      return false;
    }
  }
}

/**
 * Get or create API client instance
 */
let clientInstance: ContinuumApiClient | null = null;

export function getApiClient(): ContinuumApiClient {
  if (!clientInstance) {
    const config = getConfigFromWorkspace();
    clientInstance = new ContinuumApiClient(config);
  }
  return clientInstance;
}

export function updateApiClient(config: Partial<ContinuumConfig>): void {
  if (clientInstance) {
    clientInstance.updateConfig(config);
  } else {
    const fullConfig = { ...getConfigFromWorkspace(), ...config };
    clientInstance = new ContinuumApiClient(fullConfig);
  }
}

/**
 * Load configuration from VS Code workspace settings
 */
function getConfigFromWorkspace(): ContinuumConfig {
  const config = vscode.workspace.getConfiguration('continuum');

  return {
    apiUrl: config.get<string>('apiUrl', 'http://localhost:8000'),
    apiKey: config.get<string>('apiKey', ''),
    tenantId: config.get<string>('tenantId', 'vscode'),
    maxConcepts: config.get<number>('maxConcepts', 10),
  };
}
