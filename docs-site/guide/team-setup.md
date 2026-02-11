# Team Setup

Roll out Quadruple Verification to your entire team with a single config file.

## How It Works

When you commit a `.claude/settings.json` file to your repository with the plugin reference, every team member who opens the project in Claude Code will be prompted to install the plugin automatically.

## Setup

**Step 1:** Create `.claude/settings.json` in your project root:

```json
{
  "plugins": [
    "kirollosatef/customgpt-claude-quadruple-verification"
  ]
}
```

**Step 2:** Commit and push:

```bash
git add .claude/settings.json
git commit -m "Add quadruple verification plugin for team"
git push
```

**Step 3:** When any team member opens the project in Claude Code, they'll see a prompt to install the plugin. One click and they're protected.

## Project-Level Configuration

You can also commit a project-level config to customize which rules are active:

```json
// .claude/quadruple-verify-config.json
{
  "disabledRules": ["no-empty-pass"],
  "audit": {
    "enabled": true
  }
}
```

This config will apply to everyone working on the project, ensuring consistent verification standards.

## What Team Members See

Once installed, the plugin runs silently in the background. Team members will only notice it when:

1. **A violation is caught** — They'll see a clear message explaining what was blocked and why
2. **Cycle 3 output review** — A quality gateway table appears at the end of each response
3. **Audit logs** — A `.claude/quadruple-verify-audit/` directory appears with session logs

## Recommended Team Workflow

1. **Enable for all repos** — Add `.claude/settings.json` to every repository
2. **Customize per project** — Use `.claude/quadruple-verify-config.json` for project-specific rules
3. **Review audit logs** — Periodically check what violations are being caught
4. **Update rules** — The marketplace install auto-updates, so new rules roll out automatically

## Template

A ready-to-use template is available at [`docs/team-setup/settings.json`](https://github.com/kirollosatef/customgpt-claude-quadruple-verification/blob/master/docs/team-setup/settings.json) in the repository.
