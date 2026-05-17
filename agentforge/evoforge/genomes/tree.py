"""TreeGenome — GP tree with ADF support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from numpy.random import Generator


@dataclass
class TreeNode:
    """AST node for genetic programming trees."""
    value: str | float
    children: list[TreeNode] = field(default_factory=list)

    def depth(self) -> int:
        """Return the maximum depth of this subtree."""
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)

    def copy(self) -> TreeNode:
        """Return a deep copy of this subtree."""
        return TreeNode(value=self.value, children=[c.copy() for c in self.children])

    def evaluate(self, context: dict[str, float] | None = None) -> float:
        """Evaluate the tree by recursively computing arithmetic operations."""
        context = context or {}
        if not self.children:
            if isinstance(self.value, str) and self.value in context:
                return context[self.value]
            return float(self.value)
        args = [c.evaluate(context) for c in self.children]
        op = self.value
        if op == "+":
            return args[0] + args[1]
        elif op == "-":
            return args[0] - args[1]
        elif op == "*":
            return args[0] * args[1]
        elif op == "/":
            return args[0] / args[1] if abs(args[1]) > 1e-10 else 0.0
        return 0.0


@dataclass
class TreeGenome:
    """GP tree genome with crossover, mutation, and random generation."""
    root: TreeNode
    max_depth: int = 10
    fitness: float | None = None

    def crossover(self, other: TreeGenome, rng: Generator) -> tuple[TreeGenome, TreeGenome]:
        """Return two offspring via subtree-swap crossover."""
        c1 = self.root.copy()
        c2 = other.root.copy()

        # Collect all nodes with their parent references for swapping
        nodes1 = _collect_nodes(c1)
        nodes2 = _collect_nodes(c2)

        if not nodes1 or not nodes2:
            return (
                TreeGenome(root=c1, max_depth=self.max_depth),
                TreeGenome(root=c2, max_depth=self.max_depth),
            )

        # Pick random nodes in each tree
        idx1 = rng.integers(0, len(nodes1))
        idx2 = rng.integers(0, len(nodes2))
        parent1, child_idx1, node1 = nodes1[idx1]
        parent2, child_idx2, node2 = nodes2[idx2]

        # Swap subtrees
        if parent1 is None:
            c1 = node2.copy()
        else:
            parent1.children[child_idx1] = node2.copy()

        if parent2 is None:
            c2 = node1.copy()
        else:
            parent2.children[child_idx2] = node1.copy()

        return (
            TreeGenome(root=c1, max_depth=self.max_depth),
            TreeGenome(root=c2, max_depth=self.max_depth),
        )

    def mutate(self, rate: float, rng: Generator) -> TreeGenome:
        """Subtree mutation — replace a random node with a new random subtree."""
        new_root = self.root.copy()
        if rng.random() < rate:
            nodes = _collect_nodes(new_root)
            if nodes:
                idx = rng.integers(0, len(nodes))
                parent, child_idx, node = nodes[idx]
                # Generate a new random subtree limited to remaining depth budget
                current_depth = _node_depth(new_root, node)
                remaining = max(1, self.max_depth - current_depth)
                variables = ["x", "y"]
                new_subtree = _random_subtree(variables, remaining, rng)
                if parent is None:
                    new_root = new_subtree
                else:
                    parent.children[child_idx] = new_subtree
        return TreeGenome(root=new_root, max_depth=self.max_depth)

    def clone(self) -> TreeGenome:
        """Return an independent deep copy."""
        return TreeGenome(root=self.root.copy(), max_depth=self.max_depth, fitness=self.fitness)

    @classmethod
    def random(cls, variables: list[str] | None = None, max_depth: int = 4, rng: Generator | None = None) -> TreeGenome:
        """Generate a random tree genome up to the given depth."""
        rng = rng or np.random.default_rng()  # type: ignore[name-defined]
        variables = variables or ["x", "y"]

        def build(depth: int) -> TreeNode:
            if depth >= max_depth or rng.random() < 0.3:
                val = rng.choice(variables + [rng.uniform(-1, 1)])
                return TreeNode(value=val)
            op = rng.choice(["+", "-", "*"])
            return TreeNode(value=op, children=[build(depth + 1), build(depth + 1)])

        return cls(root=build(0), max_depth=max_depth)


def _collect_nodes(root: TreeNode) -> list[tuple[TreeNode | None, int, TreeNode]]:
    """Collect all nodes as (parent, child_index, node) triples via BFS."""
    result: list[tuple[TreeNode | None, int, TreeNode]] = [(None, -1, root)]
    queue: list[tuple[TreeNode | None, int, TreeNode]] = [(None, -1, root)]
    while queue:
        parent, child_idx, node = queue.pop(0)
        for i, child in enumerate(node.children):
            entry = (node, i, child)
            result.append(entry)
            queue.append(entry)
    return result


def _node_depth(root: TreeNode, target: TreeNode) -> int:
    """Find the depth of a target node within the tree via BFS."""
    queue: list[tuple[TreeNode, int]] = [(root, 0)]
    while queue:
        node, depth = queue.pop(0)
        if node is target:
            return depth
        for child in node.children:
            queue.append((child, depth + 1))
    return 0


def _random_subtree(variables: list[str], max_depth: int, rng: Generator) -> TreeNode:
    """Generate a random subtree up to max_depth."""
    if max_depth <= 0 or rng.random() < 0.3:
        val = rng.choice(variables + [rng.uniform(-1, 1)])
        return TreeNode(value=val)
    op = rng.choice(["+", "-", "*"])
    return TreeNode(value=op, children=[
        _random_subtree(variables, max_depth - 1, rng),
        _random_subtree(variables, max_depth - 1, rng),
    ])
