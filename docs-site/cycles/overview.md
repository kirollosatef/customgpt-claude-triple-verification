# Verification Cycles Overview

The plugin runs four verification cycles on every Claude Code operation. Each cycle targets a different class of issues, and together they provide comprehensive coverage.

## The Four Cycles

```
User Request → Claude generates code
                    ↓
              ┌─────────────┐
              │  Cycle 1    │  PreToolUse (Write|Edit)
              │  Quality    │  Blocks placeholder/TODO code
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │  Cycle 2    │  PreToolUse (Write|Edit|Bash|MCP)
              │  Security   │  Blocks eval, secrets, injection
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │  Cycle 3    │  Stop (prompt hook)
              │  Output QA  │  Second AI reviews final output
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │  Cycle 4    │  PreToolUse (Write|Edit) + Stop
              │  Research   │  Blocks vague claims, missing sources
              └──────┬──────┘
                     ↓
              ┌─────────────┐
              │  Audit      │  PostToolUse (all tools)
              │  Logger     │  JSONL trail of every operation
              └─────────────┘
```

## Cycle Summary

| Cycle | Name | Hook Event | Can Block? | Rules |
|-------|------|-----------|------------|-------|
| **1** | [Code Quality](cycles/cycle-1.md) | PreToolUse | Yes | 6 rules |
| **2** | [Security](cycles/cycle-2.md) | PreToolUse | Yes | 11 rules |
| **3** | [Output Quality](cycles/cycle-3.md) | Stop | Yes (prompt) | AI review |
| **4** | [Research Claims](cycles/cycle-4.md) | PreToolUse + Stop | Yes | 3 rules |

## How Blocking Works

Cycles 1, 2, and 4 use **command hooks** — they execute a Node.js script that reads the tool input from stdin, runs pattern matching, and outputs a JSON decision:

- **Approve**: `{"decision": "approve"}` — operation proceeds
- **Block**: `{"decision": "block", "reason": "..."}` — operation is rejected with explanation

Cycle 3 uses a **prompt hook** — it injects a review prompt that asks Claude to self-verify before completing its response.

## When Each Cycle Runs

| Tool Being Used | Cycle 1 | Cycle 2 | Cycle 3 | Cycle 4 |
|----------------|---------|---------|---------|---------|
| Write | :white_check_mark: | :white_check_mark: | | :white_check_mark:* |
| Edit | :white_check_mark: | :white_check_mark: | | :white_check_mark:* |
| Bash | | :white_check_mark: | | |
| MCP tools | | :white_check_mark: | | |
| WebFetch/WebSearch | | :white_check_mark: | | |
| Stop (response end) | | | :white_check_mark: | :white_check_mark: |

*\* Cycle 4 only applies to research `.md` files*

## Fail-Open Design

All cycles are designed to **fail open**: if a verifier script crashes or times out, the operation proceeds normally. The plugin must never break Claude Code. Errors are logged to stderr but never block operations.

## Performance

The command hooks (Cycles 1, 2, 4) typically add **<50ms** per operation. The prompt hook (Cycle 3) adds some latency because it triggers an additional AI review pass.
