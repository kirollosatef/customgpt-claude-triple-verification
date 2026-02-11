# Hooks

The plugin integrates with Claude Code through its **hook system**. Hooks are defined in `hooks/hooks.json` and specify when and how the verification scripts run.

## Hook Events

Claude Code provides three hook events:

| Event | When | Type | Can Block? |
|-------|------|------|-----------|
| **PreToolUse** | Before a tool call executes | Command | Yes |
| **PostToolUse** | After a tool call completes | Command | No |
| **Stop** | Before Claude finishes responding | Prompt | Yes |

## Hook Configuration

Hooks are defined in `hooks/hooks.json` using an event-keyed structure:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/scripts/pre-tool-gate.mjs\"",
            "timeout": 10000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/scripts/post-tool-audit.mjs\"",
            "timeout": 5000
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "..."
          }
        ]
      }
    ]
  }
}
```

## Key Concepts

### Matchers

The `matcher` field is a regex pattern that determines which tool calls trigger the hook:

| Matcher | Matches |
|---------|---------|
| `Write\|Edit` | Only Write and Edit tool calls |
| `Write\|Edit\|Bash\|.*MCP.*\|WebFetch\|WebSearch` | File, bash, MCP, and web tools |
| `.*` | All tool calls |
| `""` (empty) | Used for Stop hooks (no tool to match) |

### Hook Types

**Command hooks** run an external script and read its stdout for a decision:
- Exit 0 with `{"decision": "approve"}` → operation proceeds
- Exit 0 with `{"decision": "block", "reason": "..."}` → operation rejected
- Any error → operation proceeds (fail-open)

**Prompt hooks** inject text into Claude's context:
- Used for Cycle 3 (output quality review)
- The prompt asks Claude to self-verify before completing

### `${CLAUDE_PLUGIN_ROOT}`

This variable is resolved by Claude Code to the plugin's actual installation directory. It ensures scripts are found regardless of where the plugin was installed.

### Timeouts

Each hook has a `timeout` field (in milliseconds). If the script doesn't complete within the timeout:
- The operation proceeds (fail-open)
- A warning is logged to stderr

Default timeouts:
- **PreToolUse hooks:** 10,000ms (10 seconds)
- **PostToolUse hooks:** 5,000ms (5 seconds)

## How the Plugin Uses Hooks

| Hook | Event | Matcher | Script | Purpose |
|------|-------|---------|--------|---------|
| Code Quality | PreToolUse | `Write\|Edit` | `pre-tool-gate.mjs` | Cycle 1 rules |
| Security | PreToolUse | `Write\|Edit\|Bash\|.*MCP.*\|WebFetch\|WebSearch` | `pre-tool-gate.mjs` | Cycle 2 rules |
| Research | PreToolUse | `Write\|Edit` | `pre-tool-gate.mjs` | Cycle 4 rules |
| Output QA | Stop | (all) | Prompt injection | Cycle 3 review |
| Research Scan | Stop | (all) | `stop-gate.mjs` | Cycle 4 end-of-session |
| Audit Logger | PostToolUse | `.*` | `post-tool-audit.mjs` | JSONL logging |

> **Note:** The `pre-tool-gate.mjs` script is a single dispatcher that routes to the appropriate cycle based on the tool being used and the file being written. This "one dispatcher per event" design avoids hook ordering issues.
