# Audit Trail

Every operation that passes through the plugin is logged to a JSONL audit trail for full traceability.

## How It Works

The audit logger runs as a **PostToolUse** hook — after every tool call completes, it appends a structured JSON entry to a log file. The logger is non-blocking: it never prevents operations from completing, even if logging fails.

## Log Location

Audit logs are stored in:

```
.claude/quadruple-verify-audit/
```

Each session creates a separate JSONL file named with the session ID.

## Log Format

Each line in the JSONL file is a self-contained JSON object:

```json
{
  "timestamp": "2026-02-09T12:00:00.000Z",
  "sessionId": "session-1234567890",
  "event": "pre-tool",
  "tool": "Write",
  "decision": "block",
  "violations": [
    {
      "ruleId": "no-todo",
      "cycle": 1,
      "message": "Code contains a TODO comment..."
    }
  ],
  "metadata": {
    "fileExt": ".py",
    "context": "file-write"
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp |
| `sessionId` | string | Unique session identifier |
| `event` | string | `"pre-tool"` or `"post-tool"` |
| `tool` | string | Tool name (Write, Edit, Bash, etc.) |
| `decision` | string | `"approve"`, `"block"`, or `"log-only"` |
| `violations` | array | List of violations found (empty if approved) |
| `metadata` | object | Additional context (file extension, command, URL) |

### Violation Object

| Field | Type | Description |
|-------|------|-------------|
| `ruleId` | string | Rule identifier (e.g., `"no-todo"`) |
| `cycle` | number | Which cycle caught it (1, 2, or 4) |
| `message` | string | Human-readable explanation |

## Cleaning Up Old Logs

Audit logs can accumulate over time. Clean up old sessions:

<!-- tabs:start -->

#### **macOS / Linux**

```bash
# Remove logs older than 30 days
find ~/.claude/quadruple-verify-audit/ -name "*.jsonl" -mtime +30 -delete
```

#### **Windows (PowerShell)**

```powershell
Get-ChildItem ~/.claude/quadruple-verify-audit/*.jsonl |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
  Remove-Item
```

<!-- tabs:end -->

## Analyzing Logs

Since the logs are JSONL (one JSON object per line), you can analyze them with standard tools:

```bash
# Count blocks vs approvals
grep -c '"decision":"block"' session-*.jsonl
grep -c '"decision":"approve"' session-*.jsonl

# Find all blocked rules
grep '"decision":"block"' session-*.jsonl | jq '.violations[].ruleId'

# Find blocks by cycle
grep '"decision":"block"' session-*.jsonl | jq '.violations[] | select(.cycle == 2)'
```

## Disabling Audit Logging

To disable the audit trail, add this to your config:

```json
{
  "audit": {
    "enabled": false
  }
}
```

See [Configuration](reference/configuration.md) for config file locations.
