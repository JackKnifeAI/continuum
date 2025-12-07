/**
 * CONTINUUM API Client
 * Handles all communication with CONTINUUM backend
 */

import type {
  Memory,
  CaptureRequest,
  SearchResult,
  Concept,
  PageContext,
  ContinuumConfig
} from './types';

export class ContinuumAPIClient {
  private baseURL: string;
  private apiKey: string;

  constructor(config: Pick<ContinuumConfig, 'apiEndpoint' | 'apiKey'>) {
    this.baseURL = config.apiEndpoint;
    this.apiKey = config.apiKey;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  /**
   * Capture new memory
   */
  async capture(request: CaptureRequest): Promise<Memory> {
    return this.request<Memory>('/api/memories', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Search memories
   */
  async search(query: string, limit = 10): Promise<SearchResult[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    return this.request<SearchResult[]>(`/api/search?${params}`);
  }

  /**
   * Get memory by ID
   */
  async getMemory(id: string): Promise<Memory> {
    return this.request<Memory>(`/api/memories/${id}`);
  }

  /**
   * Get recent memories
   */
  async getRecentMemories(limit = 20): Promise<Memory[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.request<Memory[]>(`/api/memories/recent?${params}`);
  }

  /**
   * Get memories for current page
   */
  async getPageContext(url: string): Promise<PageContext> {
    const params = new URLSearchParams({ url });
    return this.request<PageContext>(`/api/context?${params}`);
  }

  /**
   * Find related memories
   */
  async findRelated(memoryId: string, limit = 10): Promise<Memory[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.request<Memory[]>(
      `/api/memories/${memoryId}/related?${params}`
    );
  }

  /**
   * Get concept by name
   */
  async getConcept(name: string): Promise<Concept> {
    const params = new URLSearchParams({ name });
    return this.request<Concept>(`/api/concepts?${params}`);
  }

  /**
   * Get all concepts
   */
  async getConcepts(limit = 100): Promise<Concept[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.request<Concept[]>(`/api/concepts?${params}`);
  }

  /**
   * Get concept graph
   */
  async getConceptGraph(): Promise<{
    nodes: Concept[];
    edges: Array<{ source: string; target: string; weight: number }>;
  }> {
    return this.request('/api/concepts/graph');
  }

  /**
   * Update memory
   */
  async updateMemory(
    id: string,
    updates: Partial<Memory>
  ): Promise<Memory> {
    return this.request<Memory>(`/api/memories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete memory
   */
  async deleteMemory(id: string): Promise<void> {
    await this.request(`/api/memories/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * Extract concepts from text
   */
  async extractConcepts(text: string): Promise<string[]> {
    return this.request<string[]>('/api/extract/concepts', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: 'ok' | 'error'; version: string }> {
    return this.request('/api/health');
  }
}

export default ContinuumAPIClient;
