"""Preset test scenarios for evolution-engine factories.

Valid defaults, edge cases, and boundary values for comprehensive testing.
"""
from __future__ import annotations

import uuid

import numpy as np

from tests.factories.evoforge_factory import (
    RealGenomeFactory,
    BinaryGenomeFactory,
    TreeGenomeFactory,
    TreeNodeFactory,
    IndividualFactory,
    PopulationFactory,
    GenerationStatsFactory,
    TerminationCriteriaFactory,
    HistoryFactory,
)


# ===========================================================================
# GENOME SCENARIOS
# ===========================================================================

class GenomeScenarios:
    """Preset genome configurations for tests."""

    @classmethod
    def valid_real(cls) -> dict:
        return {"name": "valid_real", "factory": "RealGenomeFactory", "data": RealGenomeFactory.create()}

    @classmethod
    def valid_binary(cls) -> dict:
        return {"name": "valid_binary", "factory": "BinaryGenomeFactory", "data": BinaryGenomeFactory.create()}

    @classmethod
    def valid_tree(cls) -> dict:
        return {"name": "valid_tree", "factory": "TreeGenomeFactory", "data": TreeGenomeFactory.create()}

    @classmethod
    def single_gene(cls) -> dict:
        return {"name": "single_gene_real", "data": RealGenomeFactory.create(genes=[0.5], bounds=[(-1.0, 1.0)])}

    @classmethod
    def large_genome(cls) -> dict:
        n = 100
        genes = np.random.default_rng(42).uniform(-10, 10, n)
        bounds = [(-10.0, 10.0)] * n
        return {"name": "large_real_100d", "data": RealGenomeFactory.create(genes=genes, bounds=bounds)}

    @classmethod
    def all_true_binary(cls) -> dict:
        return {"name": "all_true_binary", "data": BinaryGenomeFactory.create(genes=[True] * 8)}

    @classmethod
    def all_false_binary(cls) -> dict:
        return {"name": "all_false_binary", "data": BinaryGenomeFactory.create(genes=[False] * 8)}

    @classmethod
    def deep_tree(cls) -> dict:
        return {"name": "deep_tree_6", "data": TreeGenomeFactory.create(max_depth=6)}

    @classmethod
    def flat_tree(cls) -> dict:
        return {"name": "flat_tree_leaf", "data": TreeGenomeFactory.create(root=TreeNodeFactory.leaf("x"), max_depth=1)}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [
            cls.valid_real(),
            cls.valid_binary(),
            cls.valid_tree(),
            cls.single_gene(),
            cls.large_genome(),
            cls.all_true_binary(),
            cls.all_false_binary(),
            cls.deep_tree(),
            cls.flat_tree(),
        ]


# ===========================================================================
# INDIVIDUAL SCENARIOS
# ===========================================================================

class IndividualScenarios:
    """Preset individual configurations for tests."""

    @classmethod
    def unevaluated(cls) -> dict:
        return {"name": "unevaluated", "data": IndividualFactory.create(fitness=None)}

    @classmethod
    def high_fitness(cls) -> dict:
        return {"name": "high_fitness", "data": IndividualFactory.create(fitness=0.99)}

    @classmethod
    def low_fitness(cls) -> dict:
        return {"name": "low_fitness", "data": IndividualFactory.create(fitness=0.01)}

    @classmethod
    def zero_fitness(cls) -> dict:
        return {"name": "zero_fitness", "data": IndividualFactory.create(fitness=0.0)}

    @classmethod
    def negative_fitness(cls) -> dict:
        return {"name": "negative_fitness", "data": IndividualFactory.create(fitness=-5.0)}

    @classmethod
    def with_parents(cls) -> dict:
        p1, p2 = uuid.uuid4(), uuid.uuid4()
        return {"name": "with_parents", "data": IndividualFactory.create(parents=[p1, p2], generation=5)}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [cls.unevaluated(), cls.high_fitness(), cls.low_fitness(),
                cls.zero_fitness(), cls.negative_fitness(), cls.with_parents()]


# ===========================================================================
# POPULATION SCENARIOS
# ===========================================================================

class PopulationScenarios:
    """Preset population configurations for tests."""

    @classmethod
    def small(cls) -> dict:
        return {"name": "small_pop_4", "data": PopulationFactory.create(size=4)}

    @classmethod
    def standard(cls) -> dict:
        return {"name": "standard_pop_20", "data": PopulationFactory.create(size=20)}

    @classmethod
    def large(cls) -> dict:
        return {"name": "large_pop_100", "data": PopulationFactory.create(size=100)}

    @classmethod
    def empty(cls) -> dict:
        return {"name": "empty_pop", "data": PopulationFactory.create_empty()}

    @classmethod
    def single(cls) -> dict:
        return {"name": "single_individual", "data": PopulationFactory.create_single(fitness=0.75)}

    @classmethod
    def unevaluated(cls) -> dict:
        return {"name": "unevaluated_pop", "data": PopulationFactory().with_size(10).without_fitness().build()}

    @classmethod
    def converged(cls) -> dict:
        return {"name": "converged_pop", "data": PopulationFactory().with_size(10).with_fitness_range(0.95, 0.96).build()}

    @classmethod
    def diverse(cls) -> dict:
        return {"name": "diverse_pop", "data": PopulationFactory().with_size(20).with_fitness_range(0.01, 0.99).build()}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [cls.small(), cls.standard(), cls.large(), cls.empty(),
                cls.single(), cls.unevaluated(), cls.converged(), cls.diverse()]


# ===========================================================================
# TERMINATION SCENARIOS
# ===========================================================================

class TerminationScenarios:
    """Preset termination criteria configurations for tests."""

    @classmethod
    def max_gen_only(cls) -> dict:
        return {"name": "max_gen_50", "data": TerminationCriteriaFactory.create_max_gen_only(50)}

    @classmethod
    def fitness_only(cls) -> dict:
        return {"name": "fitness_0.9", "data": TerminationCriteriaFactory.create_fitness_only(0.9)}

    @classmethod
    def convergence_only(cls) -> dict:
        return {"name": "convergence_15", "data": TerminationCriteriaFactory.create_convergence_only(15)}

    @classmethod
    def combined(cls) -> dict:
        return {"name": "combined_all", "data": TerminationCriteriaFactory.create(
            max_generations=100, fitness_threshold=0.95, convergence_generations=10)}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [cls.max_gen_only(), cls.fitness_only(), cls.convergence_only(), cls.combined()]


# ===========================================================================
# HISTORY SCENARIOS
# ===========================================================================

class HistoryScenarios:
    """Preset evolution history configurations for tests."""

    @classmethod
    def short(cls) -> dict:
        return {"name": "short_5gen", "data": HistoryFactory.create(n_generations=5)}

    @classmethod
    def standard(cls) -> dict:
        return {"name": "standard_20gen", "data": HistoryFactory.create(n_generations=20)}

    @classmethod
    def long(cls) -> dict:
        return {"name": "long_100gen", "data": HistoryFactory.create(n_generations=100)}

    @classmethod
    def flat(cls) -> dict:
        return {"name": "flat_fitness", "data": HistoryFactory.create(n_generations=10, start_fitness=0.5, end_fitness=0.5)}

    @classmethod
    def declining(cls) -> dict:
        return {"name": "declining_fitness", "data": HistoryFactory.create(n_generations=10, start_fitness=0.9, end_fitness=0.1)}

    @classmethod
    def all_scenarios(cls) -> list[dict]:
        return [cls.short(), cls.standard(), cls.long(), cls.flat(), cls.declining()]
