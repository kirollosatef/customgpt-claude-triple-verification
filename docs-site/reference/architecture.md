# Architecture

## Overview

CustomGPT Quadruple Verification is a Claude Code plugin that intercepts every tool operation through the hook system. It runs four verification cycles and an audit logger, all implemented in Node.js with zero npm dependencies.

## Design Principles

1. **Zero dependencies** — Uses only Node.js built-ins (`fs`, `path`, `process`, `os`) for cross-OS reliability and no supply chain risk
2. **Fail-open** — If a verifier crashes, operations proceed. The plugin must never "break Claude"
3. **Block by default** — Violations are blocked; Claude must fix issues before proceeding
4. **One dispatcher per event** — Hooks run in parallel, so ordering is handled internally
5. **Cross-OS** — Works on Windows, macOS, Linux, and WSL

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
```

## Hook Lifecycle

Claude Code provides three hook events:

| Event | When | Can Block? |
|-------|------|-----------|
| `PreToolUse` | Before a tool call executes | Yes (command type) |
| `PostToolUse` | After a tool call completes | No (command type) |
| `Stop` | Before Claude finishes responding | Yes (prompt type) |

## Data Flow

### PreToolUse (Cycles 1, 2, 4)

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
```

### Stop (Cycles 3 and 4)

```
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

### PostToolUse (Audit)

```
stdin (JSON) → post-tool-audit.mjs
                    ↓
              Extract tool name, decision, metadata
                    ↓
              Append JSONL entry to audit log
                    ↓
              exit 0 (never blocks)
```

## Error Handling

All hook scripts wrap their main logic in `failOpen()`:

- **On success:** Output decision and exit 0
- **On error:** Write to stderr, exit 0 (operation proceeds)
- **Audit logging errors** are silently swallowed (never block operations)

This ensures the plugin can never prevent Claude Code from functioning, even if the verifier has a bug or the filesystem is unavailable.

## Installation Methods

| Method | Command | Auto-Updates |
|--------|---------|--------------|
| **Marketplace** (recommended) | `/plugin marketplace add ...` | Yes |
| **npx** | `npx @customgpt/claude-quadruple-verification` | Per-run |
| **Manual** | `git clone` + install script | No (`git pull`) |

For details, see [Quick Start](guide/quick-start.md).
