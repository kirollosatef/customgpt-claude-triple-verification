# Quick Start

## Requirements

- **Node.js** >= 18
- **Claude Code** CLI installed and working

## Installation

Choose your preferred installation method:

<!-- tabs:start -->

#### **Marketplace (Recommended)**

The marketplace method gives you auto-updates and is the simplest setup.

**Step 1:** Open Claude Code in any project.

**Step 2:** Add the marketplace source:
```
/plugin marketplace add kirollosatef/customgpt-claude-quadruple-verification
```

**Step 3:** Install the plugin:
```
/plugin install customgpt-claude-quadruple-verification@kirollosatef-customgpt-claude-quadruple-verification
```

That's it. The plugin is now active and will auto-update every session.

#### **npx**

Run from any terminal. This fetches the latest version each time:

```bash
npx @customgpt/claude-quadruple-verification
```

The npx installer will:
1. Detect your OS (Windows, macOS, Linux, or WSL)
2. Copy hook scripts to the correct Claude Code plugin directory
3. Register the hooks automatically

#### **Manual Install (Windows)**

```powershell
git clone https://github.com/kirollosatef/customgpt-claude-quadruple-verification.git
cd customgpt-claude-quadruple-verification
.\install\install.ps1
```

#### **Manual Install (macOS / Linux)**

```bash
git clone https://github.com/kirollosatef/customgpt-claude-quadruple-verification.git
cd customgpt-claude-quadruple-verification
bash install/install.sh
```

<!-- tabs:end -->

## Verify Installation

After installing, run the smoke test to confirm everything is working:

```bash
node install/verify.mjs
```

This checks:
- Hook configuration is valid JSON
- All referenced script files exist
- Rules engine loads correctly
- Config loader works
- Audit logger initializes

## Test It Live

1. Start Claude Code in any project
2. Ask: *"Create a Python file with a TODO comment"*
3. The operation should be **BLOCKED** with a message like:

   > Code contains a TODO comment. Remove TODO/FIXME/HACK/XXX comments and implement the actual code.

4. Check the audit log:
   ```bash
   ls .claude/quadruple-verify-audit/
   ```

## What Happens Next

With the plugin installed, every Claude Code operation goes through four verification cycles automatically:

- **Write/Edit a file** → Cycle 1 (code quality) + Cycle 2 (security) check the content
- **Run a bash command** → Cycle 2 (security) checks for destructive commands
- **Claude finishes responding** → Cycle 3 (output quality) reviews the response
- **Write a research .md file** → Cycle 4 (research claims) checks for sourced claims
- **Every operation** → Audit trail logs the result

No configuration needed — the plugin works with sensible defaults out of the box.

## Next Steps

- [Team Setup](guide/team-setup.md) — Roll out to your entire team
- [Configuration](reference/configuration.md) — Customize rules for your project
- [Verification Cycles](cycles/overview.md) — Understand what each cycle does
