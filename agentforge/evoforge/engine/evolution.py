"""EvolutionEngine — main evolution loop."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
from numpy.random import Generator

from agentforge.evoforge.engine.callbacks import Callback, CompositeCallback, GenerationStats, StatsCollector
from agentforge.evoforge.engine.population import Individual, Population
from agentforge.evoforge.engine.termination import TerminationCriteria
from agentforge.evoforge.operators.selection import tournament_selection
from agentforge.evoforge.operators.mutation import gaussian_mutation, bitflip_mutation


class EvolutionEngine:
    """Main evolutionary loop with configurable operators, elitism, and callbacks."""
    def __init__(
        self,
        fitness_fn: Callable[[list[Any]], list[float]],
        selection_fn: Callable = tournament_selection,
        crossover_fn: Callable | None = None,
        mutation_fn: Callable = gaussian_mutation,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elite_size: int = 0,
        termination: TerminationCriteria | None = None,
        callback: Callback | None = None,
        seed: int | None = None,
    ) -> None:
        self._fitness_fn = fitness_fn
        self._selection_fn = selection_fn
        self._crossover_fn = crossover_fn
        self._mutation_fn = mutation_fn
        self._mutation_rate = mutation_rate
        self._crossover_rate = crossover_rate
        self._elite_size = elite_size
        self._termination = termination or TerminationCriteria(max_generations=100)
        self._callback = CompositeCallback([callback] if callback else [])
        self._stats = StatsCollector()
        self._callback.add(self._stats)
        self._rng: Generator = np.random.default_rng(seed)
        self._generation = 0
        self._termination_reason = ""

    @property
    def generation(self) -> int:
        """Return the current generation number."""
        return self._generation

    @property
    def history(self) -> list[GenerationStats]:
        """Return per-generation statistics collected so far."""
        return self._stats.history

    @property
    def termination_reason(self) -> str:
        """Return the reason the last evolution run stopped."""
        return self._termination_reason

    def evolve(self, population: Population) -> Population:
        """Run the evolution loop until a termination criterion is met."""
        pop = population
        while True:
            self._generation += 1
            fitnesses = self._fitness_fn(pop.individuals)
            for ind, fit in zip(pop.individuals, fitnesses):
                ind.fitness = fit

            self._callback.on_evaluation(pop.individuals, fitnesses)

            stats = pop.stats()
            best = pop.best()
            gen_stats = GenerationStats(
                generation=self._generation,
                best_fitness=stats["best"],
                mean_fitness=stats["mean"],
                std_fitness=stats["std"],
                diversity=stats["diversity"],
                best_individual_id=str(best.id) if best else "",
            )
            self._callback.on_generation_end(gen_stats, pop)

            should_stop, reason = self._termination.should_terminate(self._generation, stats["best"], stats["diversity"])
            if should_stop:
                self._termination_reason = reason
                self._callback.on_termination(reason, gen_stats)
                break

            pop = self._create_next_generation(pop, fitnesses)
        return pop

    def _create_next_generation(self, pop: Population, fitnesses: list[float]) -> Population:
        pop.sort_by_fitness()
        new_individuals: list[Individual] = []

        if self._elite_size > 0:
            elites = pop.individuals[:self._elite_size]
            for e in elites:
                new_individuals.append(Individual(
                    genome=e.genome.clone(),
                    generation=self._generation,
                    parents=[e.id],
                ))

        while len(new_individuals) < len(pop.individuals):
            parents = self._selection_fn(pop.individuals, 2, self._rng)
            p1, p2 = parents[0], parents[1]

            if self._crossover_fn and self._rng.random() < self._crossover_rate:
                c1_genome, c2_genome = self._crossover_fn(p1.genome, p2.genome, self._rng)
            else:
                c1_genome, c2_genome = p1.genome.clone(), p2.genome.clone()

            c1_genome = self._mutation_fn(c1_genome, self._mutation_rate, self._rng)
            c2_genome = self._mutation_fn(c2_genome, self._mutation_rate, self._rng)

            new_individuals.append(Individual(genome=c1_genome, generation=self._generation, parents=[p1.id, p2.id]))
            if len(new_individuals) < len(pop.individuals):
                new_individuals.append(Individual(genome=c2_genome, generation=self._generation, parents=[p1.id, p2.id]))

        return Population(new_individuals[: len(pop.individuals)])
