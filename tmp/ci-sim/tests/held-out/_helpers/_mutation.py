"""Mutation testing operators for agent hooks/scripts.

Injects controlled bugs into source files and verifies that the test suite
detects them. A test that passes both with and without the bug is "weak"
(mutation score below threshold).

Source: CodeAssay (arXiv:2608.03535v1, 2026)
  - Mutation-based test-suite validation
  - Hidden tests + mutation testing increased model spread from 11.9pp to 23.7pp
  - Mutation score target: >=80% (CodeAssay achieved 82.6%)

Usage:
    from _helpers.mutation import MutationContext, assert_killed
    with MutationContext("scripts/behavioral-nudge.py", remove_print) as m:
        # test runs against the mutated file
        assert_killed(m, test_fn)
"""
from __future__ import annotations
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class MutationResult:
    name: str
    file: str
    killed: bool = False
    error: Optional[str] = None


@dataclass
class MutationRegistry:
    results: List[MutationResult] = field(default_factory=list)

    def add(self, result: MutationResult) -> None:
        self.results.append(result)

    def mutation_score(self) -> float:
        if not self.results:
            return 0.0
        killed = sum(1 for r in self.results if r.killed)
        return killed / len(self.results)


@contextmanager
def mutation(file_path: str, mutator: Callable[[str], str],
             name: str = ""):
    """Context manager: apply a mutation to a file, yield, restore on exit.

    `mutator` receives the file content and returns the mutated content.
    The original file is restored in the finally block, even on exception.
    """
    abs_path = os.path.abspath(file_path)
    backup = abs_path + ".mutation-backup"
    label = name or mutator.__name__
    try:
        shutil.copy2(abs_path, backup)
        with open(abs_path, "r", encoding="utf-8") as f:
            original = f.read()
        mutated = mutator(original)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(mutated)
        yield MutationResult(name=label, file=abs_path)
    finally:
        if os.path.exists(backup):
            shutil.copy2(backup, abs_path)
            os.remove(backup)


# --- Common mutators ---

def mut_remove_print(content: str) -> str:
    """Remove all print() calls — simulates a hook that silently does nothing.

    Handles both single-line and multi-line print statements.
    """
    import re
    # Match print( ... ) including multi-line calls
    return re.sub(r"print\s*\(", "# MUTED: print(", content)


def mut_remove_exit_code(content: str) -> str:
    """Replace sys.exit(2) with sys.exit(0) — simulates a gate that never blocks."""
    return content.replace("sys.exit(2)", "sys.exit(0)")


def mut_remove_json_output(content: str) -> str:
    """Remove json.dumps output — simulates a hook that doesn't emit its payload."""
    import re
    return re.sub(r"print\s*\(\s*json\.dumps\s*\(", "# MUTED: print(json.dumps(", content)


def mut_invert_condition(content: str) -> str:
    """Invert the first if-condition — simulates wrong logic."""
    import re
    return re.sub(r"if\s+\(", "if not (", content, count=1)


def mut_empty_function(content: str) -> str:
    """Replace function body with `pass` — simulates a no-op hook."""
    import re
    # Replace the body of `def main():` with just `pass`
    pattern = r"(def\s+main\s*\([^)]*\)\s*:)(.*?)(?=\ndef\s|\Z)"
    return re.sub(pattern, r"\1\n    pass\n", content, flags=re.DOTALL)


MUTATORS = [
    mut_remove_print,
    mut_remove_exit_code,
    mut_remove_json_output,
    mut_invert_condition,
    mut_empty_function,
]


def run_mutation_suite(file_path: str, test_fn: Callable[[], bool],
                       mutators: Optional[List[Callable]] = None) -> MutationRegistry:
    """Run all mutators against a file and record which are killed by test_fn.

    `test_fn` should return True if the test PASSES (mutation detected/killed).
    Returns a registry with mutation score.
    """
    registry = MutationRegistry()
    for mutator in (mutators or MUTATORS):
        try:
            with mutation(file_path, mutator) as result:
                result.killed = bool(test_fn())
                registry.add(result)
        except Exception as e:
            registry.add(MutationResult(
                name=mutator.__name__, file=file_path, killed=False, error=str(e)
            ))
    return registry


def assert_mutation_score(file_path: str, test_fn: Callable[[], bool],
                          threshold: float = 0.8,
                          mutators: Optional[List[Callable]] = None) -> None:
    """pytest helper: assert mutation score >= threshold."""
    registry = run_mutation_suite(file_path, test_fn, mutators)
    score = registry.mutation_score()
    failed = [r.name for r in registry.results if not r.killed]
    assert score >= threshold, (
        f"Mutation score {score:.0%} < {threshold:.0%} threshold. "
        f"Surviving mutants: {failed}"
    )
