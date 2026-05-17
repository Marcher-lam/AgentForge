"""Tests for Fitness and Constraints — Task 2."""

import numpy as np
import pytest

from agentforge.evoforge.fitness.functions import (
    SimpleFitness,
    WeightedMultiObjective,
    BoundaryClip,
    PenaltyFunction,
)
from agentforge.evoforge.genomes.real import RealGenome


class TestSimpleFitness:
    def test_evaluate(self):
        fn = SimpleFitness(lambda g: float(np.sum(g.genes)))
        g1 = RealGenome(genes=np.array([1.0, 2.0, 3.0]))
        g2 = RealGenome(genes=np.array([4.0, 5.0]))
        scores = fn.evaluate([g1, g2])
        assert scores == [6.0, 9.0]


class TestWeightedMultiObjective:
    def test_two_objectives(self):
        obj1 = lambda g: float(np.sum(g.genes))
        obj2 = lambda g: float(-np.var(g.genes))
        fn = WeightedMultiObjective([obj1, obj2], weights=[1.0, 0.5])
        g = RealGenome(genes=np.array([1.0, 2.0, 3.0]))
        scores = fn.evaluate([g])
        assert len(scores) == 1
        # Weights are normalized to sum to 1.0: [1.0/1.5, 0.5/1.5]
        w1, w2 = 1.0 / 1.5, 0.5 / 1.5
        expected = w1 * 6.0 + w2 * (-np.var(np.array([1.0, 2.0, 3.0])))
        assert abs(scores[0] - expected) < 1e-10


class TestBoundaryClip:
    def test_clip_genes(self):
        clipper = BoundaryClip()
        g = RealGenome(genes=np.array([5.0, -3.0]), bounds=[(-1, 1), (-1, 1)])
        clipper.enforce(g)
        assert g.genes[0] == 1.0
        assert g.genes[1] == -1.0


class TestPenaltyFunction:
    def test_penalty_applied(self):
        constraint = lambda g: max(0, float(np.sum(g.genes)) - 5.0)
        penalty = PenaltyFunction(constraint, penalty_factor=10.0)
        g = RealGenome(genes=np.array([3.0, 3.0]))  # sum=6, violation=1
        p = penalty.apply(g)
        assert p == -10.0
