import { z } from 'zod';

// ─── Shared Sub-Schemas ────────────────────────────────────────

const BoundsSchema = z.object({
  min: z.number(),
  max: z.number(),
  scale: z.enum(['linear', 'log']).optional(),
});

const IntBoundsSchema = z.object({
  min: z.number().int(),
  max: z.number().int(),
  step: z.number().int().min(1).optional(),
});

// ─── RL Hyperparameters ────────────────────────────────────────

export const PPOHyperparamsSchema = z.object({
  algorithm: z.literal('PPO'),
  learning_rate: z.number().positive().max(0.1),
  n_steps: z.number().int().min(32).max(16384),
  batch_size: z.number().int().min(8).max(4096),
  epochs: z.number().int().min(1).max(50).optional(),
  gamma: z.number().positive().max(1),
  gae_lambda: z.number().min(0).max(1).optional(),
  clip_range: z.number().positive().max(1).optional(),
  entropy_coef: z.number().min(0).max(0.1).optional(),
  hidden_layers: z.array(z.number().int().min(8)).min(1).max(6).optional(),
});
export type PPOHyperparams = z.infer<typeof PPOHyperparamsSchema>;

export const DQNHyperparamsSchema = z.object({
  algorithm: z.literal('DQN'),
  learning_rate: z.number().positive().max(0.1),
  buffer_size: z.number().int().min(1000).optional(),
  batch_size: z.number().int().min(8).max(4096),
  gamma: z.number().positive().max(1),
  target_update_freq: z.number().int().min(1).optional(),
  target_update_type: z.enum(['hard', 'soft']).optional(),
  tau: z.number().positive().max(1).optional(),
  epsilon_start: z.number().min(0).max(1).optional(),
  epsilon_end: z.number().min(0).max(1).optional(),
  epsilon_decay_steps: z.number().int().min(100).optional(),
  dueling: z.boolean().optional(),
  hidden_layers: z.array(z.number().int().min(8)).min(1).max(6).optional(),
});
export type DQNHyperparams = z.infer<typeof DQNHyperparamsSchema>;

export const RLConfigSchema = z.discriminatedUnion('algorithm', [
  PPOHyperparamsSchema,
  DQNHyperparamsSchema,
]);
export type RLConfig = z.infer<typeof RLConfigSchema>;

// ─── Evaluation Config ─────────────────────────────────────────

export const EvaluationConfigSchema = z.object({
  env_id: z.string().min(1),
  max_steps: z.number().int().min(100),
  n_episodes: z.number().int().min(1).max(1000),
  seed: z.number().int().min(0).optional(),
  metric: z.enum(['mean_reward', 'median_reward', 'success_rate', 'min_reward']),
});
export type EvaluationConfig = z.infer<typeof EvaluationConfigSchema>;

// ─── Evolution Config ──────────────────────────────────────────

export const EvolutionConfigSchema = z.object({
  population_size: z.number().int().min(4).max(1000),
  max_generations: z.number().int().min(1).max(10000),
  selection: z.enum(['tournament', 'roulette', 'rank', 'elite']),
  tournament_k: z.number().int().min(2).max(10).optional(),
  crossover_rate: z.number().min(0).max(1),
  mutation_rate: z.number().min(0).max(1),
  elite_size: z.number().int().min(0).optional(),
  fitness_threshold: z.number().optional(),
  convergence_generations: z.number().int().min(1).optional(),
  seed: z.number().int().min(0).optional(),
});
export type EvolutionConfig = z.infer<typeof EvolutionConfigSchema>;

// ─── Search Space ──────────────────────────────────────────────

export const SearchSpaceSchema = z.object({
  learning_rate: BoundsSchema.optional(),
  n_steps: IntBoundsSchema.optional(),
  batch_size: IntBoundsSchema.optional(),
  gamma: BoundsSchema.optional(),
  hidden_layers: z.object({
    min_neurons: z.number().int(),
    max_neurons: z.number().int(),
    min_layers: z.number().int(),
    max_layers: z.number().int(),
  }).optional(),
});
export type SearchSpace = z.infer<typeof SearchSpaceSchema>;

// ─── Results ───────────────────────────────────────────────────

export const OptimizationResultSchema = z.object({
  best_fitness: z.number().optional(),
  best_generation: z.number().int().min(0).optional(),
  best_hyperparams: z.record(z.unknown()).optional(),
  total_evaluations: z.number().int().min(0).optional(),
  completed_at: z.string().datetime().optional(),
  termination_reason: z.enum(['MAX_GENERATIONS', 'FITNESS_THRESHOLD', 'CONVERGENCE', 'CANCELLED']).optional(),
});
export type OptimizationResult = z.infer<typeof OptimizationResultSchema>;

export const CoEvolutionResultSchema = z.object({
  best_agent_fitness: z.number().optional(),
  best_env_difficulty: z.number().optional(),
  final_round: z.number().int().optional(),
  fitness_history: z.array(z.object({
    round: z.number().int(),
    agent_fitness: z.number(),
    env_difficulty: z.number(),
  })).optional(),
  completed_at: z.string().datetime().optional(),
});
export type CoEvolutionResult = z.infer<typeof CoEvolutionResultSchema>;

// ─── Workflow Types ────────────────────────────────────────────

const baseFields = {
  workflow_id: z.string().uuid(),
  name: z.string().min(1),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime().optional(),
};

export const HyperparameterOptimizationSchema = z.object({
  ...baseFields,
  workflow_type: z.literal('hyperparameter_optimization'),
  rl_config: RLConfigSchema,
  evolution_config: EvolutionConfigSchema,
  evaluation: EvaluationConfigSchema,
  search_space: SearchSpaceSchema.optional(),
  result: OptimizationResultSchema.optional(),
});
export type HyperparameterOptimization = z.infer<typeof HyperparameterOptimizationSchema>;

export const PolicySearchSchema = z.object({
  ...baseFields,
  workflow_type: z.literal('policy_search'),
  network_architecture: z.object({
    input_dim: z.number().int().min(1),
    output_dim: z.number().int().min(1),
    hidden_layers: z.array(z.number().int()).optional(),
  }),
  evolution_config: EvolutionConfigSchema,
  evaluation: EvaluationConfigSchema,
  result: OptimizationResultSchema.optional(),
});
export type PolicySearch = z.infer<typeof PolicySearchSchema>;

export const CoEvolutionSchema = z.object({
  ...baseFields,
  workflow_type: z.literal('co_evolution'),
  agent_config: RLConfigSchema,
  env_population_config: EvolutionConfigSchema,
  agent_population_config: EvolutionConfigSchema,
  evaluation: EvaluationConfigSchema,
  rounds: z.number().int().min(1),
  current_round: z.number().int().min(0).optional(),
  result: CoEvolutionResultSchema.optional(),
});
export type CoEvolution = z.infer<typeof CoEvolutionSchema>;

export const EvoRLWorkflowSchema = z.discriminatedUnion('workflow_type', [
  HyperparameterOptimizationSchema,
  PolicySearchSchema,
  CoEvolutionSchema,
]);
export type EvoRLWorkflow = z.infer<typeof EvoRLWorkflowSchema>;
