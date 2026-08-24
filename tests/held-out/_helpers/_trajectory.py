"""Trajectory analysis: verifies the agent used tools, not deduction.

ProcBench-style evaluation: the agent's execution trajectory is inspected,
not just the final output. An agent that produces a correct answer via
deduction (no tool calls) fails the trajectory check.

Source: ProcBench (arXiv:2605.20251v2, 2026)
  - 11 defect types in 4 categories: context management, tool-use efficiency,
    workflow architecture, tool-ecosystem consistency
  - Control preservation: interpretable, interruptible, correctable, reversible

Usage:
    from _helpers.trajectory import Trajectory, ToolCall
    traj = Trajectory([
        ToolCall("read", {"file_path": "/path"}),
        ToolCall("edit", {"file_path": "/path", "old_string": "...", "new_string": "..."}),
    ])
    assert traj.uses_tool_before("read", "edit")
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)

    def matches(self, name: str, arg_filter: Optional[Dict[str, Any]] = None) -> bool:
        if self.name != name:
            return False
        if arg_filter:
            for k, v in arg_filter.items():
                if self.args.get(k) != v:
                    return False
        return True


@dataclass
class Trajectory:
    calls: List[ToolCall] = field(default_factory=list)

    def uses_tool(self, name: str, arg_filter: Optional[Dict] = None) -> bool:
        return any(c.matches(name, arg_filter) for c in self.calls)

    def uses_any_tool(self, names: List[str]) -> bool:
        return any(self.uses_tool(n) for n in names)

    def tool_before(self, before: str, after: str,
                    after_arg_filter: Optional[Dict] = None) -> bool:
        """Check that a `before` tool call occurs before any `after` tool call."""
        before_idx = None
        for i, c in enumerate(self.calls):
            if c.name == before:
                before_idx = i
                break
        if before_idx is None:
            return False
        for c in self.calls[before_idx + 1:]:
            if c.matches(after, after_arg_filter):
                return True
        return False

    def uses_tool_before(self, before: str, after: str) -> bool:
        """Alias for tool_before with clearer semantics."""
        return self.tool_before(before, after)

    def has_deduction_only(self, verify_tools: List[str]) -> bool:
        """True if NO verify-tool was used (agent deduced instead of verifying)."""
        return not self.uses_any_tool(verify_tools)

    def first_call(self) -> Optional[ToolCall]:
        return self.calls[0] if self.calls else None

    def call_count(self, name: str) -> int:
        return sum(1 for c in self.calls if c.name == name)


def parse_trajectory(log: List[Dict]) -> Trajectory:
    """Parse a list of tool-call dicts into a Trajectory.

    Expected format: [{"name": "read", "args": {...}}, ...]
    """
    calls = []
    for entry in log:
        name = entry.get("name") or entry.get("tool_name") or ""
        args = entry.get("args") or entry.get("tool_input") or {}
        calls.append(ToolCall(name=name, args=args))
    return Trajectory(calls=calls)
