// Auto-generated types for AgentForge frontend

export type SessionType = 'ONE_VS_ONE' | 'GROUP_BROADCAST' | 'GROUP_MULTICAST';
export type FrontendMessageType = 'TEXT' | 'MARKDOWN' | 'CODE' | 'IMAGE' | 'FILE' | 'SYSTEM';
export type AgentStatus = 'ONLINE' | 'OFFLINE' | 'BUSY' | 'ERROR';

export interface FrontendMessage {
  message_id: string;
  session_id: string;
  sender_type: 'USER' | 'AGENT' | 'SYSTEM';
  sender_id: string | null;
  sender_name: string;
  content: string;
  content_type: FrontendMessageType;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface SessionResponse {
  session_id: string;
  type: SessionType;
  name: string | null;
  agent_ids: string[];
  unread_count: number;
  last_message: FrontendMessage | null;
  created_at: string;
  updated_at: string;
}

export interface AgentSummary {
  agent_id: string;
  name: string;
  avatar_url: string | null;
  status: AgentStatus;
  last_message_preview: string | null;
  system_prompt?: string;
  capabilities?: string[];
  config?: AgentConfig;
  tools?: ToolDefinition[];
  skills?: string[];
}

export interface MonitorMessage {
  message_id: string;
  sender_id: string;
  receiver_id: string | null;
  topic: string;
  message_type: string;
  payload?: Record<string, unknown>;
  timestamp: string;
}

export interface TopologyNode {
  agent_id: string;
  name: string;
  status: string;
  position: { x: number; y: number };
}

export interface TopologyEdge {
  source_id: string;
  target_id: string;
  message_count: number;
  frequency: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface DataPoint {
  x: number;
  y: number;
}

export interface EvolutionDashboardData {
  evolution_id: string;
  current_generation: number;
  status: string;
  fitness_curves: {
    best: DataPoint[];
    mean: DataPoint[];
    std: DataPoint[];
  };
  gene_tree: unknown;
  heatmap: { gene_dims: number; individuals: number; values: number[][] } | null;
  downsampled: boolean;
}

export interface TrainingDashboardData {
  task_id: string;
  algorithm: string;
  current_step: number;
  current_episode: number;
  status: string;
  metrics: Record<string, DataPoint[]>;
  hyperparameters: Record<string, unknown>;
  downsampled: boolean;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

// ── Per-Agent Capability System Types ──────────────────

export interface LLMOverride {
  provider_profile?: string | null;
  provider?: string | null;
  model?: string | null;
  base_url?: string | null;
  api_key?: string | null;
  temperature?: number | null;
  max_tokens?: number | null;
}

export interface LLMProfile {
  id: string;
  name: string;
  provider: string;
  base_url: string;
  api_key: string;
  models: string[];
}

export interface EvolutionConfig {
  mode: string;
  population_size: number;
  max_generations: number;
  mutation_rate: number;
  elite_size: number;
  genome_dim: number;
  seed: number;
}

export interface RLConfig {
  algorithm: string;
  total_steps: number;
  learning_rate: number;
  seed: number;
}

export interface AgentConfig {
  llm?: LLMOverride | null;
  tool_ids: string[];
  skill_ids: string[];
  mcp_server_ids: string[];
  evolution?: EvolutionConfig | null;
  rl?: RLConfig | null;
}

export interface SkillSummary {
  name: string;
  version: string;
  tags: string[];
  dependencies: string[];
}

export interface MCPServerSummary {
  server_id: string;
  name: string;
  description: string;
  connection_type: string;
  command: string;
  url: string;
  tool_names: string[];
  enabled: boolean;
}

// ── OpenClaw Skill Types ──────────────────────────────

export interface OpenClawSkillSummary {
  name: string;
  description: string;
  instructions: string;
  source_path?: string | null;
  metadata?: Record<string, unknown>;
}

export interface OpenClawScanResult {
  installed: string[];
  skipped: { name: string; reason: string[] }[];
  total_found: number;
}
