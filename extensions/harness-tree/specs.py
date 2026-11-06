#!/usr/bin/env python3
"""specs.py - SurfaceSpec mapping harness components c1..c8 to bundle paths.

Omitted-is-inherited: a diff only lists paths that change; anything absent
from a diff keeps the base value.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SurfaceSpec:
    name: str
    components: dict
    exclude_names: tuple = ("__pycache__", ".venv", "venv", "node_modules",
                            ".git", "target", ".backups")


DEVIN = SurfaceSpec(name="devin", components={
    "c1_system_prompt": ["AGENTS.md", ".devin/global_rules.md"],
    "c2_guardrails":    [".devin/rules", "hooks.v1.json"],
    "c3_memory":        [".devin/memory"],
    "c4_tool_guidance": ["skills/skill-discovery", "skills/ask-bundle",
                         ".devin/docs/SKILL-TIERS.md"],
    "c5_subagents":     [".devin/agents"],
    "c6_skills":        ["skills"],
    "c7_scripts":       ["scripts"],
    "c8_plugins":       ["mcp_config.json", "manifest.json"],
})


def component_of(spec, relpath):
    """Component id owning relpath, or None if outside spec."""
    relpath = relpath.replace("\\", "/")
    for cid, paths in spec.components.items():
        for p in paths:
            p = p.replace("\\", "/").rstrip("/")
            if relpath == p or relpath.startswith(p + "/"):
                return cid
    return None


def skipped(relpath, spec):
    parts = relpath.replace("\\", "/").split("/")
    return any(part in spec.exclude_names for part in parts)
