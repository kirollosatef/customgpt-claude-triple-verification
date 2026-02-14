# Python Port — Why and How

## Context

This repo was originally built as a **Claude Code CLI plugin**. The hooks work by registering shell commands in `hooks/hooks.json` that Claude Code calls at lifecycle events (`PreToolUse`, `PostToolUse`, `Stop`). Each script reads a JSON blob from stdin and writes an approve/block decision to stdout.

The question was: can this plugin be used inside a **Python agent built with the Claude Agent SDK**?

## The Answer: Yes — but not by running the JS

The Claude Agent SDK (Python) has the same hook types — `PreToolUse`, `PostToolUse`, `Stop` — but instead of shell commands, hooks are **async Python callbacks** registered in `ClaudeAgentOptions`. There is no stdin/stdout protocol; you return a dict.

Three approaches were considered:

### Option 1: Subprocess adapter
Wrap the existing Node scripts in Python callbacks that spawn `node pre-tool-gate.mjs` as a subprocess, pipe `input_data` as JSON to stdin, read stdout, and translate the response format.

**Rejected.** Every tool call incurs a process spawn. Debugging crosses a language boundary. Node.js becomes a runtime dependency of the Python project. The response format (`{ decision: "block" }`) differs from the SDK format (`{ hookSpecificOutput: { permissionDecision: "deny" } }`), requiring a translation layer anyway.

### Option 2: Use MCP server layer
The SDK treats custom tools as MCP servers. Could the JS hooks be attached at the MCP level instead?

**Rejected.** Built-in tools (`Write`, `Edit`, `Bash`) are native SDK tools, not MCP tools — they don't pass through MCP at all. And even for custom MCP tools, there is no hook injection point at the MCP transport layer; hooks are only available via the SDK's own callback system.

### Option 3: Port the logic to Python ✓
The JS is almost entirely scaffolding (stdin/stdout plumbing). The actual value is the **rules** — regex patterns and violation messages. Those are pure data, trivially translatable to Python.

**Chosen.** Result: `quadruple_verification.py` — a single-file Python module with zero dependencies beyond the standard library.

---

## What was ported

| JS file | Ported to | Notes |
|---|---|---|
| `scripts/lib/rules-engine.mjs` | `quadruple_verification.py` | `_CYCLE1_RULES`, `_CYCLE2_RULES`, `_run_cycle1()`, `_run_cycle2()` |
| `scripts/lib/research-verifier.mjs` | `quadruple_verification.py` | `_run_cycle4()`, claim/source/vague patterns |
| `scripts/lib/audit-logger.mjs` | `quadruple_verification.py` | `_log_entry()` using `pathlib` + `json` |
| `scripts/lib/config-loader.mjs` | `quadruple_verification.py` | `_load_config()`, `_deep_merge()`, `_load_json_file()` |
| `scripts/pre-tool-gate.mjs` | `_make_pre_tool_hook()` | Returns async callback instead of writing to stdout |
| `scripts/post-tool-audit.mjs` | `_make_post_tool_hook()` | Returns async callback |
| `scripts/stop-gate.mjs` | `_make_stop_hook()` | Returns async callback; Stop hook also injects Cycle 3 prompt via `systemMessage` |
| `hooks/hooks.json` (Stop prompt) | `CYCLE3_SYSTEM_MESSAGE` | Constant string, injected as `systemMessage` from Stop hook |

### What disappeared

- `scripts/lib/utils.mjs` — stdin/stdout helpers, `failOpen()`, `findProjectRoot()`. None of these are needed; the SDK handles the protocol, and `pathlib.Path` handles filesystem traversal.
- `install/` scripts — not applicable to a library module.
- `hooks/hooks.json` — replaced by `make_hooks()` which returns the equivalent Python dict.

---

## What changed behaviorally

### Response format
JS scripts output `{ "decision": "block", "reason": "..." }` to stdout.
Python callbacks return `{ "hookSpecificOutput": { "permissionDecision": "deny", "permissionDecisionReason": "..." } }`.

### Fail-open
JS used a `failOpen()` wrapper that caught all errors and wrote `{ decision: "approve" }` to stdout before `process.exit(0)`.
Python uses a `try/except` in each callback that logs to stderr and returns `{}` (approve) on any unhandled exception. Same semantics.

### Session ID
JS read `process.env.CLAUDE_SESSION_ID` or fell back to `session-{Date.now()}`.
Python reads `os.environ.get("CLAUDE_SESSION_ID")` or falls back to `session-{int(timestamp * 1000)}`. Identical.

### Config loading
Three-layer merge is preserved: plugin defaults → `~/.claude/quadruple-verify-config.json` → `$PROJECT/.claude/quadruple-verify-config.json`. The `plugin_root` argument to `make_hooks()` is optional; if omitted, only user/project configs are loaded (since the JS repo's `config/default-rules.json` may not be present in a Python-only project).

### MCP tool context
All `mcp__*` tools land in `"mcp"` context. Rules scoped to `"file-write"` or `"bash"` do **not** fire for MCP tool inputs. This is identical to the original JS behaviour and is intentional — MCP tools are treated as opaque inputs, not as file writes or shell commands.

---

## Integration into customgpt-manus-agent

The agent (`src/claude_agent/agent.py`) registers hooks in `_build_hooks()`. The quadruple verification hooks are appended there:

```python
from ..quality.quadruple_verification import (
    _load_config, _make_pre_tool_hook, _make_post_tool_hook,
    _make_stop_hook, CYCLE3_SYSTEM_MESSAGE,
)

def _build_hooks(self, hook_state):
    # ... existing hooks ...
    qv_config = _load_config()
    return {
        "PreToolUse": [
            # ... existing matchers ...
            HookMatcher(matcher="mcp__.*", hooks=[_make_pre_tool_hook(qv_config)]),
        ],
        "PostToolUse": [
            # ... existing matchers ...
            HookMatcher(hooks=[_make_post_tool_hook(qv_config)]),
        ],
        "Stop": [
            HookMatcher(hooks=[qv_stop]),  # Cycle 4 + Cycle 3 system message
        ],
    }
```

The `mcp__.*` matcher ensures verification only fires for the agent's custom MCP tools, not SDK built-ins.

---

## Running the tests

```bash
# From the repo root
python3 -m unittest tests/test_python_port.py -v

# If pytest is available
pytest tests/test_python_port.py -v
```

The Python test suite (`tests/test_python_port.py`) mirrors the existing JS tests (`test-cycle1.mjs`, `test-cycle2.mjs`, `test-cycle4.mjs`, `test-audit.mjs`, `test-config.mjs`) and uses the same fixture files from `tests/fixtures/`. Both suites should pass for any change to the rules.

---

## Configuring rules

Create a JSON file at either location to override defaults:

```
~/.claude/quadruple-verify-config.json          # user-wide
<project>/.claude/quadruple-verify-config.json  # project-specific (wins)
```

Example — disable TODOs check and Cycle 4 entirely:

```json
{
    "disabledRules": ["no-todo"],
    "cycle4": { "enabled": false }
}
```

All options from the original `config/default-rules.json` are supported.
