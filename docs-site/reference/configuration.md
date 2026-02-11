# Configuration

The plugin works out of the box with sensible defaults. Configuration is optional and allows you to customize behavior per-user or per-project.

## Config Merge Order

Configuration is loaded and merged from three sources (later overrides earlier):

```
config/default-rules.json                          # Plugin defaults
        ↓ merge
~/.claude/quadruple-verify-config.json             # User overrides
        ↓ merge
$PROJECT/.claude/quadruple-verify-config.json      # Project overrides
        ↓
    Final config
```

Deep merge is used: nested objects are merged recursively, arrays are replaced.

## Config File Locations

| Source | Path | Scope |
|--------|------|-------|
| **Plugin defaults** | `config/default-rules.json` (inside the plugin) | All users |
| **User config** | `~/.claude/quadruple-verify-config.json` | Current user, all projects |
| **Project config** | `$PROJECT/.claude/quadruple-verify-config.json` | Current project, all users |

## Configuration Options

### Disable Specific Rules

Disable rules by adding their IDs to the `disabledRules` array:

```json
{
  "disabledRules": ["no-todo", "no-empty-pass"]
}
```

### Available Rule IDs

**Cycle 1 — Code Quality:**
- `no-todo` — Block TODO/FIXME/HACK/XXX comments
- `no-empty-pass` — Block placeholder `pass` in Python
- `no-not-implemented` — Block `raise NotImplementedError`
- `no-ellipsis` — Block `...` placeholder in Python
- `no-placeholder-text` — Block placeholder/stub text
- `no-throw-not-impl` — Block `throw new Error("not implemented")`

**Cycle 2 — Security:**
- `no-eval` — Block `eval()`
- `no-exec` — Block `exec()` in Python
- `no-os-system` — Block `os.system()`
- `no-shell-true` — Block `shell=True`
- `no-hardcoded-secrets` — Block hardcoded secrets
- `no-raw-sql` — Block SQL injection
- `no-innerhtml` — Block `.innerHTML =`
- `no-rm-rf` — Block destructive `rm -rf`
- `no-chmod-777` — Block `chmod 777`
- `no-curl-pipe-sh` — Block `curl | sh`
- `no-insecure-url` — Block `http://` URLs

**Cycle 4 — Research Claims:**
- `no-vague-claims` — Block vague language
- `no-unverified-claims` — Block unverified statistics
- `no-unsourced-claims` — Block claims without source URLs

### Audit Configuration

Control audit logging:

```json
{
  "audit": {
    "enabled": true
  }
}
```

## Examples

### Disable a single rule (user-level)

Create `~/.claude/quadruple-verify-config.json`:

```json
{
  "disabledRules": ["no-placeholder-text"]
}
```

### Project-specific configuration

Create `.claude/quadruple-verify-config.json` in your project root:

```json
{
  "disabledRules": ["no-empty-pass", "no-ellipsis"],
  "audit": {
    "enabled": true
  }
}
```

### Disable all Cycle 1 rules

```json
{
  "disabledRules": [
    "no-todo",
    "no-empty-pass",
    "no-not-implemented",
    "no-ellipsis",
    "no-placeholder-text",
    "no-throw-not-impl"
  ]
}
```

## Debugging Config Issues

If disabled rules are still firing:

1. Verify your JSON syntax is valid:
   ```bash
   node -e "console.log(JSON.parse(require('fs').readFileSync('.claude/quadruple-verify-config.json', 'utf-8')))"
   ```
2. Check the file is in the correct location
3. Ensure `disabledRules` is an array of strings matching the rule IDs listed above
