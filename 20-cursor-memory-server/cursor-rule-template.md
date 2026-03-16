---
description: Memory system instructions for automatic context recall and saving
globs:
alwaysApply: true
---

# Memory System

You have access to a persistent memory system via MCP tools (server: "memory"). Use it to maintain context across conversations.

## On Conversation Start

Call `memory_get_context` at the beginning of every conversation to recall relevant memories. The `project_name` is automatically detected from the environment — you can omit it or pass the current project name.

## When to Save Memories (Automatic)

Proactively call `memory_add` when you observe any of the following during conversation:

- **Decisions**: User makes a technical decision (e.g., choosing a framework, database, architecture pattern)
- **Architecture**: System design choices, data flow decisions, API designs
- **Preferences**: User expresses preferences about coding style, tools, workflows, response language
- **Progress**: Milestones reached, features completed, major changes made
- **Bugs**: Important bugs discovered, root causes identified, workarounds found

Set `source: "auto"` for these automatic saves.

## When to Save Memories (Manual)

When the user explicitly says any of the following, save with `source: "manual"`:
- "记住这个" / "记住" / "remember this"
- "保存这个决定" / "save this"
- Any clear instruction to persist information

## When to Delete/Update Memories

- "忘掉这个" / "forget this" / "删除记忆" → call `memory_delete`
- "更新记忆" / "update memory" → call `memory_update`
- When a decision is reversed or superseded, update the old memory rather than creating a duplicate

## Scope Guidelines

- **global**: User preferences (language, style), universal coding standards, cross-project patterns
- **project**: Project-specific decisions, architecture, progress, bugs — this is the default

## Importance Guidelines

- **9-10**: Critical architecture decisions, core technology choices
- **7-8**: Important preferences, significant milestones, recurring patterns
- **5-6**: General notes, minor decisions (default)
- **3-4**: Temporary context, may become irrelevant
- **1-2**: Trivial observations

## Category Reference

| Category | Use For |
|----------|---------|
| decision | Technical decisions, tool/framework choices |
| architecture | System design, data models, API structure |
| preference | User preferences, coding style, workflow habits |
| progress | Milestones, completed features, project status |
| bug | Bugs, issues, workarounds, root causes |
| general | Anything that doesn't fit above categories |
