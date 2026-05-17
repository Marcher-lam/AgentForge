// Auto-generated from OpenAPI specs
// agentforge-core + frontend-ui + rlforge + evoforge

// ─── Agent Core ───

export type AgentState =
  | "CREATED"
  | "INITIALIZED"
  | "RUNNING"
  | "STOPPED"
  | "DESTROYED";

export interface AgentStateTransition {
  from: AgentState;
  to: AgentState;
  timestamp: string;
}

export interface CreateAgentRequest {
  name: string;
  type: string;
  config?: Record<string, unknown>;
}

export interface AgentResponse {
  agent_id: string;
  name: string;
  type: string;
  state: AgentState;
  created_at: string;
  config?: Record<string, unknown>;
}

export type MessageType =
  | "TEXT"
  | "JSON"
  | "BINARY"
  | "TOOL_CALL"
  | "TOOL_RESULT"
  | "SYSTEM"
  | "DELIVERY_FAILED";

export interface Message {
  message_id: string;
  topic: string;
  message_type: MessageType;
  sender_id: string;
  payload?: Record<string, unknown>;
  timestamp: string;
  correlation_id?: string;
}

export interface SubscribeRequest {
  topic: string;
  handler_id: string;
  queue_capacity?: number;
}

export interface SubscribeResponse {
  subscription_id: string;
}

export interface UnsubscribeRequest {
  subscription_id: string;
}

export interface PublishRequest {
  topic: string;
  message: Message;
}

export interface RpcRequest {
  topic: string;
  message: Message;
  timeout_ms?: number;
}

export interface RpcResponse {
  message: Message;
  timed_out: boolean;
}

// ─── Sessions ───

export type SessionType =
  | "ONE_VS_ONE"
  | "GROUP_BROADCAST"
  | "GROUP_MULTICAST";

export type FrontendMessageType =
  | "TEXT"
  | "MARKDOWN"
  | "CODE"
  | "IMAGE"
  | "FILE"
  | "SYSTEM";

