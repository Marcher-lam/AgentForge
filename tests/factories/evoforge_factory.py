"""Evolution-engine test data factories.

Builders: RealGenome, BinaryGenome, TreeGenome, Individual, Population,
          GenerationStats, TerminationCriteria.
Scenarios: valid defaults, edge cases, boundary values.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np

from agentforge.evoforge.genomes.real import RealGenome
from agentforge.evoforge.genomes.binary import BinaryGenome
from agentforge.evoforge.genomes.tree import TreeGenome, TreeNode
from agentforge.evoforge.engine.population import Individual, Population
from agentforge.evoforge.engine.callbacks import GenerationStats
from agentforge.evoforge.engine.termination import TerminationCriteria


# ---------------------------------------------------------------------------
# RealGenome
# ---------------------------------------------------------------------------
class RealGenomeFactory:
    """Build RealGenome instances for tests."""

    def __init__(self):
        self._genes: np.ndarray | None = None
        self._bounds: list[tuple[float, float]] | None = None
        self._fitness: float | None = None

    def with_genes(self, genes: list[float] | np.ndarray) -> RealGenomeFactory:
        self._genes = np.array(genes, dtype=float)
        return self

    def with_bounds(self, bounds: list[tuple[float, float]]) -> RealGenomeFactory:
        self._bounds = bounds
        return self

    def with_fitness(self, fitness: float | None) -> RealGenomeFactory:
        self._fitness = fitness
        return self

    def build(self) -> RealGenome:
        genes = self._genes if self._genes is not None else np.array([0.5, -0.3, 0.8])
        bounds = self._bounds if self._bounds is not None else [(-1.0, 1.0)] * len(genes)
        return RealGenome(genes=genes, bounds=bounds, fitness=self._fitness)

    @classmethod
    def create(cls, **kwargs) -> RealGenome:
        f = cls()
        if "genes" in kwargs:
            f.with_genes(kwargs["genes"])
        if "bounds" in kwargs:
            f.with_bounds(kwargs["bounds"])
        if "fitness" in kwargs:
            f.with_fitness(kwargs["fitness"])
        return f.build()

    @classmethod
    def create_hpo_genes(cls) -> RealGenome:
        """Genes representing PPO hyperparams in search space."""
        return cls().with_genes(
            [0.0003, 2048.0, 64.0, 0.99, 0.95, 0.2, 0.01, 10.0, 256.0, 256.0]
        ).with_bounds(
            [(0.0001, 0.01), (32, 16384), (8, 4096), (0.9, 0.999),
             (0.8, 1.0), (0.05, 0.5), (0.0, 0.1), (1, 50), (8, 512), (8, 512)]
        ).with_fitness(350.5).build()


# ---------------------------------------------------------------------------
# BinaryGenome
# ---------------------------------------------------------------------------
class BinaryGenomeFactory:
    """Build BinaryGenome instances for tests."""

    def __init__(self):
        self._genes: np.ndarray | None = None
        self._fitness: float | None = None

    def with_genes(self, genes: list[bool] | np.ndarray) -> BinaryGenomeFactory:
        self._genes = np.array(genes, dtype=bool)
        return self

    def with_fitness(self, fitness: float | None) -> BinaryGenomeFactory:
        self._fitness = fitness
        return self

    def build(self) -> BinaryGenome:
        genes = self._genes if self._genes is not None else np.array([True, False, True, True])
        return BinaryGenome(genes=genes, fitness=self._fitness)

    @classmethod
    def create(cls, **kwargs) -> BinaryGenome:
        f = cls()
        if "genes" in kwargs:
            f.with_genes(kwargs["genes"])
        if "fitness" in kwargs:
            f.with_fitness(kwargs["fitness"])
        return f.build()


# ---------------------------------------------------------------------------
# TreeGenome / TreeNode
# ---------------------------------------------------------------------------
class TreeNodeFactory:
    """Build TreeNode instances for tests."""

    @classmethod
    def leaf(cls, value: str | float = "x") -> TreeNode:
        return TreeNode(value=value, children=[])

    @classmethod
    def branch(cls, value: str = "+", left: TreeNode | None = None, right: TreeNode | None = None) -> TreeNode:
        return TreeNode(
            value=value,
            children=[left or cls.leaf(), right or cls.leaf()],
        )

    @classmethod
    def deep(cls, max_depth: int = 3) -> TreeNode:
        if max_depth <= 1:
            return cls.leaf(np.random.choice(["x", "y", 1.0, -1.0]))
        op = np.random.choice(["+", "-", "*"])
        return cls.branch(op, cls.deep(max_depth - 1), cls.deep(max_depth - 1))


class TreeGenomeFactory:
    """Build TreeGenome instances for tests."""

    def __init__(self):
        self._root: TreeNode | None = None
        self._max_depth: int = 4

    def with_root(self, root: TreeNode) -> TreeGenomeFactory:
        self._root = root
        return self

    def with_max_depth(self, depth: int) -> TreeGenomeFactory:
        self._max_depth = depth
        return self

    def with_fitness(self, fitness: float | None) -> TreeGenomeFactory:
        self._fitness = fitness
        return self

    def build(self) -> TreeGenome:
        root = self._root or TreeNodeFactory.deep(self._max_depth)
        return TreeGenome(root=root, max_depth=self._max_depth, fitness=self._fitness)

    def __init__(self):
        self._root: TreeNode | None = None
        self._max_depth: int = 4
        self._fitness: float | None = None

    @classmethod
    def create(cls, **kwargs) -> TreeGenome:
        f = cls()
        if "root" in kwargs:
            f.with_root(kwargs["root"])
        if "max_depth" in kwargs:
            f.with_max_depth(kwargs["max_depth"])
        if "fitness" in kwargs:
            f.with_fitness(kwargs["fitness"])
        return f.build()


# ---------------------------------------------------------------------------
# Individual
# ---------------------------------------------------------------------------
class IndividualFactory:
    """Build Individual instances for tests."""

    def __init__(self):
        self._id: uuid.UUID = uuid.uuid4()
        self._genome: Any = RealGenomeFactory.create()
        self._generation: int = 0
        self._parents: list[uuid.UUID] = []
        self._fitness: float | None = None

    def with_id(self, id: uuid.UUID) -> IndividualFactory:
        self._id = id
        return self

    def with_genome(self, genome: Any) -> IndividualFactory:
        self._genome = genome
        return self

    def with_generation(self, gen: int) -> IndividualFactory:
        self._generation = gen
        return self

    def with_parents(self, parents: list[uuid.UUID]) -> IndividualFactory:
        self._parents = parents
        return self

    def with_fitness(self, fitness: float | None) -> IndividualFactory:
        self._fitness = fitness
        return self

    def build(self) -> Individual:
        ind = Individual(
            id=self._id,
            genome=self._genome,
            generation=self._generation,
            parents=self._parents,
        )
        ind.fitness = self._fitness
        return ind

    @classmethod
    def create(cls, **kwargs) -> Individual:
        f = cls()
        if "id" in kwargs:
            f.with_id(kwargs["id"])
        if "genome" in kwargs:
            f.with_genome(kwargs["genome"])
        if "generation" in kwargs:
            f.with_generation(kwargs["generation"])
        if "parents" in kwargs:
            f.with_parents(kwargs["parents"])
        if "fitness" in kwargs:
            f.with_fitness(kwargs["fitness"])
        return f.build()

    @classmethod
    def create_evaluated(cls, fitness: float = 0.85) -> Individual:
        return cls().with_fitness(fitness).build()

    @classmethod
    def create_with_real_genome(cls, fitness: float = 100.0) -> Individual:
        return cls().with_genome(RealGenomeFactory.create_hpo_genes()).with_fitness(fitness).build()


# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------
class PopulationFactory:
    """Build Population instances for tests."""

    def __init__(self):
        self._individuals: list[Individual] | None = None
        self._size: int = 10
        self._fitness_range: tuple[float, float] = (0.1, 1.0)
        self._with_fitness: bool = True

    def with_size(self, size: int) -> PopulationFactory:
        self._size = size
        return self

    def with_individuals(self, individuals: list[Individual]) -> PopulationFactory:
        self._individuals = individuals
        return self

    def with_fitness_range(self, lo: float, hi: float) -> PopulationFactory:
        self._fitness_range = (lo, hi)
        return self

    def without_fitness(self) -> PopulationFactory:
        self._with_fitness = False
        return self

    def build(self) -> Population:
        if self._individuals is not None:
            return Population(self._individuals)

        rng = np.random.default_rng(42)
        individuals = []
        for i in range(self._size):
            lo, hi = self._fitness_range
            fitness = rng.uniform(lo, hi) if self._with_fitness else None
            ind = IndividualFactory.create(
                generation=0,
                fitness=fitness,
            )
            individuals.append(ind)
        return Population(individuals)

    @classmethod
    def create(cls, **kwargs) -> Population:
        f = cls()
        if "size" in kwargs:
            f.with_size(kwargs["size"])
        if "individuals" in kwargs:
            f.with_individuals(kwargs["individuals"])
        if "fitness_range" in kwargs:
            f.with_fitness_range(*kwargs["fitness_range"])
        return f.build()

    @classmethod
    def create_single(cls, fitness: float = 0.5) -> Population:
        return cls().with_size(1).with_fitness_range(fitness, fitness).build()

    @classmethod
    def create_empty(cls) -> Population:
        return Population([])


# ---------------------------------------------------------------------------
# GenerationStats
# ---------------------------------------------------------------------------
class GenerationStatsFactory:
    """Build GenerationStats instances for tests."""

    def __init__(self):
        self._generation: int = 1
        self._best_fitness: float = 0.95
        self._mean_fitness: float = 0.72
        self._std_fitness: float = 0.12
        self._diversity: float = 0.45
        self._best_individual_id: str = str(uuid.uuid4())
        self._timestamp: str = datetime.now(timezone.utc).isoformat()

    def with_generation(self, gen: int) -> GenerationStatsFactory:
        self._generation = gen
        return self

    def with_best_fitness(self, bf: float) -> GenerationStatsFactory:
        self._best_fitness = bf
        return self

    def with_mean_fitness(self, mf: float) -> GenerationStatsFactory:
        self._mean_fitness = mf
        return self

    def with_std_fitness(self, sf: float) -> GenerationStatsFactory:
        self._std_fitness = sf
        return self

    def with_diversity(self, d: float) -> GenerationStatsFactory:
        self._diversity = d
        return self

    def build(self) -> GenerationStats:
        return GenerationStats(
            generation=self._generation,
            best_fitness=self._best_fitness,
            mean_fitness=self._mean_fitness,
            std_fitness=self._std_fitness,
            diversity=self._diversity,
            best_individual_id=self._best_individual_id,
            timestamp=self._timestamp,
        )

    @classmethod
    def create(cls, **kwargs) -> GenerationStats:
        f = cls()
        for k, v in kwargs.items():
            method = getattr(f, f"with_{k}", None)
            if method:
                method(v)
        return f.build()

    @classmethod
    def create_converged(cls) -> GenerationStats:
        return cls().with_best_fitness(0.999).with_mean_fitness(0.998).with_std_fitness(0.001).with_diversity(0.01).build()

    @classmethod
    def create_early(cls) -> GenerationStats:
        return cls().with_generation(1).with_best_fitness(0.1).with_mean_fitness(0.05).with_std_fitness(0.08).with_diversity(0.95).build()


# ---------------------------------------------------------------------------
# TerminationCriteria
# ---------------------------------------------------------------------------
class TerminationCriteriaFactory:
    """Build TerminationCriteria instances for tests."""

    def __init__(self):
        self._max_generations: int | None = 100
        self._fitness_threshold: float | None = 0.95
        self._convergence_generations: int | None = None
        self._convergence_threshold: float = 1e-6

    def with_max_generations(self, mg: int | None) -> TerminationCriteriaFactory:
        self._max_generations = mg
        return self

    def with_fitness_threshold(self, ft: float | None) -> TerminationCriteriaFactory:
        self._fitness_threshold = ft
        return self

    def with_convergence(self, generations: int = 10, threshold: float = 1e-6) -> TerminationCriteriaFactory:
        self._convergence_generations = generations
        self._convergence_threshold = threshold
        return self

    def build(self) -> TerminationCriteria:
        return TerminationCriteria(
            max_generations=self._max_generations,
            fitness_threshold=self._fitness_threshold,
            convergence_generations=self._convergence_generations,
            convergence_threshold=self._convergence_threshold,
        )

    @classmethod
    def create(cls, **kwargs) -> TerminationCriteria:
        f = cls()
        if "max_generations" in kwargs:
            f.with_max_generations(kwargs["max_generations"])
        if "fitness_threshold" in kwargs:
            f.with_fitness_threshold(kwargs["fitness_threshold"])
        if "convergence_generations" in kwargs:
            f.with_convergence(kwargs.get("convergence_generations", 10), kwargs.get("convergence_threshold", 1e-6))
        return f.build()

    @classmethod
    def create_max_gen_only(cls, max_gen: int = 50) -> TerminationCriteria:
        return cls().with_max_generations(max_gen).with_fitness_threshold(None).build()

    @classmethod
    def create_fitness_only(cls, threshold: float = 0.9) -> TerminationCriteria:
        return cls().with_max_generations(None).with_fitness_threshold(threshold).build()

    @classmethod
    def create_convergence_only(cls, generations: int = 15) -> TerminationCriteria:
        return cls().with_max_generations(None).with_fitness_threshold(None).with_convergence(generations).build()


# ---------------------------------------------------------------------------
# History (list[GenerationStats])
# ---------------------------------------------------------------------------
class HistoryFactory:
    """Build a list of GenerationStats simulating evolution progress."""

    @classmethod
    def create(cls, n_generations: int = 20, start_fitness: float = 0.1, end_fitness: float = 0.95) -> list[GenerationStats]:
        rng = np.random.default_rng(42)
        fitnesses = np.linspace(start_fitness, end_fitness, n_generations)
        history = []
        for i in range(n_generations):
            bf = fitnesses[i]
            noise = rng.uniform(-0.02, 0.02)
            mf = max(0, bf - rng.uniform(0.05, 0.2) + noise)
            sf = rng.uniform(0.01, 0.1)
            div = max(0.01, 1.0 - i / n_generations + rng.uniform(-0.05, 0.05))
            history.append(GenerationStatsFactory.create(
                generation=i + 1,
                best_fitness=round(bf, 4),
                mean_fitness=round(mf, 4),
                std_fitness=round(sf, 4),
                diversity=round(div, 4),
            ))
        return history
