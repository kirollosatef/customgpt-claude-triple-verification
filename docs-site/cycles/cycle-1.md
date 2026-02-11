# Cycle 1 — Code Quality

<span class="badge badge-cycle1">PreToolUse</span> <span class="badge badge-block">Blocks on violation</span>

Cycle 1 runs on every **Write** and **Edit** tool call. It uses regex pattern matching to detect placeholder code, stubs, and incomplete implementations.

## Why This Matters

AI coding assistants sometimes leave behind TODO comments, stub functions, or placeholder text — especially when working on complex tasks. Cycle 1 catches these before they reach your codebase.

## Rules

### `no-todo` — Block TODO/FIXME/HACK/XXX comments

**Blocked:**
```python
# TODO: implement this later
# FIXME: broken edge case
# HACK: temporary workaround
# XXX: needs review
```

**Allowed:**
```python
# Calculate the total price including tax
total = subtotal * (1 + tax_rate)
```

---

### `no-empty-pass` — Block placeholder `pass` in Python

Applies to: `.py`, `.pyi` files

**Blocked:**
```python
def process_data(items):
    pass
```

**Allowed:**
```python
def process_data(items):
    return [transform(item) for item in items]
```

---

### `no-not-implemented` — Block `raise NotImplementedError`

Applies to: `.py`, `.pyi` files

**Blocked:**
```python
def calculate_discount(order):
    raise NotImplementedError("coming soon")
```

**Allowed:**
```python
def calculate_discount(order):
    if order.total > 100:
        return order.total * 0.1
    return 0
```

---

### `no-ellipsis` — Block `...` placeholder in Python

Applies to: `.py`, `.pyi` files

**Blocked:**
```python
class UserService:
    def get_user(self, id: str) -> User:
        ...
```

**Allowed:**
```python
class UserService:
    def get_user(self, id: str) -> User:
        return self.db.query(User).filter_by(id=id).first()
```

---

### `no-placeholder-text` — Block placeholder/stub text

Catches: "placeholder", "stub", "mock implementation", "implement this", "your code here"

**Blocked:**
```javascript
// This is a placeholder implementation
// Add implementation here
// Your code here
function stub() { return null; }
```

**Allowed:**
```javascript
function calculateTax(amount, rate) {
  return amount * rate;
}
```

---

### `no-throw-not-impl` — Block `throw new Error("not implemented")`

Applies to: `.js`, `.ts`, `.jsx`, `.tsx` files

**Blocked:**
```typescript
async function fetchUsers(): Promise<User[]> {
  throw new Error("not implemented yet");
}
```

**Allowed:**
```typescript
async function fetchUsers(): Promise<User[]> {
  const response = await fetch('/api/users');
  return response.json();
}
```

## Disabling Rules

If a rule causes false positives for your project (e.g., `no-placeholder-text` matching HTML placeholder attributes), disable it in your config:

```json
{
  "disabledRules": ["no-placeholder-text"]
}
```

See [Configuration](reference/configuration.md) for details on where to place this file.
