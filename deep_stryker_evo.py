#!/usr/bin/env python3
"""Deep Stryker for evolution-engine."""
import ast, subprocess, sys
from pathlib import Path
from deep_stryker import Mutator, MutantResult, find_mutable_lines, run_tests

ROOT = Path("/Users/marcher/Desktop/STDD-TEST")

targets = [
    ("agentforge/evoforge/engine/evolution.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/engine/population.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/engine/termination.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/engine/callbacks.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/fitness/functions.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/genomes/real.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/genomes/binary.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/genomes/tree.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/operators/selection.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/operators/crossover.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
    ("agentforge/evoforge/operators/mutation.py", "tests/unit/evoforge/ tests/integration/test_evoforge_integration.py"),
]

def apply_mutation(source, target_line):
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

def mutate_file(source_file, test_file, max_mutants=50):
    full_path = ROOT / source_file
    source = full_path.read_text()
    lines = find_mutable_lines(source)
    results = []
    for line_no in lines:
        if len(results) >= max_mutants:
            break
        mutated = apply_mutation(source, line_no)
        if mutated is None:
            continue
        full_path.write_text(mutated)
        try:
            survived = run_tests(test_file)
        except subprocess.TimeoutExpired:
            survived = False
        full_path.write_text(source)
        line_text = source.split('\n')[line_no - 1].strip() if line_no <= len(source.split('\n')) else ''
        if any(op in line_text for op in ['+', '-', '*', '/', '%']):
            op = "AOR"
        elif any(op in line_text for op in ['==', '!=', '<', '>', '<=', '>=']):
            op = "ROR"
        elif 'and' in line_text or 'or' in line_text:
            op = "LCR"
        elif 'return' in line_text:
            op = "SDL"
        else:
            op = "UOI"
        results.append(MutantResult(file=source_file, line=line_no, operator=op, description=line_text[:80], killed=not survived))
    return results

def main():
    all_results = []
    print("=" * 70)
    print("DEEP STRYKER — evolution-engine")
    print("=" * 70)
    for src, tst in targets:
        print(f"\n>> Mutating: {src}")
        results = mutate_file(src, tst)
        all_results.extend(results)
        k = sum(1 for r in results if r.killed)
        t = len(results)
        print(f"   {k}/{t} killed ({100*k//t if t else 0}%)")

    print("\n" + "=" * 70)
    print("MUTATION REPORT")
    print("=" * 70)
    killed = sum(1 for r in all_results if r.killed)
    total = len(all_results)
    survived = [r for r in all_results if not r.killed]

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
