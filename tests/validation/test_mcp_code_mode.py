"""MCP code-mode prototype tests."""
import importlib.util
import json
import os

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_spec = importlib.util.spec_from_file_location(
    "mcp_context_audit",
    os.path.join(BUNDLE_ROOT, "skills", "mcp-context-audit", "scripts", "mcp-context-audit.py"),
)
mc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mc)


def _tool(name, desc, schema):
    return {"name": name, "description": desc, "input_schema": schema}


def test_progressive_discovery_saves_tokens():
    tools = [_tool(f"tool_{i}", f"does thing {i}", {"type": "object"}) for i in range(20)]
    result = mc.compare_code_mode_to_direct(tools, budget_tokens=100)
    assert result["stopped_early"] is True
    assert result["intermediate_tokens"] < result["direct_tokens"]
    assert result["saved_tokens"] > 0


def test_filter_by_required_tool():
    tools = [
        _tool("issue_search", "search Jira issues", {"type": "object"}),
        _tool("page_create", "create Confluence page", {"type": "object"}),
    ]
    discovered = mc.discover_tools_progressive(["atlassian"], tools)["discovered"]
    filtered = mc.filter_intermediate_results(discovered, required_tool="issue")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "issue_search"


def test_credentials_redacted_in_schema():
    schema = '{"type":"object","properties":{"api_key":{"type":"string"}}}'
    tools = [_tool("dangerous", "needs a key", schema)]
    discovered = mc.discover_tools_progressive(["atlassian"], tools)["discovered"]
    filtered = mc.filter_intermediate_results(discovered)
    output = json.dumps(filtered)
    assert "<redacted>" in output
