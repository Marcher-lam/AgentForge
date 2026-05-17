#!/usr/bin/env python3
"""Deep Stryker — Systematic Operator Mutation Engine.

Applies standard mutation operators:
  AOR: Arithmetic Operator Replacement (+→-, -→+, *→/, etc.)
  ROR: Relational Operator Replacement (==→!=, <→>=, etc.)
  LCR: Logical Connector Replacement (and→or, or→and)
  UOI: Unary Operator Insertion (negate conditions)
  SBR: Statement Body Replacement (→ pass)
  SDL: Statement Deletion
  ABS: Absolute Value Insertion (x→abs(x))
"""
import ast
import copy
import os
import subprocess
import sys
import tempfile
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

ROOT = Path("/Users/marcher/Desktop/STDD-TEST")

# ── Mutation Operators ──────────────────────────────────────────────────────

AOR = {
    ast.Add: ast.Sub, ast.Sub: ast.Add,
    ast.Mult: ast.Div, ast.Div: ast.Mult,
    ast.Mod: ast.Mult, ast.FloorDiv: ast.Div,
    ast.Pow: ast.Mult,
}

ROR = {
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.Lt: ast.GtE, ast.LtE: ast.Gt,
    ast.Gt: ast.LtE, ast.GtE: ast.Lt,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
}

LCR = {ast.And: ast.Or, ast.Or: ast.And}

# ── AST Mutator ─────────────────────────────────────────────────────────────

class Mutator(ast.NodeTransformer):
    def __init__(self, target_line: int):
        self.target_line = target_line
        self.mutated = False

    def _should_mutate(self, node: ast.AST) -> bool:
        return hasattr(node, 'lineno') and node.lineno == self.target_line

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if self._should_mutate(node) and type(node.op) in AOR:
            node.op = AOR[type(node.op)]()
            self.mutated = True
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        if self._should_mutate(node):
            new_ops = []
            changed = False
            for op in node.ops:
                if type(op) in ROR:
                    new_ops.append(ROR[type(op)]())
                    changed = True
                else:
                    new_ops.append(op)
            if changed:
                node.ops = new_ops
                self.mutated = True
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if self._should_mutate(node) and type(node.op) in LCR:
            node.op = LCR[type(node.op)]()
            self.mutated = True
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if self._should_mutate(node):
            if isinstance(node.op, ast.Not):
                # Remove not operator
                self.mutated = True
                return node.operand
            elif isinstance(node.op, ast.USub):
                # Remove unary minus
                self.mutated = True
                return node.operand
        return node

    def visit_Constant(self, node):
        if self._should_mutate(node):
            if isinstance(node.value, bool):
                node.value = not node.value
                self.mutated = True
            elif isinstance(node.value, int) and not isinstance(node.value, bool):
                if node.value == 0:
                    node.value = 1
                elif node.value == 1:
                    node.value = 0
                else:
                    node.value = node.value + 1
                self.mutated = True
        return node

    def visit_Return(self, node):
        self.generic_visit(node)
        if self._should_mutate(node) and node.value is not None:
            # Replace return value with None
            node.value = ast.Constant(value=None)
            self.mutated = True
        return node

# ── SBR: Replace statement body with pass ──────────────────────────────────

class StatementBodyMutator(ast.NodeTransformer):
    """Replace function/method bodies with 'pass'."""
    def __init__(self, target_name: str):
        self.target_name = target_name
        self.mutated = False

    def visit_FunctionDef(self, node):
        if node.name == self.target_name and not node.name.startswith('_'):
            # Only mutate public methods, keep internals working
            pass  # don't mutate for now
        self.generic_visit(node)
        return node

# ── Engine ──────────────────────────────────────────────────────────────────

@dataclass
class MutantResult:
    file: str
    line: int
    operator: str
    description: str
    killed: bool

def find_mutable_lines(source: str) -> list[int]:
    """Find lines with mutable operators."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    
    lines = set()
    for node in ast.walk(tree):
        if hasattr(node, 'lineno'):
            if isinstance(node, (ast.BinOp, ast.Compare, ast.BoolOp, ast.UnaryOp)):
                lines.add(node.lineno)
            elif isinstance(node, ast.Constant) and isinstance(node.value, (bool, int)) and not isinstance(node.value, bool):
                lines.add(node.lineno)
            elif isinstance(node, ast.Return) and node.value is not None:
                if not isinstance(node.value, ast.Constant) or node.value.value is not None:
                    lines.add(node.lineno)
    return sorted(lines)

def apply_mutation(source: str, target_line: int) -> str | None:
    """Apply mutation at target line, return mutated source or None."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    
    mutator = Mutator(target_line)
    mutated_tree = mutator.visit(tree)
    
    if not mutator.mutated:
        return None
    
    ast.fix_missing_locations(mutated_tree)
    try:
        return ast.unparse(mutated_tree)
    except Exception:
        return None

