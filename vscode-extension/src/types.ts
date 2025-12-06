/**
 * Type definitions for Continuum API
 */

export interface ContinuumConfig {
  apiUrl: string;
  apiKey: string;
  tenantId: string;
  maxConcepts: number;
}

export interface RecallRequest {
  message: string;
  max_concepts?: number;
}

export interface RecallResponse {
  context: string;
  concepts_found: number;
  relationships_found: number;
  query_time_ms: number;
  tenant_id: string;
}

export interface LearnRequest {
  user_message: string;
  ai_response: string;
  metadata?: Record<string, any>;
}

export interface LearnResponse {
  concepts_extracted: number;
  decisions_detected: number;
  links_created: number;
  compounds_found: number;
  tenant_id: string;
}

export interface TurnRequest {
  user_message: string;
  ai_response: string;
  max_concepts?: number;
  metadata?: Record<string, any>;
}

export interface TurnResponse {
  recall: RecallResponse;
  learn: LearnResponse;
}

export interface StatsResponse {
  tenant_id: string;
  instance_id: string;
  entities: number;
  messages: number;
  decisions: number;
  attention_links: number;
  compound_concepts: number;
}

export interface EntityItem {
  name: string;
  type: string;
  description?: string;
  created_at?: string;
}

export interface EntitiesResponse {
  entities: EntityItem[];
  total: number;
  tenant_id: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface CreateKeyRequest {
  tenant_id: string;
  name?: string;
}

export interface CreateKeyResponse {
  api_key: string;
  tenant_id: string;
  message: string;
}

export interface MemoryTreeItem {
  label: string;
  description?: string;
  tooltip?: string;
  contextValue: string;
  children?: MemoryTreeItem[];
  entity?: EntityItem;
}

export interface ConnectionStatus {
  connected: boolean;
  apiUrl: string;
  tenantId: string;
  lastSync?: Date;
  error?: string;
}

export enum SyncStatus {
  Idle = 'idle',
  Syncing = 'syncing',
  Success = 'success',
  Error = 'error',
}
