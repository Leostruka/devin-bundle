# Google Artemis MCP eval (Android automation)

status: resolved
priority: P3
source: reels batch-4 follow-up research (.devin/research/2026-11-06-reels-batch4-survey.md)

## Evidence
google/artemis (Apache-2.0, 16.7k stars, created 2026-08): MCP-native Android automation - natural language -> device workflows, 99%+ AndroidWorld (self-reported), no tagged releases (pin SHA). MCP tools: mobile_run_task/manage_task/get_device_state/inspect_trace/diagnose; Flash+Pro models, 3-5s/step observe-act loop.

## Task
Verdict: overlaps extensions/computer-use (cu_adb_backend exists for ADB). Artemis is MCP-server-shaped = would need mcp-governance review before adding an MCP to the bundle config. Record as eval; candidate when a real Android device target exists.

## Answer

Evaluated: Artemis = Apache-2.0 MCP server for Android automation. Overlaps cu_adb_backend; adoption would go through mcp-governance (new MCP). Recorded as candidate for when an Android target exists; pin-by-SHA (no tagged releases).