export interface CreateSessionRequest {
  type: SessionType;
  agent_ids?: string[];
  name?: string;
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

export interface FrontendMessage {
  message_id: string;
  session_id: string;
  sender_type: "USER" | "AGENT" | "SYSTEM";
  sender_id: string | null;
  sender_name: string;
  content: string;
  content_type: FrontendMessageType;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface SendMessageRequest {
  content: string;
  content_type?: FrontendMessageType;
  metadata?: Record<string, unknown>;
}

export interface MessageListResponse {
  messages: FrontendMessage[];
  has_more: boolean;
  cursor: string | null;
}

export interface AgentSummary {
  agent_id: string;
  name: string;
  avatar_url: string | null;
  status: "ONLINE" | "OFFLINE" | "BUSY" | "ERROR";
  last_message_preview: string | null;
  capabilities?: string[];
}

// ─── Monitor ───

export interface MonitorMessage {
  message_id: string;
  sender_id: string;
  receiver_id: string | null;
  topic: string;
  message_type: string;
  payload?: Record<string, unknown>;
  timestamp: string;
}

export interface MonitorMessageList {
  messages: MonitorMessage[];
  has_more: boolean;
  cursor: string | null;
  total_count: number;
}

export interface MonitorStatistics {
  total_messages: number;
  messages_per_sec: number;
  avg_latency_ms: number;
  per_agent_stats: Array<{
    agent_id: string;
    sent_count: number;
    received_count: number;
  }>;
  topic_distribution: Record<string, number>;
}

export interface TopologyNode {
  agent_id: string;
  name: string;
  status: string;
  position: { x: number; y: number };
}

export type EdgeFrequency = "LOW" | "MEDIUM" | "HIGH";

export interface TopologyEdge {
  source_id: string;
  target_id: string;
  message_count: number;
  frequency: EdgeFrequency;
}

export interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

// ─── Dashboard ───

export interface DataPoint {
  x: number;
  y: number;
}

export interface FitnessCurves {
  best: DataPoint[];
  mean: DataPoint[];
  std: DataPoint[];
}

export interface EvolutionDashboardData {
  evolution_id: string;
  current_generation: number;
  status: string;
  fitness_curves: FitnessCurves;
  gene_tree: unknown;
  heatmap: {
    gene_dims: number;
    individuals: number;
    values: number[][];
  } | null;
  downsampled: boolean;
}

export type AlgorithmType = "DQN" | "PPO" | "MADDPG";
export type TrainingStatus =
  | "PENDING"
  | "RUNNING"
  | "EVALUATING"
  | "PAUSED"
  | "COMPLETED"
  | "FAILED";

export interface TrainingDashboardData {
  task_id: string;
  algorithm: AlgorithmType;
  current_step: number;
  current_episode: number;
  status: TrainingStatus;
  metrics: Record<string, DataPoint[]>;
  hyperparameters: Record<string, unknown>;
  downsampled: boolean;
}

export interface TrainingRunComparison {
  task_id: string;
  label: string;
  hyperparameters: Record<string, unknown>;
  data: DataPoint[];
}

export interface TrainingCompareData {
  runs: TrainingRunComparison[];
}

// ─── RL Engine ───

export type EnvType = "SINGLE_AGENT" | "MULTI_AGENT";
export type ActionSpaceType = "DISCRETE" | "CONTINUOUS";

export interface EnvironmentInfo {
  env_id: string;
  name: string;
  type: EnvType;
  observation_space: {
    shape: number[];
    dtype: string;
  };
  action_space: {
    type: ActionSpaceType;
    shape: number[];
    n?: number;
  };
  max_episode_steps: number | null;
}

export interface CreateEnvInstanceRequest {
  seed?: number;
  num_envs?: number;
  render?: boolean;
}

export interface EnvInstanceResponse {
  instance_id: string;
  env_id: string;
  status: "READY" | "RUNNING" | "CLOSED";
  num_envs: number;
  seed: number | null;
}

export interface TrainingTaskResponse {
  task_id: string;
  algorithm: AlgorithmType;
  env_id: string;
  status: TrainingStatus;
  current_step: number;
  current_episode: number;
  best_reward: number;
  seed: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface CheckpointInfo {
  checkpoint_id: string;
  task_id: string;
  step: number;
  episode: number;
  reward: number;
  created_at: string;
  size_bytes: number;
}

export interface EvaluateRequest {
  num_episodes?: number;
  render?: boolean;
}

export interface EvaluateResponse {
  mean_reward: number;
  std_reward: number;
  mean_length: number;
  episodes: number;
}

// ─── Evolution Engine ───

export type GenomeEncoding = "REAL" | "BINARY" | "TREE";
export type EvolutionStatus =
  | "PENDING"
  | "RUNNING"
  | "PAUSED"
  | "COMPLETED"
  | "TERMINATED";
export type TerminationReason =
  | "MAX_GENERATIONS"
  | "FITNESS_THRESHOLD"
  | "CONVERGENCE"
  | "MANUAL_STOP";

export interface CreatePopulationRequest {
  encoding: GenomeEncoding;
  size?: number;
  bounds?: Array<{ min: number; max: number }>;
  fitness_function: string;
  seed?: number;
}

export interface PopulationResponse {
  population_id: string;
  encoding: GenomeEncoding;
  size: number;
  generation: number;
  created_at: string;
  best_fitness: number | null;
}

export interface Individual {
  individual_id: string;
  index: number;
  genome: unknown;
  fitness: number | null;
  parents?: string[];
}

export interface PopulationStats {
  generation: number;
  best_fitness: number;
  mean_fitness: number;
  worst_fitness: number;
  std_fitness: number;
  diversity: number;
}

export type SelectionType =
  | "ROULETTE"
  | "TOURNAMENT"
  | "ELITE"
  | "RANK";
export type CrossoverType =
  | "SINGLE_POINT"
  | "MULTI_POINT"
  | "UNIFORM"
  | "SBX";
export type MutationType =
  | "GAUSSIAN"
  | "UNIFORM"
  | "BIT_FLIP"
  | "POLYNOMIAL";

export interface OperatorConfig {
  selection?: SelectionType;
  crossover?: CrossoverType;
  crossover_rate?: number;
  mutation?: MutationType;
  mutation_rate?: number;
  elite_size?: number;
}

export interface TerminationCriteria {
  max_generations?: number;
  fitness_threshold?: number;
  convergence_generations?: number;
  convergence_threshold?: number;
}

export interface CreateEvolutionRequest {
  population_id: string;
  operators: OperatorConfig;
  termination: TerminationCriteria;
  callbacks?: string[];
}

export interface EvolutionResponse {
  evolution_id: string;
  population_id: string;
  status: EvolutionStatus;
  current_generation: number;
  termination_reason: TerminationReason | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface GenerationSnapshot {
  generation: number;
  best_fitness: number;
  mean_fitness: number;
  std_fitness: number;
  diversity: number;
  best_individual_id: string;
  timestamp: string;
}

export interface GeneTreeNode {
  individual_id: string;
  generation: number;
  fitness: number;
  genome_summary?: unknown;
  children?: GeneTreeNode[];
}

// ─── Error ───

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ─── WebSocket Event Types ───

export type WsEventType =
  | "message"
  | "state_change"
  | "monitor"
  | "training_metric"
  | "evolution_update";

export interface WsEvent<T = unknown> {
  type: WsEventType;
  data: T;
}
