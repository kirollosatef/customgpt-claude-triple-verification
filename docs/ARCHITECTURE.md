# Architecture

## Overview

CustomGPT Triple Verification is a Claude Code plugin that intercepts every tool operation through the hook system. It runs three verification cycles and an audit logger, all implemented in Node.js with zero npm dependencies.

## Design Principles

1. **Zero dependencies** — Uses only Node.js built-ins (fs, path, process, os) for cross-OS reliability and no supply chain risk
2. **Fail-open** — If a verifier crashes, operations proceed. The plugin must never "break Claude"
3. **Block by default** — Violations are blocked; Claude must fix issues before proceeding
4. **One dispatcher per event** — Hooks run in parallel, so ordering is handled internally
5. **Cross-OS** — Works on Windows, macOS, Linux, and WSL

## Installation Methods

The plugin supports three install methods:

| Method | Command | Auto-Updates |
|--------|---------|--------------|
| **Marketplace** (recommended) | `/plugin marketplace add kirollosatef/customgpt-claude-triple-verification` | Yes |
| **npx** | `npx @customgpt/claude-triple-verification` | Per-run |
| **Manual** | `git clone` + install script | No (`git pull`) |

For team rollout, commit a `.claude/settings.json` with the plugin reference — team members get prompted to install automatically.

## Hook Lifecycle

Claude Code provides three hook events:

| Event | When | Can Block? |
|-------|------|-----------|
| `PreToolUse` | Before a tool call executes | Yes (command type) |
| `PostToolUse` | After a tool call completes | No (command type) |
| `Stop` | Before Claude finishes responding | Yes (prompt type) |

### Hook Configuration Format

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
    "PostToolUse": [ ... ],
    "Stop": [ ... ]
  }
}
```

The `${CLAUDE_PLUGIN_ROOT}` variable is resolved by Claude Code to the plugin's installation directory.

## Verification Cycles

### Cycle 1 — Code Quality (PreToolUse)

**Triggers:** Write, Edit tools
**Type:** Command hook (blocks on violation)

Runs regex-based pattern matching against file content being written or edited. Catches:
- TODO/FIXME/HACK/XXX comments
- Placeholder `pass` statements in Python
- `raise NotImplementedError` stubs
- Ellipsis (`...`) placeholders in Python
- "placeholder", "stub", "implement this" text
- `throw new Error("not implemented")` in JS/TS

### Cycle 2 — Security (PreToolUse)

**Triggers:** Write, Edit, Bash, MCP tools, WebFetch, WebSearch
**Type:** Command hook (blocks on violation)

Runs security-focused pattern matching. Catches:
- `eval()` and `exec()` usage
- `os.system()` and `shell=True` in Python
- Hardcoded API keys, passwords, and tokens
- SQL injection via string concatenation
- `.innerHTML =` XSS vectors
- Destructive bash commands (`rm -rf /`, `chmod 777`)
- `curl | sh` pipe-to-shell patterns
- Non-HTTPS URLs (except localhost)

### Cycle 3 — Output Quality (Stop)

**Triggers:** Before Claude completes any response
**Type:** Prompt hook

Injects a review prompt that asks Claude to self-verify:
1. Completeness — No placeholders or stubs left behind
2. Quality — Production-ready code with proper error handling
3. Correctness — Implementation actually solves the problem
4. Security — No hardcoded secrets or injection risks
5. Tests — If tests were expected, they exist and pass

### Cycle 4 — Research Claim Verification (PreToolUse + Stop)

**Triggers:** Write/Edit of research `.md` files (PreToolUse) + session end scan (Stop)
**Type:** Command hook (blocks on violation)

Runs two-pass verification on research markdown files. A file is considered "research" if it has a `.md` extension AND either lives in a `/research/` directory or has "research" in its filename.

**Pass 1 — Vague Language Detection:**
Scans for 14 vague phrases like "studies show", "experts say", "data suggests". Instant block if found.

**Pass 2 — Claim Extraction + Source Proximity:**
1. Extracts statistical/factual claims (percentages, dollar amounts, multipliers, study references, etc.)
2. Requires `<!-- PERPLEXITY_VERIFIED -->` tag — proves claims were checked via Perplexity MCP tools
3. Each claim must have a source URL (markdown link, bare URL, or `[Source:]`/`[Ref:]`/`[Verified:]` marker) within 300 characters

The **Stop gate** also scans `docs/research/`, `research/`, and `docs/` directories at session end for any research files that may have been written without going through the PreToolUse gate.

### Audit Trail (PostToolUse)

**Triggers:** All tool calls
**Type:** Command hook (non-blocking)

Logs every operation to a JSONL file for full auditability. Each entry includes:
- Timestamp (ISO 8601)
- Session ID
- Tool name
- Decision (approve/block/log-only)
- Violations found (if any)
- Metadata (file path, command, URL)

## File Structure

```
.claude-plugin/
├── plugin.json                # Plugin manifest
└── marketplace.json           # Marketplace catalog
bin/
└── cli.mjs                    # npx entry point (installer)
scripts/
├── pre-tool-gate.mjs          # Main dispatcher for PreToolUse (Cycles 1-2 + Cycle 4 routing)
├── post-tool-audit.mjs        # Audit logger for PostToolUse
├── stop-gate.mjs              # Stop gate — scans research files at session end (Cycle 4)
└── lib/
    ├── rules-engine.mjs       # All Cycle 1 + 2 rule definitions
    ├── research-verifier.mjs  # Cycle 4 research claim verification engine
    ├── audit-logger.mjs       # JSONL structured logging
    ├── config-loader.mjs      # Multi-source config merge
    └── utils.mjs              # Stdin reader, helpers, isResearchFile()
hooks/
└── hooks.json                 # Hook configuration (event-keyed)
config/
└── default-rules.json         # Default rule settings
install/
├── install.ps1                # Windows installer
├── install.sh                 # macOS/Linux/WSL installer
└── verify.mjs                 # Post-install smoke test
docs/
├── ARCHITECTURE.md            # This file
├── RULES.md                   # Rule reference with examples
├── TROUBLESHOOTING.md         # Common issues and fixes
└── team-setup/
    └── settings.json          # Template for team rollout
```

## Data Flow

```
stdin (JSON) → pre-tool-gate.mjs
                    ↓
              extractContent()     # Determine what to verify based on tool type
                    ↓
              isResearchFile?
              ├── YES → runCycle4()   # Research claim verification
              └── NO  → runCycle1()   # Code quality patterns
                        runCycle2()   # Security patterns
                    ↓
              violations?
              ├── YES → deny() + logPreTool('block')
              └── NO  → approve() + logPreTool('approve')

Stop hook (session end):
              stop-gate.mjs
                    ↓
              Find research .md files in docs/research/, research/, docs/
                    ↓
              runCycle4() on each file
                    ↓
              violations?
              ├── YES → deny() with per-file summary
              └── NO  → approve()
```

## Configuration Merge

```
config/default-rules.json          # Plugin defaults
        ↓ merge
~/.claude/triple-verify-config.json    # User overrides
        ↓ merge
$PROJECT/.claude/triple-verify-config.json  # Project overrides
        ↓
    Final config
```

Deep merge is used: nested objects are merged recursively, arrays are replaced.

## Audit Log Format

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

## Error Handling

All hook scripts wrap their main logic in `failOpen()`:
- On success: output decision and exit 0
- On error: write to stderr, exit 0 (operation proceeds)
- Audit logging errors are silently swallowed (never block operations)
