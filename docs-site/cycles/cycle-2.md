# Cycle 2 — Security

<span class="badge badge-cycle2">PreToolUse</span> <span class="badge badge-block">Blocks on violation</span>

Cycle 2 runs on **Write**, **Edit**, **Bash**, **MCP tools**, **WebFetch**, and **WebSearch** tool calls. It detects security vulnerabilities and dangerous operations before they execute.

## Why This Matters

AI coding assistants can inadvertently introduce security vulnerabilities — `eval()` calls, hardcoded secrets, SQL injection, XSS vectors, and destructive shell commands. Cycle 2 catches these at the point of execution.

## Rules

### `no-eval` — Block `eval()`

Applies to: JS/TS/Python files

**Blocked:**
```javascript
const result = eval(userInput);
```

**Allowed:**
```javascript
const result = JSON.parse(userInput);
```

---

### `no-exec` — Block `exec()` in Python

**Blocked:**
```python
exec(code_string)
```

**Allowed:**
```python
import ast
tree = ast.parse(code_string)
```

---

### `no-os-system` — Block `os.system()` in Python

**Blocked:**
```python
os.system("ls -la")
```

**Allowed:**
```python
subprocess.run(["ls", "-la"], capture_output=True)
```

---

### `no-shell-true` — Block `shell=True` in subprocess

**Blocked:**
```python
subprocess.run(cmd, shell=True)
```

**Allowed:**
```python
subprocess.run(["cmd", "arg1", "arg2"], capture_output=True)
```

---

### `no-hardcoded-secrets` — Block hardcoded API keys, passwords, tokens

**Blocked:**
```python
api_key = "sk-abc123def456ghi789jkl012mno345pqr678"
password = "mysecretpassword123"
access_token = "ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Allowed:**
```python
api_key = os.environ["API_KEY"]
password = get_secret("db_password")
access_token = os.getenv("GITHUB_TOKEN")
```

---

### `no-raw-sql` — Block SQL injection via string concatenation

**Blocked:**
```python
query = f"SELECT * FROM users WHERE id={user_id}"
query = "SELECT * FROM users WHERE name='" + name + "'"
```

**Allowed:**
```python
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
```

---

### `no-innerhtml` — Block `.innerHTML =` (XSS)

Applies to: JS/TS/HTML files

**Blocked:**
```javascript
element.innerHTML = userContent;
```

**Allowed:**
```javascript
element.textContent = userContent;
```

---

### `no-rm-rf` — Block destructive `rm -rf`

Applies to: Bash commands. Blocks `rm -rf` on root, home, or system paths.

**Blocked:**
```bash
rm -rf /
rm -rf $HOME
rm -rf ~/
```

**Allowed:**
```bash
rm -rf ./build
rm -rf ./dist
```

---

### `no-chmod-777` — Block world-writable permissions

Applies to: Bash commands

**Blocked:**
```bash
chmod 777 /var/www
```

**Allowed:**
```bash
chmod 755 /var/www
chmod 644 config.yaml
```

---

### `no-curl-pipe-sh` — Block `curl`/`wget` piped to shell

Applies to: Bash commands

**Blocked:**
```bash
curl https://example.com/install.sh | sh
wget https://example.com/script.sh | bash
```

**Allowed:**
```bash
curl -o install.sh https://example.com/install.sh
chmod +x install.sh
./install.sh
```

---

### `no-insecure-url` — Block `http://` URLs (except localhost)

Applies to: Web/MCP operations

**Blocked:**
```
http://api.example.com/data
http://external-service.com/endpoint
```

**Allowed:**
```
https://api.example.com/data
http://localhost:3000/api
http://127.0.0.1:8080
```

## Disabling Rules

If you need to allow a specific pattern (e.g., `eval` in a build tool), disable the rule:

```json
{
  "disabledRules": ["no-eval"]
}
```

See [Configuration](reference/configuration.md) for details.
