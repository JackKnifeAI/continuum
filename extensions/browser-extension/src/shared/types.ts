/**
 * Shared TypeScript types for CONTINUUM browser extension
 */

export interface ContinuumConfig {
  apiEndpoint: string;
  apiKey: string;
  autoCapture: boolean;
  syncInterval: number;
  theme: 'light' | 'dark' | 'system';
  capturePreferences: {
    saveMetadata: boolean;
    saveScreenshots: boolean;
    captureCode: boolean;
    captureVideos: boolean;
  };
}

export interface Memory {
  id: string;
  content: string;
  source: MemorySource;
  metadata: MemoryMetadata;
  concepts: string[];
  embedding?: number[];
  createdAt: string;
  updatedAt: string;
}

export interface MemorySource {
  type: 'web' | 'selection' | 'article' | 'code' | 'video' | 'pdf' | 'tweet' | 'github';
  url: string;
  title: string;
  domain: string;
  author?: string;
  publishedDate?: string;
}

export interface MemoryMetadata {
  selectionContext?: string;
  pageContext?: string;
  screenshot?: string;
  favicon?: string;
  tags?: string[];
  notes?: string;
}

export interface Concept {
  id: string;
  name: string;
  description: string;
  relatedConcepts: string[];
  memoryCount: number;
}

export interface SearchResult {
  memory: Memory;
  score: number;
  highlights: string[];
}

export interface CaptureRequest {
  content: string;
  source: MemorySource;
  metadata?: MemoryMetadata;
  concepts?: string[];
}

export interface PageContext {
  url: string;
  title: string;
  domain: string;
  relatedMemories: Memory[];
  suggestedConcepts: Concept[];
}

export interface SyncStatus {
  lastSync: string;
  pendingItems: number;
  isOnline: boolean;
  errors: string[];
}

export type MessageType =
  | 'CAPTURE_SELECTION'
  | 'QUICK_SEARCH'
  | 'GET_PAGE_CONTEXT'
  | 'SYNC_STATUS'
  | 'HIGHLIGHT_MEMORIES'
  | 'OPEN_SIDEBAR'
  | 'UPDATE_CONFIG';

export interface ExtensionMessage<T = unknown> {
  type: MessageType;
  payload: T;
  requestId?: string;
}

export interface ExtensionResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  requestId?: string;
}

export interface StorageData {
  config: ContinuumConfig;
  authToken?: string;
  syncedAt?: string;
  cachedMemories?: Memory[];
  pendingCaptures?: CaptureRequest[];
}

export interface HighlightInfo {
  memoryId: string;
  range: {
    startOffset: number;
    endOffset: number;
    text: string;
  };
  color: string;
}

export interface ContentExtractionResult {
  type: MemorySource['type'];
  content: string;
  metadata: {
    author?: string;
    publishedDate?: string;
    tags?: string[];
    codeLanguage?: string;
    videoId?: string;
    duration?: number;
  };
}
