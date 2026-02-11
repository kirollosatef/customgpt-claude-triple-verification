# Auto-Updates

How the plugin stays up to date depends on your installation method.

## Update Behavior by Install Method

| Method | Update Mechanism | Action Required |
|--------|-----------------|-----------------|
| **Marketplace** | Auto-updates every session | None — always current |
| **npx** | Fetches latest on each run | Run `npx` command again |
| **Manual (git)** | No auto-update | Run `git pull` manually |

## Marketplace (Automatic)

Marketplace installs are the recommended method because they auto-update every time you start a Claude Code session. When the plugin repository is updated:

1. Push changes to the `master` branch
2. Next time any user starts Claude Code, the plugin updates automatically
3. No action required from individual users

This makes it ideal for teams — push a rule update and everyone gets it immediately.

## npx (Per-Run)

Each time you run `npx @customgpt/claude-quadruple-verification`, npm fetches the latest published version. To update:

```bash
npx @customgpt/claude-quadruple-verification
```

If you're seeing a cached version, clear the npx cache:

```bash
npx --yes @customgpt/claude-quadruple-verification
```

## Manual Install (Git Pull)

For manual installations via `git clone`, you need to pull updates yourself:

```bash
cd ~/.claude/plugins/customgpt-claude-quadruple-verification
git pull origin master
```

Then re-run the install script to update hook registrations:

<!-- tabs:start -->

#### **Windows**

```powershell
.\install\install.ps1
```

#### **macOS / Linux**

```bash
bash install/install.sh
```

<!-- tabs:end -->

## Checking Your Version

Check which version you're running by looking at the changelog or package.json:

```bash
# In the plugin directory
cat package.json | grep version
```

Compare against the [latest release](https://github.com/kirollosatef/customgpt-claude-quadruple-verification/blob/master/CHANGELOG.md).
