import { z } from 'zod';

// Agent Message Schema
export const AgentMessageSchema = z.object({
  message_id: z.string().uuid(),
  topic: z.string().min(1),
  message_type: z.enum([
    'text', 'json', 'binary', 'tool_call', 'tool_result', 'system', 'delivery_failed',
  ]),
  sender_id: z.string().uuid(),
  payload: z.record(z.unknown()).optional(),
  timestamp: z.string().datetime(),
  correlation_id: z.string().uuid().nullable().optional(),
});
export type AgentMessage = z.infer<typeof AgentMessageSchema>;

// Agent State Schema
export const AgentStateSchema = z.enum([
  'created', 'initialized', 'running', 'stopped', 'destroyed',
]);
export type AgentState = z.infer<typeof AgentStateSchema>;

// Frontend Message Schema
export const FrontendMessageSchema = z.object({
  message_id: z.string().uuid(),
  session_id: z.string().uuid(),
  sender_type: z.enum(['USER', 'AGENT', 'SYSTEM']),
  sender_id: z.string().nullable(),
  sender_name: z.string().min(1),
  content: z.string(),
  content_type: z.enum(['TEXT', 'MARKDOWN', 'CODE', 'IMAGE', 'FILE', 'SYSTEM']),
  metadata: z.record(z.unknown()).optional(),
  created_at: z.string().datetime(),
});
export type FrontendMessage = z.infer<typeof FrontendMessageSchema>;

// Session Schema
export const SessionResponseSchema = z.object({
  session_id: z.string().uuid(),
  type: z.enum(['ONE_VS_ONE', 'GROUP_BROADCAST', 'GROUP_MULTICAST']),
  name: z.string().nullable(),
  agent_ids: z.array(z.string()),
  unread_count: z.number().int().min(0),
  last_message: FrontendMessageSchema.nullable(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});
export type SessionResponse = z.infer<typeof SessionResponseSchema>;

// Agent Summary Schema
export const AgentSummarySchema = z.object({
  agent_id: z.string(),
  name: z.string(),
  avatar_url: z.string().nullable(),
  status: z.enum(['ONLINE', 'OFFLINE', 'BUSY', 'ERROR']),
  last_message_preview: z.string().nullable(),
  capabilities: z.array(z.string()).optional(),
});
export type AgentSummary = z.infer<typeof AgentSummarySchema>;

// Monitor Message Schema
export const MonitorMessageSchema = z.object({
  message_id: z.string().uuid(),
  sender_id: z.string().uuid(),
  receiver_id: z.string().nullable(),
  topic: z.string().min(1),
  message_type: z.string(),
  payload: z.record(z.unknown()).optional(),
  timestamp: z.string().datetime(),
});
export type MonitorMessage = z.infer<typeof MonitorMessageSchema>;

// DataPoint Schema
export const DataPointSchema = z.object({
  x: z.number(),
  y: z.number(),
});
export type DataPoint = z.infer<typeof DataPointSchema>;

// Evolution Dashboard Schema
export const EvolutionDashboardDataSchema = z.object({
  evolution_id: z.string(),
  current_generation: z.number().int().min(0),
  status: z.enum(['running', 'completed', 'failed']),
  fitness_curves: z.object({
    best: z.array(DataPointSchema),
    mean: z.array(DataPointSchema),
    std: z.array(DataPointSchema),
  }),
  gene_tree: z.unknown().optional(),
  heatmap: z.object({
    gene_dims: z.number(),
    individuals: z.number(),
    values: z.array(z.array(z.number())),
  }).nullable(),
  downsampled: z.boolean(),
});
export type EvolutionDashboardData = z.infer<typeof EvolutionDashboardDataSchema>;

// Training Dashboard Schema
export const TrainingDashboardDataSchema = z.object({
  task_id: z.string(),
  algorithm: z.enum(['DQN', 'PPO', 'MADDPG']),
  current_step: z.number().int().min(0),
  current_episode: z.number().int().min(0),
  status: z.enum(['running', 'completed', 'failed']),
  metrics: z.record(z.array(DataPointSchema)),
  hyperparameters: z.record(z.unknown()),
  downsampled: z.boolean(),
});
export type TrainingDashboardData = z.infer<typeof TrainingDashboardDataSchema>;

// Error Response Schema
export const ErrorResponseSchema = z.object({
  error_code: z.string(),
  message: z.string(),
  details: z.record(z.unknown()).optional(),
});
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