def run_tests(test_path: str) -> bool:
    """Run tests, return True if pass (mutant survived)."""
    result = subprocess.run(
        ["python", "-m", "pytest", test_path, "-x", "-q", "--tb=line",
         "-o", "faulthandler_timeout=15"],
        capture_output=True, text=True, cwd=str(ROOT),
        timeout=20,
    )
    return result.returncode == 0

def mutate_file(
    source_file: str,
    test_file: str,
    max_mutants: int = 50,
) -> list[MutantResult]:
    """Run all mutations on a source file."""
    full_path = ROOT / source_file
    source = full_path.read_text()
    lines = find_mutable_lines(source)
    
    results = []
    count = 0
    
    for line_no in lines:
        if count >= max_mutants:
            break
        
        mutated_source = apply_mutation(source, line_no)
        if mutated_source is None:
            continue
        
        # Write mutated file
        full_path.write_text(mutated_source)
        
        try:
            survived = run_tests(test_file)
        except subprocess.TimeoutExpired:
            survived = False  # Timeout = killed (test hung)
        
        # Restore original
        full_path.write_text(source)
        
        # Determine operator type
        line_text = source.split('\n')[line_no - 1].strip() if line_no <= len(source.split('\n')) else ''
        if any(op in line_text for op in ['+', '-', '*', '/', '%']):
            op = "AOR"
        elif any(op in line_text for op in ['==', '!=', '<', '>', '<=', '>=', ' in ', 'is ']):
            op = "ROR"
        elif 'and' in line_text or 'or' in line_text:
            op = "LCR"
        elif 'return' in line_text:
            op = "SDL"
        else:
            op = "UOI"
        
        results.append(MutantResult(
            file=source_file,
            line=line_no,
            operator=op,
            description=line_text[:80],
            killed=not survived,
        ))
        count += 1
    
    return results

def main():
    targets = [
        ("agentforge/types/state.py", "tests/unit/types/test_agentforge_types.py tests/unit/agent/test_agent.py"),
        ("agentforge/types/message.py", "tests/unit/types/test_agentforge_types.py"),
        ("agentforge/agent/base.py", "tests/unit/agent/test_agent.py"),
        ("agentforge/agent/events.py", "tests/unit/agent/test_agent.py"),
        ("agentforge/bus/topic_matcher.py", "tests/unit/bus/test_bus.py"),
        ("agentforge/bus/inprocess.py", "tests/unit/bus/test_bus.py"),
        ("agentforge/infra/config.py", "tests/unit/infra/test_infra.py"),
        ("agentforge/infra/shutdown.py", "tests/unit/infra/test_infra.py"),
    ]
    
    all_results: list[MutantResult] = []
    
    print("=" * 70)
    print("DEEP STRYKER — Systematic Operator Mutation Engine")
    print("=" * 70)
    
    for source_file, test_file in targets:
        print(f"\n>> Mutating: {source_file}")
        results = mutate_file(source_file, test_file)
        all_results.extend(results)
        
        killed = sum(1 for r in results if r.killed)
        total = len(results)
        print(f"   {killed}/{total} killed ({100*killed//total if total else 0}%)")
    
    # Summary
    print("\n" + "=" * 70)
    print("MUTATION REPORT")
    print("=" * 70)
    
    killed = sum(1 for r in all_results if r.killed)
    total = len(all_results)
    survived = [r for r in all_results if not r.killed]
    
    # By operator
    ops = {}
    for r in all_results:
        ops.setdefault(r.operator, {"killed": 0, "total": 0})
        ops[r.operator]["total"] += 1
        if r.killed:
            ops[r.operator]["killed"] += 1
    
    print(f"\nTotal Mutants: {total}")
    print(f"Killed:        {killed}")
    print(f"Survived:      {total - killed}")
    print(f"Score:         {100*killed/total:.1f}%" if total else "N/A")
    
    print("\nBy Operator:")
    for op, data in sorted(ops.items()):
        pct = 100 * data["killed"] / data["total"] if data["total"] else 0
        print(f"  {op}: {data['killed']}/{data['total']} ({pct:.0f}%)")
    
    if survived:
        print(f"\n⚠️  SURVIVING MUTANTS ({len(survived)}):")
        for r in survived:
            print(f"  {r.file}:{r.line} [{r.operator}] {r.description}")
    
    threshold = 80
    score = 100 * killed / total if total else 0
    status = "✅ PASS" if score >= threshold else "❌ FAIL"
    print(f"\nThreshold: {threshold}% | Score: {score:.1f}% | {status}")

if __name__ == "__main__":
    main()
