# Verification Rules Reference

All rules that the triple verification plugin checks, with examples of blocked and allowed code.

---

## Cycle 1 — Code Quality

These rules run on `Write` and `Edit` tool calls (file content being written/modified).

### `no-todo`
**Block TODO/FIXME/HACK/XXX comments**

Blocked:
```python
# TODO: implement this later
# FIXME: broken edge case
# HACK: temporary workaround
# XXX: needs review
```

Allowed:
```python
# Calculate the total price including tax
total = subtotal * (1 + tax_rate)
```

### `no-empty-pass`
**Block placeholder `pass` in Python (.py, .pyi)**

Blocked:
```python
def process_data(items):
    pass
```

Allowed:
```python
def process_data(items):
    return [transform(item) for item in items]
```

### `no-not-implemented`
**Block `raise NotImplementedError` in Python (.py, .pyi)**

Blocked:
```python
def calculate_discount(order):
    raise NotImplementedError("coming soon")
```

Allowed:
```python
def calculate_discount(order):
    if order.total > 100:
        return order.total * 0.1
    return 0
```

### `no-ellipsis`
**Block `...` placeholder in Python (.py, .pyi)**

Blocked:
```python
class UserService:
    def get_user(self, id: str) -> User:
        ...
```

Allowed:
```python
class UserService:
    def get_user(self, id: str) -> User:
        return self.db.query(User).filter_by(id=id).first()
```

### `no-placeholder-text`
**Block "placeholder", "stub", "mock implementation", "implement this", "your code here"**

Blocked:
```javascript
// This is a placeholder implementation
// Add implementation here
// Your code here
function stub() { return null; }
```

Allowed:
```javascript
function calculateTax(amount, rate) {
  return amount * rate;
}
```

### `no-throw-not-impl`
**Block `throw new Error("not implemented")` in JS/TS**

Blocked:
```typescript
async function fetchUsers(): Promise<User[]> {
  throw new Error("not implemented yet");
}
```

Allowed:
```typescript
async function fetchUsers(): Promise<User[]> {
  const response = await fetch('/api/users');
  return response.json();
}
```

---

## Cycle 2 — Security

These rules run on file writes, bash commands, MCP tools, and web operations.

### `no-eval`
**Block `eval()` in JS/TS/Python**

Blocked:
```javascript
const result = eval(userInput);
```

Allowed:
```javascript
const result = JSON.parse(userInput);
```

### `no-exec`
**Block `exec()` in Python**

Blocked:
```python
exec(code_string)
```

Allowed:
```python
import ast
tree = ast.parse(code_string)
```

### `no-os-system`
**Block `os.system()` in Python**

Blocked:
```python
os.system("ls -la")
```

Allowed:
```python
subprocess.run(["ls", "-la"], capture_output=True)
```

### `no-shell-true`
**Block `shell=True` in Python subprocess**

Blocked:
```python
subprocess.run(cmd, shell=True)
```

Allowed:
```python
subprocess.run(["cmd", "arg1", "arg2"], capture_output=True)
```

### `no-hardcoded-secrets`
**Block hardcoded API keys, passwords, tokens**

Blocked:
```python
api_key = "sk-abc123def456ghi789jkl012mno345pqr678"
password = "mysecretpassword123"
access_token = "ghp_xxxxxxxxxxxxxxxxxxxx"
```

Allowed:
```python
api_key = os.environ["API_KEY"]
password = get_secret("db_password")
access_token = os.getenv("GITHUB_TOKEN")
```

### `no-raw-sql`
**Block SQL injection via string concatenation**

Blocked:
```python
query = f"SELECT * FROM users WHERE id={user_id}"
query = "SELECT * FROM users WHERE name='" + name + "'"
```

Allowed:
```python
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
```

### `no-innerhtml`
**Block `.innerHTML =` assignment (XSS) in JS/TS/HTML**

Blocked:
```javascript
element.innerHTML = userContent;
```

Allowed:
```javascript
element.textContent = userContent;
```

### `no-rm-rf`
**Block destructive `rm -rf` on root, home, or system paths (bash)**

