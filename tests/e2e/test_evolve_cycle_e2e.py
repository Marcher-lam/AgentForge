"""E2E: Full evolution cycle — init → evaluate → select → crossover → mutate → terminate.

Outside-in TDD outer shell — tests the complete evolution loop end-to-end.
Covers specs:
  - evolution-engine.md: Population management, evolution loop, termination, callbacks
  - genome.md: Real/Binary/Tree genome creation and operations
  - fitness.md: Fitness function registration, multi-objective, constraints
  - operators.md: Selection, crossover, mutation, replacement strategies
"""

from __future__ import annotations

import pytest
import numpy as np

from agentforge.evoforge.engine.evolution import EvolutionEngine
from agentforge.evoforge.engine.population import Individual, Population
from agentforge.evoforge.engine.termination import TerminationCriteria
from agentforge.evoforge.engine.callbacks import Callback, GenerationStats
from agentforge.evoforge.genomes.real import RealGenome
from agentforge.evoforge.genomes.binary import BinaryGenome
from agentforge.evoforge.operators.selection import tournament_selection
from agentforge.evoforge.operators.mutation import gaussian_mutation, bitflip_mutation


class TestFullEvolveCycleE2E:
    """Complete evolution: init population → evolve → converge → verify results."""

    @pytest.mark.anyio
    async def test_sphere_optimization_converges(self):
        """Spec: evolution-engine — 标准进化流程, 种子控制可复现"""
        # Sphere function: minimize sum of squares, optimum at 0
        def sphere_fitness(individuals: list[Individual]) -> list[float]:
            return [-(np.sum(np.array(ind.genome.genes) ** 2)) for ind in individuals]

        genome_factory = lambda rng: RealGenome(
            genes=rng.uniform(-5.0, 5.0, size=10),
            bounds=[(-5.0, 5.0)] * 10,
        )

        termination = TerminationCriteria(max_generations=50)
        engine = EvolutionEngine(
            fitness_fn=sphere_fitness,
            selection_fn=tournament_selection,
            mutation_fn=gaussian_mutation,
            mutation_rate=0.2,
            elite_size=2,
            termination=termination,
            seed=42,
        )

        rng = np.random.default_rng(42)
        population = Population.random(genome_factory, size=30, rng=rng)

        final_pop = engine.evolve(population)

        assert engine.generation == 50
        assert engine.termination_reason == "MAX_GENERATIONS"
        assert final_pop is not None
        assert len(final_pop.individuals) == 30

        # Best fitness should be close to 0 (negative of sphere)
        best = final_pop.best()
        assert best is not None
        assert best.fitness > -10.0  # reasonably converged

    @pytest.mark.anyio
    async def test_seed_reproducibility(self):
        """Spec: evolution-engine — 种子控制可复现"""
        def sphere_fitness(individuals: list[Individual]) -> list[float]:
            return [-(np.sum(np.array(ind.genome.genes) ** 2)) for ind in individuals]

        genome_factory = lambda rng: RealGenome(
            genes=rng.uniform(-5.0, 5.0, size=5),
            bounds=[(-5.0, 5.0)] * 5,
        )

        results = []
        for _ in range(2):
            engine = EvolutionEngine(
                fitness_fn=sphere_fitness,
                mutation_fn=gaussian_mutation,
                termination=TerminationCriteria(max_generations=10),
                seed=42,
            )
            pop = Population.random(genome_factory, size=20, rng=np.random.default_rng(42))
            final = engine.evolve(pop)
            best = final.best()
            results.append(best.fitness)

        assert results[0] == results[1]  # identical results with same seed

    @pytest.mark.anyio
    async def test_fitness_threshold_termination(self):
        """Spec: evolution-engine — 适应度阈值终止"""
        call_count = 0

        def perfect_fitness(individuals: list[Individual]) -> list[float]:
            nonlocal call_count
            call_count += 1
            return [1.0] * len(individuals)

        engine = EvolutionEngine(
            fitness_fn=perfect_fitness,
            mutation_fn=gaussian_mutation,
            termination=TerminationCriteria(
                max_generations=1000,
                fitness_threshold=0.99,
            ),
            seed=42,
        )

        genome_factory = lambda rng: RealGenome(genes=np.array([0.0] * 5), bounds=[(-1.0, 1.0)] * 5)
        pop = Population.random(genome_factory, size=10, rng=np.random.default_rng(42))
        final = engine.evolve(pop)

        assert engine.termination_reason == "FITNESS_THRESHOLD"
        assert engine.generation == 1  # terminates immediately after first eval

    @pytest.mark.anyio
    async def test_callbacks_fire_in_order(self):
        """Spec: evolution-engine — 回调 on_generation_end / on_termination"""
        events: list[str] = []

        class Tracker(Callback):
            def on_generation_end(self, stats: GenerationStats, population) -> None:
                events.append(f"gen:{stats.generation}")

            def on_termination(self, reason: str, stats: GenerationStats) -> None:
                events.append(f"term:{reason}")

        def fitness(individuals: list[Individual]) -> list[float]:
            return [0.0] * len(individuals)

        engine = EvolutionEngine(
            fitness_fn=fitness,
            mutation_fn=gaussian_mutation,
            termination=TerminationCriteria(max_generations=3),
            callback=Tracker(),
            seed=42,
        )

        genome_factory = lambda rng: RealGenome(genes=np.array([0.0] * 3), bounds=[(-1.0, 1.0)] * 3)
        pop = Population.random(genome_factory, size=5, rng=np.random.default_rng(42))
        engine.evolve(pop)

        assert events == ["gen:1", "gen:2", "gen:3", "term:MAX_GENERATIONS"]

    @pytest.mark.anyio
    async def test_history_records_all_generations(self):
        """Spec: evolution-engine — 种群统计 per generation"""
        def fitness(individuals: list[Individual]) -> list[float]:
            return [float(i) for i in range(len(individuals))]

        engine = EvolutionEngine(
            fitness_fn=fitness,
            mutation_fn=gaussian_mutation,
            termination=TerminationCriteria(max_generations=5),
            seed=42,
        )

        genome_factory = lambda rng: RealGenome(genes=np.array([0.0] * 3), bounds=[(-1.0, 1.0)] * 3)
        pop = Population.random(genome_factory, size=10, rng=np.random.default_rng(42))
        engine.evolve(pop)

        assert len(engine.history) == 5
        for stats in engine.history:
            assert stats.best_fitness >= stats.mean_fitness
            assert stats.generation > 0

    @pytest.mark.anyio
    async def test_binary_genome_evolution(self):
        """Spec: genome.md — 二进制位串进化"""
        def onemax_fitness(individuals: list[Individual]) -> list[float]:
            return [float(np.sum(ind.genome.genes)) for ind in individuals]

        genome_factory = lambda rng: BinaryGenome(genes=rng.integers(0, 2, size=20).astype(bool))

        engine = EvolutionEngine(
            fitness_fn=onemax_fitness,
            mutation_fn=bitflip_mutation,
            mutation_rate=0.05,
            termination=TerminationCriteria(max_generations=30),
            seed=42,
        )

        pop = Population.random(genome_factory, size=20, rng=np.random.default_rng(42))
        final = engine.evolve(pop)

        best = final.best()
        assert best.fitness >= 15.0  # should find many 1s
