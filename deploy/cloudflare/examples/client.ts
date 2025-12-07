/**
 * CONTINUUM Cloudflare Workers - TypeScript Client Example
 */

interface ContinuumClientOptions {
  apiUrl: string;
  token: string;
}

interface Memory {
  id?: string;
  content: string;
  metadata?: Record<string, unknown>;
  tags?: string[];
  embedding?: number[];
}

interface SearchQuery {
  query: string;
  limit?: number;
  offset?: number;
  filters?: Record<string, unknown>;
}

class ContinuumClient {
  private apiUrl: string;
  private token: string;

  constructor(options: ContinuumClientOptions) {
    this.apiUrl = options.apiUrl.replace(/\/$/, '');
    this.token = options.token;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.apiUrl}${path}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error?.message || 'Request failed');
    }

    return data.data;
  }

  // Memories
  async listMemories(params?: { limit?: number; offset?: number; tags?: string[] }) {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    if (params?.tags?.length) query.set('tags', params.tags.join(','));

    return this.request<{ memories: Memory[]; total: number }>(
      `/api/v1/memories?${query}`
    );
  }

  async getMemory(id: string) {
    return this.request<Memory>(`/api/v1/memories/${id}`);
  }

  async createMemory(memory: Omit<Memory, 'id'>) {
    return this.request<Memory>('/api/v1/memories', {
      method: 'POST',
      body: JSON.stringify(memory),
    });
  }

  async updateMemory(id: string, updates: Partial<Memory>) {
    return this.request<Memory>(`/api/v1/memories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteMemory(id: string) {
    return this.request<{ deleted: boolean }>(`/api/v1/memories/${id}`, {
      method: 'DELETE',
    });
  }

  // Search
  async search(query: SearchQuery) {
    return this.request<{
      memories: Memory[];
      total: number;
      query: string;
      took_ms: number;
    }>('/api/v1/search', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async semanticSearch(query: SearchQuery) {
    return this.request<{
      memories: Memory[];
      total: number;
      query: string;
      took_ms: number;
    }>('/api/v1/search/semantic', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async getSuggestions(query: string, limit: number = 10) {
    return this.request<{ suggestions: string[] }>(
      `/api/v1/search/suggest?q=${encodeURIComponent(query)}&limit=${limit}`
    );
  }

  async searchByTag(tag: string, params?: { limit?: number; offset?: number }) {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());

    return this.request<{
      memories: Memory[];
      total: number;
    }>(`/api/v1/search/tags/${tag}?${query}`);
  }

  // Sync (WebSocket)
  connectSync(
    onMessage: (message: any) => void,
    onError?: (error: any) => void
  ): WebSocket {
    const wsUrl = this.apiUrl.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/api/v1/sync`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
    } as any);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      onMessage(message);
    };

    if (onError) {
      ws.onerror = onError;
    }

    return ws;
  }

  // Health
  async healthCheck() {
    return this.request<{
      status: string;
      version: string;
      services: Record<string, boolean>;
    }>('/health');
  }
}

// Usage Example
async function example() {
  const client = new ContinuumClient({
    apiUrl: 'https://your-worker.workers.dev',
    token: 'your-jwt-token',
  });

  try {
    // Health check
    const health = await client.healthCheck();
    console.log('Health:', health);

    // Create memory
    const memory = await client.createMemory({
      content: 'This is a test memory',
      tags: ['test', 'example'],
      metadata: {
        source: 'client-example',
      },
    });
    console.log('Created:', memory);

    // List memories
    const { memories } = await client.listMemories({ limit: 10 });
    console.log('Memories:', memories);

    // Search
    const results = await client.search({
      query: 'test',
      limit: 5,
    });
    console.log('Search results:', results);

    // Connect to sync
    const ws = client.connectSync(
      (message) => console.log('Sync message:', message),
      (error) => console.error('Sync error:', error)
    );

    // Send sync message
    ws.send(JSON.stringify({
      type: 'ping',
      timestamp: new Date().toISOString(),
    }));
  } catch (error) {
    console.error('Error:', error);
  }
}

export { ContinuumClient, type ContinuumClientOptions, type Memory, type SearchQuery };