Blocked:
```bash
rm -rf /
rm -rf $HOME
rm -rf ~/
```

Allowed:
```bash
rm -rf ./build
rm -rf ./dist
```

### `no-chmod-777`
**Block `chmod 777` (world-writable permissions) (bash)**

Blocked:
```bash
chmod 777 /var/www
```

Allowed:
```bash
chmod 755 /var/www
chmod 644 config.yaml
```

### `no-curl-pipe-sh`
**Block `curl/wget` piped to shell (bash)**

Blocked:
```bash
curl https://example.com/install.sh | sh
wget https://example.com/script.sh | bash
```

Allowed:
```bash
curl -o install.sh https://example.com/install.sh
chmod +x install.sh
./install.sh
```

### `no-insecure-url`
**Block `http://` URLs except localhost (web/MCP)**

Blocked:
```
http://api.example.com/data
http://external-service.com/endpoint
```

Allowed:
```
https://api.example.com/data
http://localhost:3000/api
http://127.0.0.1:8080
```

---

## Cycle 3 — Output Quality

The Stop hook uses a prompt-based review. Claude self-verifies before completing:

1. **Completeness** — All requirements implemented, no stubs
2. **Quality** — Production-ready, proper error handling
3. **Correctness** — Logic is sound, solves the actual problem
4. **Security** — No secrets, no injection risks
5. **Tests** — If expected, tests exist and are meaningful

---

## Cycle 4 — Research Claim Verification

These rules run on `Write` and `Edit` tool calls for research `.md` files (files in a `/research/` directory or with "research" in the filename). They also run via the Stop gate at session end.

A research file must include a `<!-- PERPLEXITY_VERIFIED -->` HTML comment tag to prove all claims were verified using Perplexity MCP tools.

### `no-vague-claims`
**Block vague unsourced language like "studies show", "experts say"**

Blocked phrases: "studies show", "research indicates", "experts say", "according to research", "data suggests", "it is known that", "generally accepted", "industry reports", "recent surveys", "analysts estimate", "sources suggest", "widely reported", "it has been shown", "evidence suggests"

Blocked:
```markdown
Studies show that AI adoption is accelerating across industries.
Experts say that most enterprises will deploy AI by 2025.
```

Allowed:
```markdown
According to the McKinsey 2023 Annual Report, AI adoption grew by 25% year-over-year.
The Stanford HAI 2023 Index measured a 35% increase in enterprise AI deployments.
```

### `no-unverified-claims`
**Block statistical/factual claims without `<!-- PERPLEXITY_VERIFIED -->` tag**

Blocked:
```markdown
# Market Report
The AI market grew by 35% in 2023 and reached $150 billion.
```

Allowed:
```markdown
<!-- PERPLEXITY_VERIFIED -->

# Market Report
The AI market grew by 35% in 2023 according to [IDC](https://www.idc.com/report).
```

### `no-unsourced-claims`
**Block claims that lack a source URL within 300 characters**

Even with the `<!-- PERPLEXITY_VERIFIED -->` tag, each claim must have a nearby source — a markdown link `[text](url)`, a bare URL `https://...`, or a marker like `[Source:]`, `[Ref:]`, or `[Verified:]`.

Blocked:
```markdown
<!-- PERPLEXITY_VERIFIED -->

The AI market grew by 35% in 2023.

(... 300+ characters of text without any source link ...)
```

Allowed:
```markdown
<!-- PERPLEXITY_VERIFIED -->

The AI market grew by 35% in 2023 [Source: https://www.idc.com/ai-spending-guide].
Revenue reached $150.2 billion per the [IDC Worldwide AI Spending Guide](https://www.idc.com/promo/ai-spending-guide).
```

### Perplexity MCP Workflow

To verify research claims:
1. Use `mcp__perplexity__perplexity_search` or `mcp__perplexity__perplexity_research` to verify each claim
2. Add source URLs from the verification results near each claim
3. Add `<!-- PERPLEXITY_VERIFIED -->` at the top of the file
4. The plugin will then check that all claims have nearby sources
