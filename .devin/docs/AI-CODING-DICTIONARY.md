# AI Coding Dictionary

A plain-language dictionary of terms used in agentic AI coding. The goal is to compress each concept into a tight definition so the agent and the user share the same vocabulary.

## A

**Agent harness**  
The runtime environment that connects an LLM to tools, files, and network resources. Examples: Devin CLI, Claude Code, Codex CLI.  
_Avoid: "the AI", "the model" when you mean the full system._

**Agentic coding**  
Writing, editing, and debugging code by delegating steps to an autonomous or semi-autonomous agent rather than typing every change yourself.

## C

**Context engineering**  
The practice of structuring the information an agent sees — rules, memory, skill descriptions, retrieved docs — so the agent makes correct decisions.  
_Avoid: prompt stuffing, dumping files into the chat._

**Context window**  
The maximum amount of text (tokens) a model can process in a single pass. Current coding agents typically operate between 200K and 1M tokens.

## H

**Harness engineering**  
Building or configuring the scaffold that runs the agent: hooks, skills, MCP servers, subagent profiles, and lifecycle rules.  
_Avoid: calling it "prompt engineering" — harness engineering is about the system, not a single prompt._

## L

**Lost in the middle**  
The observed tendency of LLMs to ignore or misweight information in the middle of long contexts. Mitigated by constraint pinning, skill frontmatter, and selective retrieval.

## M

**MCP server**  
A Model Context Protocol server that exposes tools or data sources to an agent through a standardized interface, e.g., Jira, databases, search.

## P

**Prompt engineering**  
Crafting the wording of a single prompt or instruction to improve a model's output. It is one technique inside the larger discipline of context and harness engineering.  
_Avoid: using it as a catch-all for every agent configuration problem._

## S

**Skill**  
A markdown file in a known location that tells the agent when and how to use a particular workflow. Loaded by name, name-matched to tasks.

**Subagent**  
A fresh agent instance dispatched for a scoped task, often with a specialized profile (architect, debugger, implementer, researcher, reviewer).

**System prompt**  
The base instructions injected into every model interaction. In Devin CLI this is shaped by rules (`AGENTS.md`, `.devin/global_rules.md`) and skills.

## T

**Tool call**  
A structured request from the model to use a defined capability (read, exec, grep, web_search, mcp_call_tool, etc.). The model decides which tool and arguments.

**Tool-use nativo**  
A model's built-in ability to emit tool calls without external parsing or conversion. Required for reliable agentic coding.
