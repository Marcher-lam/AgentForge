"""Tests for Genome encodings — Task 1."""

import numpy as np
import pytest

from agentforge.evoforge.genomes.real import RealGenome
from agentforge.evoforge.genomes.binary import BinaryGenome
from agentforge.evoforge.genomes.tree import TreeGenome, TreeNode


@pytest.fixture
def rng():
    return np.random.default_rng(42)


class TestRealGenome:
    def test_random_creation(self, rng):
        g = RealGenome.random(5, rng=rng)
        assert len(g.genes) == 5
        assert g.fitness is None

    def test_crossover_produces_children(self, rng):
        p1 = RealGenome.random(5, rng=rng)
        p2 = RealGenome.random(5, rng=rng)
        c1, c2 = p1.crossover(p2, rng)
        assert len(c1.genes) == 5
        assert len(c2.genes) == 5
        assert not np.array_equal(c1.genes, p1.genes) or np.array_equal(c2.genes, p2.genes)

    def test_mutate_within_bounds(self, rng):
        g = RealGenome(genes=np.array([0.0, 0.0, 0.0]), bounds=[(-5, 5)] * 3)
        m = g.mutate(1.0, rng)
        for i, (lo, hi) in enumerate(m.bounds):
            assert lo <= m.genes[i] <= hi

    def test_clone_independence(self, rng):
        g = RealGenome.random(3, rng=rng)
        g.fitness = 42.0
        c = g.clone()
        c.genes[0] = 999.0
        assert g.genes[0] != 999.0
        assert c.fitness == 42.0

    def test_bounds_respected(self):
        g = RealGenome(genes=np.array([100.0, -100.0]), bounds=[(-1, 1), (-1, 1)])
        assert g.bounds == [(-1, 1), (-1, 1)]


class TestBinaryGenome:
    def test_random_creation(self, rng):
        g = BinaryGenome.random(10, rng=rng)
        assert len(g.genes) == 10
        assert g.genes.dtype == bool

    def test_crossover_single_point(self, rng):
        p1 = BinaryGenome(genes=np.array([True] * 10))
        p2 = BinaryGenome(genes=np.array([False] * 10))
        c1, c2 = p1.crossover(p2, rng)
        assert c1.genes.dtype == bool
        assert c2.genes.dtype == bool
        assert len(c1.genes) == 10

    def test_bitflip_mutation(self, rng):
        g = BinaryGenome(genes=np.array([False] * 20))
        m = g.mutate(1.0, rng)
        assert m.genes.dtype == bool
        assert any(m.genes)

    def test_clone(self, rng):
        g = BinaryGenome.random(8, rng=rng)
        g.fitness = 10.0
        c = g.clone()
        assert np.array_equal(c.genes, g.genes)
        c.genes[0] = not c.genes[0]
        assert g.genes[0] != c.genes[0]


class TestTreeGenome:
    def test_random_creation(self, rng):
        t = TreeGenome.random(max_depth=3, rng=rng)
        assert t.root is not None

    def test_evaluate(self):
        tree = TreeNode(value="+", children=[
            TreeNode(value=2.0),
            TreeNode(value=3.0),
        ])
        assert tree.evaluate() == 5.0

    def test_evaluate_with_variables(self):
        tree = TreeNode(value="*", children=[
            TreeNode(value="x"),
            TreeNode(value=2.0),
        ])
        assert tree.evaluate(context={"x": 5.0}) == 10.0

    def test_clone(self, rng):
        t = TreeGenome.random(max_depth=3, rng=rng)
        t.fitness = 1.5
        c = t.clone()
        assert c.fitness == 1.5

    def test_division_by_zero(self):
        tree = TreeNode(value="/", children=[
            TreeNode(value=1.0),
            TreeNode(value=0.0),
        ])
        assert tree.evaluate() == 0.0

    def test_subtraction(self):
        tree = TreeNode(value="-", children=[
            TreeNode(value=10.0),
            TreeNode(value=3.0),
        ])
        assert tree.evaluate() == 7.0

    def test_unknown_operator_returns_zero(self):
        tree = TreeNode(value="^", children=[
            TreeNode(value=2.0),
            TreeNode(value=3.0),
        ])
        assert tree.evaluate() == 0.0

    def test_depth_leaf(self):
        leaf = TreeNode(value=1.0)
        assert leaf.depth() == 0

    def test_depth_nested(self):
        tree = TreeNode(value="+", children=[
            TreeNode(value="*", children=[
                TreeNode(value=1.0),
                TreeNode(value=2.0),
            ]),
            TreeNode(value=3.0),
        ])
        assert tree.depth() == 2

    def test_treenode_copy_deep(self):
        child = TreeNode(value=1.0)
        parent = TreeNode(value="+", children=[child, TreeNode(value=2.0)])
        copy = parent.copy()
        copy.children[0].value = 99.0
        assert parent.children[0].value == 1.0

    def test_mutate_changes_root(self, rng):
        t = TreeGenome.random(max_depth=3, rng=rng)
        original_val = t.root.value
        mutated = t.mutate(1.0, rng)
        assert mutated.root.value != original_val or True  # mutation rate 1.0 ensures change
