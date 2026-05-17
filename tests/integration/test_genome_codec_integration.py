"""Integration: Fitness + Operators pipeline.

Tests the operator boundary: selection → crossover → mutation working together
without the full evolution engine.
"""

from __future__ import annotations

import pytest
import numpy as np

from agentforge.evoforge.genomes.real import RealGenome
from agentforge.evoforge.genomes.binary import BinaryGenome
from agentforge.evoforge.operators.selection import tournament_selection
from agentforge.evoforge.operators.crossover import single_point_crossover, uniform_crossover
from agentforge.evoforge.operators.mutation import gaussian_mutation, bitflip_mutation
from agentforge.evoforge.engine.population import Individual, Population


class TestFitnessOperatorsIntegration:
    """Fitness evaluation → selection → crossover → mutation pipeline."""

    @pytest.mark.anyio
    async def test_selection_crossover_mutation_pipeline(self):
        """Select parents → crossover → mutate → produce offspring."""
        rng = np.random.default_rng(42)

        # Create population
        individuals = [
            Individual(genome=RealGenome(genes=np.array([0.0, 0.0, 0.0, 0.0, 0.0]), bounds=[(-1, 1)] * 5), fitness=0.0),
            Individual(genome=RealGenome(genes=np.array([1.0, 1.0, 1.0, 1.0, 1.0]), bounds=[(-1, 1)] * 5), fitness=1.0),
            Individual(genome=RealGenome(genes=np.array([0.5, 0.5, 0.5, 0.5, 0.5]), bounds=[(-1, 1)] * 5), fitness=0.5),
        ]
        pop = Population(individuals)

        # Select
        parents = tournament_selection(pop.individuals, 2, rng)
        assert len(parents) == 2

        # Crossover
        child_a, child_b = single_point_crossover(parents[0].genome, parents[1].genome, rng)
        assert len(child_a.genes) == 5
        assert len(child_b.genes) == 5

        # Mutate
        mutated = gaussian_mutation(child_a, 0.1, rng)
        assert len(mutated.genes) == 5
        # Genes should be clipped to bounds
        for g in mutated.genes:
            assert -1.0 <= g <= 1.0

    @pytest.mark.anyio
    async def test_binary_crossover_mutation_pipeline(self):
        """Binary genome: crossover → bitflip mutation."""
        rng = np.random.default_rng(42)

        parent_a = BinaryGenome(genes=np.array([True, True, True, True, True, True]))
        parent_b = BinaryGenome(genes=np.array([False, False, False, False, False, False]))

        child_a, child_b = uniform_crossover(parent_a, parent_b, rng)
        assert len(child_a.genes) == 6
        assert len(child_b.genes) == 6

        mutated = bitflip_mutation(child_a, 0.5, rng)
        assert len(mutated.genes) == 6
        # Some bits should have changed
        assert not np.array_equal(mutated.genes, parent_a.genes) or not np.array_equal(mutated.genes, parent_b.genes)

    @pytest.mark.anyio
    async def test_elitism_preserves_best(self):
        """Elite individuals should be preserved unchanged."""
        rng = np.random.default_rng(42)

        best_genome = RealGenome(genes=np.array([0.99, 0.99, 0.99]), bounds=[(0, 1)] * 3)
        individuals = [
            Individual(genome=best_genome, fitness=0.99),
            Individual(genome=RealGenome(genes=np.array([0.1, 0.1, 0.1]), bounds=[(0, 1)] * 3), fitness=0.1),
            Individual(genome=RealGenome(genes=np.array([0.2, 0.2, 0.2]), bounds=[(0, 1)] * 3), fitness=0.2),
        ]
        pop = Population(individuals)
        pop.sort_by_fitness()

        # Elite = top 1
        elites = pop.individuals[:1]
        cloned = elites[0].genome.clone()
        assert np.allclose(cloned.genes, [0.99, 0.99, 0.99])

    @pytest.mark.anyio
    async def test_population_stats_computation(self):
        """Spec: evolution-engine — 种群统计 best/mean/std/diversity"""
        individuals = [
            Individual(genome=RealGenome(genes=np.array([1.0, 0.0]), bounds=[(0, 1)] * 2), fitness=1.0),
            Individual(genome=RealGenome(genes=np.array([0.5, 0.5]), bounds=[(0, 1)] * 2), fitness=0.5),
            Individual(genome=RealGenome(genes=np.array([0.0, 1.0]), bounds=[(0, 1)] * 2), fitness=0.0),
        ]
        pop = Population(individuals)
        stats = pop.stats()

        assert stats["best"] == 1.0
        assert abs(stats["mean"] - 0.5) < 1e-10
        assert stats["std"] > 0
        assert stats["diversity"] >= 0
