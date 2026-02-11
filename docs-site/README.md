# CustomGPT Quadruple Verification

> Automatic quadruple verification on every Claude Code operation. Blocks placeholder code, security vulnerabilities, and ensures output quality — before anything ships.

Built by [CustomGPT.ai](https://customgpt.ai) for production teams running Claude Code at scale.

## What It Does

Four verification cycles run automatically on every Claude Code operation:

| Cycle | When | What |
|-------|------|------|
| **[Cycle 1 — Code Quality](cycles/cycle-1.md)** | Before file write/edit | Blocks TODO, placeholder, stub, and incomplete code |
| **[Cycle 2 — Security](cycles/cycle-2.md)** | Before write/edit/bash/MCP | Blocks eval(), hardcoded secrets, SQL injection, XSS, destructive commands |
| **[Cycle 3 — Output Quality](cycles/cycle-3.md)** | Before Claude finishes | Second AI review ensures completeness and correctness |
| **[Cycle 4 — Research Claims](cycles/cycle-4.md)** | Before write/edit of research .md | Blocks vague language, unverified stats, missing source URLs |
| **Audit Trail** | After every operation | Full JSONL audit log of all operations |

## Quick Install

<!-- tabs:start -->

#### **Marketplace (Recommended)**

Two commands inside Claude Code — includes auto-updates:

```
/plugin marketplace add kirollosatef/customgpt-claude-quadruple-verification
/plugin install customgpt-claude-quadruple-verification@kirollosatef-customgpt-claude-quadruple-verification
```

That's it. The plugin auto-updates every session.

#### **npx**

Run from any terminal:

```bash
npx @customgpt/claude-quadruple-verification
```

#### **Manual Install**

**Windows (PowerShell):**
```powershell
git clone https://github.com/kirollosatef/customgpt-claude-quadruple-verification.git
cd customgpt-claude-quadruple-verification
.\install\install.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/kirollosatef/customgpt-claude-quadruple-verification.git
cd customgpt-claude-quadruple-verification
bash install/install.sh
```

<!-- tabs:end -->

## Verify Installation

```bash
node install/verify.mjs
```

## Test It

1. Start Claude Code in any project
2. Ask: *"Create a Python file with a TODO comment"*
3. The operation should be **BLOCKED** with an explanation
4. Check audit logs in `.claude/quadruple-verify-audit/`

## How It Works

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

## Key Features

- :shield: **20 verification rules** across code quality, security, and research integrity
- :zap: **Zero dependencies** — Uses only Node.js built-ins for reliability and no supply chain risk
- :white_check_mark: **Fail-open design** — If a verifier crashes, operations proceed; never breaks Claude
- :globe_with_meridians: **Cross-platform** — Works on Windows, macOS, Linux, and WSL
- :busts_in_silhouette: **Team-ready** — One config file enables it for your entire team
- :arrows_counterclockwise: **Auto-updates** — Marketplace installs update every session

## Next Steps

- [Quick Start Guide](guide/quick-start.md) — Detailed installation walkthrough
- [Verification Cycles Overview](cycles/overview.md) — How the four cycles work
- [Configuration](reference/configuration.md) — Customize rules per project
- [Architecture](reference/architecture.md) — Technical deep dive
