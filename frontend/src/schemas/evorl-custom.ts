import { z } from 'zod';
import {
  EvoRLWorkflowSchema,
  EvolutionConfigSchema,
  EvaluationConfigSchema,
  type EvoRLWorkflow,
  type EvolutionConfig,
  type EvaluationConfig,
} from './evorl-workflow';

// ─── Custom Algorithm ──────────────────────────────────────────

export const RangeConstraintSchema = z.object({
  value: z.number(),
  min: z.number(),
  max: z.number(),
  scale: z.enum(['linear', 'log', 'log2']).optional(),
  dtype: z.enum(['float', 'int']).optional(),
});
export type RangeConstraint = z.infer<typeof RangeConstraintSchema>;

const HyperparamValueSchema = z.union([
  z.number(),
  z.number().int(),
  z.string(),
  z.boolean(),
  z.array(z.number()),
  RangeConstraintSchema,
]);

export const CustomAlgorithmConfigSchema = z.object({
  algorithm: z.string().min(1).refine(v => !['PPO', 'DQN'].includes(v), {
    message: 'Use PPOHyperparams or DQNHyperparams for built-in algorithms',
  }),
  version: z.string().regex(/^[0-9]+\.[0-9]+\.[0-9]+$/).optional(),
  hyperparams: z.record(HyperparamValueSchema),
  network_spec: z.object({
    input_dim: z.number().int().min(1),
    output_dim: z.number().int().min(1),
    layers: z.array(z.object({
      type: z.enum(['linear', 'lstm', 'gru', 'conv1d', 'conv2d', 'attention', 'custom']),
      units: z.number().int().min(1).optional(),
      activation: z.enum(['relu', 'tanh', 'sigmoid', 'gelu', 'swish', 'none']).optional(),
      dropout: z.number().min(0).max(1).optional(),
      custom_type: z.string().optional(),
      kwargs: z.record(z.unknown()).optional(),
    })).optional(),
    output_activation: z.string().optional(),
    normalize_input: z.boolean().optional(),
  }).optional(),
  entry_point: z.string().regex(/^[a-zA-Z_][a-zA-Z0-9_.]*:[a-zA-Z_][a-zA-Z0-9_]*$/),
});
export type CustomAlgorithmConfig = z.infer<typeof CustomAlgorithmConfigSchema>;

// ─── Fitness Strategies ────────────────────────────────────────

export const SingleObjectiveSchema = z.object({
  type: z.literal('single'),
  metric: z.enum(['mean_reward', 'median_reward', 'max_reward', 'success_rate', 'min_reward', 'custom']),
  custom_metric_fn: z.string().optional(),
  aggregation: z.enum(['mean', 'median', 'max', 'min', 'last']).optional(),
  transform: z.enum(['identity', 'negate', 'log', 'normalize', 'rank', 'custom']).optional(),
});
export type SingleObjective = z.infer<typeof SingleObjectiveSchema>;

export const MultiObjectiveSchema = z.object({
  type: z.literal('multi_objective'),
  objectives: z.array(z.object({
    name: z.string(),
    metric: z.string(),
    weight: z.number().min(0),
    direction: z.enum(['maximize', 'minimize']).optional(),
  })).min(2),
  method: z.enum(['weighted_sum', 'pareto', 'lexicographic']).optional(),
});
export type MultiObjective = z.infer<typeof MultiObjectiveSchema>;

export const CurriculumSchema = z.object({
  type: z.literal('curriculum'),
  stages: z.array(z.object({
    name: z.string(),
    metric_threshold: z.number(),
    evaluation: EvaluationConfigSchema,
  })).min(1),
});
export type Curriculum = z.infer<typeof CurriculumSchema>;

export const FitnessStrategySchema = z.discriminatedUnion('type', [
  SingleObjectiveSchema,
  MultiObjectiveSchema,
  CurriculumSchema,
]);
export type FitnessStrategy = z.infer<typeof FitnessStrategySchema>;

// ─── Resource Budget ───────────────────────────────────────────

export const ResourceBudgetSchema = z.object({
  max_wall_time_minutes: z.number().min(1).optional(),
  max_gpu_hours: z.number().min(0).optional(),
  max_cpu_cores: z.number().int().min(1).optional(),
  max_memory_gb: z.number().min(0.5).optional(),
  max_parallel_jobs: z.number().int().min(1).max(256).optional(),
});
export type ResourceBudget = z.infer<typeof ResourceBudgetSchema>;

// ─── Checkpoint Policy ────────────────────────────────────────

export const CheckpointPolicySchema = z.object({
  enabled: z.boolean().default(true),
  save_every_n_generations: z.number().int().min(1).optional(),
  save_best: z.boolean().default(true),
  max_checkpoints: z.number().int().min(1).optional(),
  path_template: z.string().optional(),
});
export type CheckpointPolicy = z.infer<typeof CheckpointPolicySchema>;

// ─── Custom Workflow Config ────────────────────────────────────

export const CustomWorkflowConfigSchema = z.object({
  algorithm_config: CustomAlgorithmConfigSchema.optional(),
  fitness_strategy: FitnessStrategySchema.optional(),
  checkpoint: CheckpointPolicySchema.optional(),
  resources: ResourceBudgetSchema.optional(),
  tags: z.array(z.string().regex(/^[a-zA-Z0-9_-]+$/)).optional(),
  metadata: z.record(z.unknown()).optional(),
  hooks: z.object({
    on_generation_start: z.string().optional(),
    on_generation_end: z.string().optional(),
    on_evaluation_start: z.string().optional(),
    on_evaluation_end: z.string().optional(),
    on_termination: z.string().optional(),
  }).optional(),
});
export type CustomWorkflowConfig = z.infer<typeof CustomWorkflowConfigSchema>;

// ─── Extended Workflow (fork of EvoRLWorkflow) ─────────────────

export const EvoRLCustomWorkflowSchema = EvoRLWorkflowSchema.extend({
  custom_config: CustomWorkflowConfigSchema.optional(),
}).transform(data => {
  // Add 'custom' as valid workflow_type via superRefine-level handling
  return data;
});
export type EvoRLCustomWorkflow = z.infer<typeof EvoRLCustomWorkflowSchema>;
