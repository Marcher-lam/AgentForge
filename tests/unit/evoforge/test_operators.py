"""Tests for Selection, Crossover, Mutation operators — Task 3."""

import numpy as np
import pytest

from agentforge.evoforge.genomes.real import RealGenome
from agentforge.evoforge.genomes.binary import BinaryGenome
from agentforge.evoforge.engine.population import Individual
from agentforge.evoforge.operators.selection import (
    roulette_selection,
    tournament_selection,
    elite_selection,
    rank_selection,
)
from agentforge.evoforge.operators.crossover import (
    single_point_crossover,
    uniform_crossover,
    sbx_crossover,
    multi_point_crossover,
)
from agentforge.evoforge.operators.mutation import (
    gaussian_mutation,
    uniform_mutation,
    bitflip_mutation,
    polynomial_mutation,
)


@pytest.fixture
def rng():
    return np.random.default_rng(42)


def make_real_pop(n: int, rng: np.random.Generator) -> list[Individual]:
    inds = []
    for i in range(n):
        g = RealGenome.random(5, rng=rng)
        g.fitness = float(i * 10)
        inds.append(Individual(genome=g, fitness=g.fitness))
    return inds


class TestSelection:
    def test_tournament_returns_correct_count(self, rng):
        pop = make_real_pop(20, rng)
        selected = tournament_selection(pop, 5, rng, k=3)
        assert len(selected) == 5

    def test_elite_returns_best(self, rng):
        pop = make_real_pop(10, rng)
        selected = elite_selection(pop, 3, rng)
        assert len(selected) == 3
        assert selected[0].fitness >= selected[1].fitness >= selected[2].fitness

    def test_roulette_returns_correct_count(self, rng):
        pop = make_real_pop(10, rng)
        selected = roulette_selection(pop, 5, rng)
        assert len(selected) == 5

    def test_rank_returns_correct_count(self, rng):
        pop = make_real_pop(10, rng)
        selected = rank_selection(pop, 5, rng)
        assert len(selected) == 5


class TestCrossover:
    def test_uniform_crossover_real(self, rng):
        p1 = RealGenome(genes=np.array([1.0, 2.0, 3.0]))
        p2 = RealGenome(genes=np.array([4.0, 5.0, 6.0]))
        c1, c2 = uniform_crossover(p1, p2, rng)
        assert len(c1.genes) == 3
        assert len(c2.genes) == 3

    def test_sbx_crossover_real(self, rng):
        p1 = RealGenome(genes=np.array([1.0, 2.0, 3.0]), bounds=[(-10, 10)] * 3)
        p2 = RealGenome(genes=np.array([4.0, 5.0, 6.0]), bounds=[(-10, 10)] * 3)
        c1, c2 = sbx_crossover(p1, p2, rng)
        assert len(c1.genes) == 3

    def test_sbx_crossover_produces_valid_children(self, rng):
        p1 = RealGenome(genes=np.array([0.0, 0.0, 0.0, 0.0, 0.0]), bounds=[(-5, 5)] * 5)
        p2 = RealGenome(genes=np.array([1.0, 1.0, 1.0, 1.0, 1.0]), bounds=[(-5, 5)] * 5)
        c1, c2 = sbx_crossover(p1, p2, rng, eta=2.0)
        assert len(c1.genes) == 5
        assert len(c2.genes) == 5
        assert all(-5 <= v <= 5 for v in c1.genes)
        assert all(-5 <= v <= 5 for v in c2.genes)

    def test_sbx_crossover_fallback_non_ndarray(self, rng):
        p1 = BinaryGenome(genes=np.array([True, False, True]))
        p2 = BinaryGenome(genes=np.array([False, True, False]))
        c1, c2 = sbx_crossover(p1, p2, rng)
        assert len(c1.genes) == 3

    def test_multi_point_crossover_real(self, rng):
        p1 = RealGenome(genes=np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]), bounds=[(-10, 10)] * 10)
        p2 = RealGenome(genes=np.array([9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0]), bounds=[(-10, 10)] * 10)
        c1, c2 = multi_point_crossover(p1, p2, rng, points=3)
        assert len(c1.genes) == 10
        assert len(c2.genes) == 10
        assert all(-10 <= v <= 10 for v in c1.genes)
        assert all(-10 <= v <= 10 for v in c2.genes)

    def test_multi_point_crossover_fallback_non_ndarray(self, rng):
        p1 = BinaryGenome(genes=np.array([True, False, True]))
        p2 = BinaryGenome(genes=np.array([False, True, False]))
        c1, c2 = multi_point_crossover(p1, p2, rng, points=1)
        assert len(c1.genes) == 3

    def test_single_point_binary(self, rng):
        p1 = BinaryGenome(genes=np.array([True] * 10))
        p2 = BinaryGenome(genes=np.array([False] * 10))
        c1, c2 = single_point_crossover(p1, p2, rng)
        assert len(c1.genes) == 10


class TestMutation:
    def test_gaussian_mutation_real(self, rng):
        g = RealGenome(genes=np.array([0.0, 0.0, 0.0]), bounds=[(-100, 100)] * 3)
        m = gaussian_mutation(g, 1.0, rng, sigma=0.5)
        assert not np.array_equal(m.genes, g.genes)

    def test_gaussian_mutation_respects_bounds(self, rng):
        g = RealGenome(genes=np.array([0.5, 0.5]), bounds=[(-1, 1), (-1, 1)])
        for _ in range(50):
            m = gaussian_mutation(g, 1.0, rng, sigma=5.0)
            assert all(-1 <= v <= 1 for v in m.genes)

    def test_bitflip_mutation(self, rng):
        g = BinaryGenome(genes=np.array([False] * 20))
        m = bitflip_mutation(g, 0.5, rng)
        assert any(m.genes)

    def test_uniform_mutation(self, rng):
        g = RealGenome(genes=np.array([0.0, 0.0, 0.0]), bounds=[(-1, 1)] * 3)
        m = uniform_mutation(g, 1.0, rng)
        assert all(-1 <= v <= 1 for v in m.genes)

    def test_polynomial_mutation(self, rng):
        g = RealGenome(genes=np.array([0.0, 0.0]), bounds=[(-1, 1), (-1, 1)])
        m = polynomial_mutation(g, 1.0, rng)
        assert all(-1 <= v <= 1 for v in m.genes)

    def test_mutation_rate_zero(self, rng):
        g = RealGenome(genes=np.array([1.0, 2.0, 3.0]))
        m = gaussian_mutation(g, 0.0, rng)
        assert np.array_equal(m.genes, g.genes)
