"""Integration tests for EvolutionEngine — Task 6."""

import numpy as np
import pytest

from agentforge.evoforge.engine.evolution import EvolutionEngine
from agentforge.evoforge.engine.population import Population, Individual
from agentforge.evoforge.engine.termination import TerminationCriteria
from agentforge.evoforge.engine.callbacks import StatsCollector, GenerationStats
from agentforge.evoforge.genomes.real import RealGenome
from agentforge.evoforge.genomes.binary import BinaryGenome
from agentforge.evoforge.operators.mutation import gaussian_mutation, bitflip_mutation
from agentforge.evoforge.operators.crossover import uniform_crossover


@pytest.fixture
def rng():
    return np.random.default_rng(42)


class TestOneMax:
    """Binary genome: maximize number of True bits."""

    def test_onemax_converges(self):
        def fitness(pop):
            return [float(np.sum(ind.genome.genes)) for ind in pop]

        rng = np.random.default_rng(42)
        pop = Population.random(
            genome_factory=lambda r: BinaryGenome.random(20, rng=r),
            size=50,
            rng=rng,
        )
        engine = EvolutionEngine(
            fitness_fn=fitness,
            crossover_fn=uniform_crossover,
            mutation_fn=bitflip_mutation,
            mutation_rate=0.02,
            termination=TerminationCriteria(max_generations=100, fitness_threshold=20.0),
            seed=42,
        )
        result = engine.evolve(pop)
        best = result.best()
        assert best is not None
        assert best.fitness >= 15.0, f"OneMax best fitness: {best.fitness}"

    def test_onemax_history_recorded(self):
        def fitness(pop):
            return [float(np.sum(ind.genome.genes)) for ind in pop]

        engine = EvolutionEngine(
            fitness_fn=fitness,
            crossover_fn=uniform_crossover,
            mutation_fn=bitflip_mutation,
            mutation_rate=0.02,
            termination=TerminationCriteria(max_generations=20),
            seed=42,
        )
        pop = Population.random(
            genome_factory=lambda r: BinaryGenome.random(10, rng=r),
            size=30,
            rng=np.random.default_rng(42),
        )
        engine.evolve(pop)
        assert len(engine.history) == 20
        assert all(isinstance(s, GenerationStats) for s in engine.history)


class TestSphere:
    """Real genome: minimize sum of squares (negate for maximization)."""

    def test_sphere_improves(self):
        def fitness(pop):
            return [-float(np.sum(ind.genome.genes ** 2)) for ind in pop]

        rng = np.random.default_rng(42)
        pop = Population.random(
            genome_factory=lambda r: RealGenome.random(5, bounds=[(-5, 5)] * 5, rng=r),
            size=80,
            rng=rng,
        )
        engine = EvolutionEngine(
            fitness_fn=fitness,
            crossover_fn=uniform_crossover,
            mutation_fn=gaussian_mutation,
            mutation_rate=0.2,
            termination=TerminationCriteria(max_generations=100),
            seed=42,
        )
        result = engine.evolve(pop)
        best = result.best()
        assert best is not None
        assert best.fitness > engine.history[0].best_fitness


class TestReproducibility:
    def test_same_seed_same_result(self):
        def fitness(pop):
            return [float(np.sum(ind.genome.genes)) for ind in pop]

        def run(seed):
            rng = np.random.default_rng(seed)
            pop = Population.random(
                genome_factory=lambda r: BinaryGenome.random(10, rng=r),
                size=30,
                rng=rng,
            )
            engine = EvolutionEngine(
                fitness_fn=fitness,
                crossover_fn=uniform_crossover,
                mutation_fn=bitflip_mutation,
                mutation_rate=0.05,
                termination=TerminationCriteria(max_generations=20),
                seed=seed,
            )
            engine.evolve(pop)
            return [s.best_fitness for s in engine.history]

        result1 = run(12345)
        result2 = run(12345)
        assert result1 == result2


class TestTermination:
    def test_fitness_threshold_terminates(self):
        def fitness(pop):
            return [10.0 for _ in pop]

        engine = EvolutionEngine(
            fitness_fn=fitness,
            termination=TerminationCriteria(fitness_threshold=5.0),
            seed=42,
        )
        pop = Population.random(
            genome_factory=lambda r: RealGenome.random(3, rng=r),
            size=10,
            rng=np.random.default_rng(42),
        )
        engine.evolve(pop)
        assert engine.termination_reason == "FITNESS_THRESHOLD"
        assert engine.generation == 1

    def test_max_generations_limit(self):
        def fitness(pop):
            return [float(i) for i in range(len(pop))]

        engine = EvolutionEngine(
            fitness_fn=fitness,
            termination=TerminationCriteria(max_generations=5),
            seed=42,
        )
        pop = Population.random(
            genome_factory=lambda r: RealGenome.random(3, rng=r),
            size=10,
            rng=np.random.default_rng(42),
        )
        engine.evolve(pop)
        assert engine.generation == 5
        assert engine.termination_reason == "MAX_GENERATIONS"
