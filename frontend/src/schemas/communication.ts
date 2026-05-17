import { z } from 'zod';

// ─── Action Schemas ───────────────────────────────────────────────

const topicPattern = z.string().min(1).regex(/^[a-zA-Z0-9_.\-*]+$/);

const DirectActionSchema = z.object({
  type: z.literal('direct'),
  action_id: z.string().uuid(),
  sender_id: z.string().uuid(),
  target_id: z.string().uuid(),
  topic: topicPattern,
  action_type: z.enum(['tool_call', 'task_assign', 'query', 'control']),
  payload: z.record(z.unknown()).optional(),
  timeout_ms: z.number().int().min(100).default(5000),
  priority: z.enum(['low', 'normal', 'high']).default('normal'),
  timestamp: z.string().datetime(),
});

const BroadcastActionSchema = z.object({
  type: z.literal('broadcast'),
  action_id: z.string().uuid(),
  sender_id: z.string().uuid(),
  topic: topicPattern,
  action_type: z.literal('broadcast'),
  payload: z.record(z.unknown()).optional(),
  require_ack: z.boolean().default(false),
  timestamp: z.string().datetime(),
});

const MulticastActionSchema = z.object({
  type: z.literal('multicast'),
  action_id: z.string().uuid(),
  sender_id: z.string().uuid(),
  target_ids: z.array(z.string().uuid()).min(2),
  topic: topicPattern,
  action_type: z.literal('multicast'),
  payload: z.record(z.unknown()).optional(),
  require_ack: z.boolean().default(false),
  timestamp: z.string().datetime(),
});

export const AgentActionSchema = z.discriminatedUnion('type', [
  DirectActionSchema,
  BroadcastActionSchema,
  MulticastActionSchema,
]);
export type AgentAction = z.infer<typeof AgentActionSchema>;
export type DirectAction = z.infer<typeof DirectActionSchema>;
export type BroadcastAction = z.infer<typeof BroadcastActionSchema>;
export type MulticastAction = z.infer<typeof MulticastActionSchema>;

// ─── Response Schemas ─────────────────────────────────────────────

const SuccessResponseSchema = z.object({
  type: z.literal('success'),
  response_id: z.string().uuid(),
  correlation_id: z.string().uuid(),
  responder_id: z.string().uuid(),
  original_sender_id: z.string().uuid(),
  topic: z.string().min(1),
  result: z.object({
    status: z.literal('ok'),
    data: z.unknown().optional(),
    content_type: z.enum(['text', 'json', 'binary', 'tool_result']).optional(),
  }).passthrough(),
  processing_time_ms: z.number().min(0).optional(),
  timestamp: z.string().datetime(),
});

const ErrorAgentResponseSchema = z.object({
  type: z.literal('error'),
  response_id: z.string().uuid(),
  correlation_id: z.string().uuid(),
  responder_id: z.string().uuid(),
  original_sender_id: z.string().uuid(),
  topic: z.string().min(1),
  error: z.object({
    code: z.string(),
    message: z.string().min(1),
    details: z.record(z.unknown()).optional(),
    retryable: z.boolean().optional(),
  }),
  timestamp: z.string().datetime(),
});

const AckResponseSchema = z.object({
  type: z.literal('ack'),
  response_id: z.string().uuid(),
  correlation_id: z.string().uuid(),
  responder_id: z.string().uuid(),
  timestamp: z.string().datetime(),
});

export const AgentResponseSchema = z.discriminatedUnion('type', [
  SuccessResponseSchema,
  ErrorAgentResponseSchema,
  AckResponseSchema,
]);
export type AgentResponse = z.infer<typeof AgentResponseSchema>;
export type SuccessResponse = z.infer<typeof SuccessResponseSchema>;
export type ErrorAgentResponse = z.infer<typeof ErrorAgentResponseSchema>;
export type AckResponse = z.infer<typeof AckResponseSchema>;

// ─── Broadcast Event Schema ───────────────────────────────────────

export const AgentBroadcastSchema = z.object({
  broadcast_id: z.string().uuid(),
  sender_id: z.string().uuid(),
  topic: topicPattern,
  event: z.enum([
    'agent_online', 'agent_offline', 'agent_error',
    'task_started', 'task_progress', 'task_completed', 'task_failed',
    'model_updated', 'config_changed',
    'generation_end', 'evaluation_done', 'termination',
    'episode_end', 'training_step', 'checkpoint_saved',
  ]),
  payload: z.record(z.unknown()).optional(),
  scope: z.enum(['global', 'session', 'namespace']).default('global'),
  scope_id: z.string().nullable().optional(),
  ttl_ms: z.number().int().min(0).optional(),
  timestamp: z.string().datetime(),
});
export type AgentBroadcast = z.infer<typeof AgentBroadcastSchema>;

// ─── Communication Envelope (wraps any message type) ──────────────

export const CommunicationEnvelopeSchema = z.object({
  envelope_id: z.string().uuid(),
  version: z.literal('1.0'),
  source: z.enum(['agent', 'user', 'system']),
  message: z.union([AgentActionSchema, AgentResponseSchema, AgentBroadcastSchema]),
  metadata: z.record(z.unknown()).optional(),
});
export type CommunicationEnvelope = z.infer<typeof CommunicationEnvelopeSchema>;
