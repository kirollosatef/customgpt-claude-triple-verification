"""
Quadruple Verification — Claude Agent SDK hooks (Python port).

Drop this file into your project and wire up the hooks:

    from quadruple_verification import make_hooks

    options = ClaudeAgentOptions(hooks=make_hooks())

That's it. All four verification cycles run automatically.

Config (optional) — create any of these JSON files:
    ~/.claude/quadruple-verify-config.json
    <project>/.claude/quadruple-verify-config.json

    {
        "disabledRules": ["no-todo", "no-ellipsis"],
        "cycle1": { "enabled": false },
        "cycle4": { "enabled": false },
        "audit": { "enabled": true, "logDir": "/tmp/audit" }
    }
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ─── Cycle 1: Code Quality Rules ─────────────────────────────────────────────

_CYCLE1_RULES = [
    {
        "id": "no-todo",
        "pattern": re.compile(r"\b(TODO|FIXME|HACK|XXX)\b"),
        "applies_to": "file-write",
        "extensions": None,
        "message": (
            "Code contains a TODO/FIXME/HACK/XXX comment. "
            "Remove placeholder comments and implement the actual logic."
        ),
    },
    {
        "id": "no-empty-pass",
        "pattern": re.compile(r"^\s*pass\s*$", re.MULTILINE),
        "applies_to": "file-write",
        "extensions": {".py", ".pyi"},
        "message": (
            'Python file contains a bare "pass" statement. '
            "Implement the actual logic instead of using a placeholder."
        ),
    },
    {
        "id": "no-not-implemented",
        "pattern": re.compile(r"raise\s+NotImplementedError"),
        "applies_to": "file-write",
        "extensions": {".py", ".pyi"},
        "message": (
            "Code raises NotImplementedError. "
            "Implement the actual functionality instead of leaving a stub."
        ),
    },
    {
        "id": "no-ellipsis",
        "pattern": re.compile(r"^\s*\.\.\.\s*$", re.MULTILINE),
        "applies_to": "file-write",
        "extensions": {".py", ".pyi"},
        "message": (
            "Python file contains an ellipsis (...) placeholder. "
            "Implement the actual logic."
        ),
    },
    {
        "id": "no-placeholder-text",
        "pattern": re.compile(
            r"\b(placeholder|stub|mock implementation|implement\s+this"
            r"|add\s+implementation\s+here|your\s+code\s+here)\b",
            re.IGNORECASE,
        ),
        "applies_to": "file-write",
        "extensions": None,
        "message": "Code contains placeholder/stub text. Write the complete implementation.",
    },
    {
        "id": "no-throw-not-impl",
        "pattern": re.compile(
            r"throw\s+new\s+Error\s*\(\s*['\"`].*not\s+implemented", re.IGNORECASE
        ),
        "applies_to": "file-write",
        "extensions": {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"},
        "message": (
            'Code throws a "not implemented" error. '
            "Implement the actual functionality."
        ),
    },
]

# ─── Cycle 2: Security Rules ──────────────────────────────────────────────────

_CYCLE2_RULES = [
    {
        "id": "no-eval",
        "pattern": re.compile(r"\beval\s*\("),
        "applies_to": "file-write",
        "extensions": {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs", ".py"},
        "message": (
            "Code uses eval(). This is a critical security risk (code injection). "
            "Use a safe alternative."
        ),
    },
    {
        "id": "no-exec",
        "pattern": re.compile(r"\bexec\s*\("),
        "applies_to": "file-write",
        "extensions": {".py"},
        "message": (
            "Python code uses exec(). This allows arbitrary code execution. "
            "Use a safe alternative."
        ),
    },
    {
        "id": "no-os-system",
        "pattern": re.compile(r"\bos\.system\s*\("),
        "applies_to": "file-write",
        "extensions": {".py"},
        "message": "Python code uses os.system(). Use subprocess.run() with shell=False instead.",
    },
    {
        "id": "no-shell-true",
        "pattern": re.compile(r"shell\s*=\s*True"),
        "applies_to": "file-write",
        "extensions": {".py"},
        "message": (
            "Python code uses shell=True in subprocess. This enables shell injection. "
            "Use shell=False and pass args as a list."
        ),
    },
    {
        "id": "no-hardcoded-secrets",
        "pattern": re.compile(
            r"(?:api[_-]?key|api[_-]?secret|password|passwd|secret[_-]?key"
            r"|access[_-]?token|auth[_-]?token|private[_-]?key)"
            r"\s*[:=]\s*['\"`][A-Za-z0-9+/=_\-]{8,}",
            re.IGNORECASE,
        ),
        "applies_to": "file-write",
        "extensions": None,
        "message": (
            "Code contains what appears to be a hardcoded secret (API key, password, or token). "
            "Use environment variables or a secrets manager instead."
        ),
    },
    {
        "id": "no-raw-sql",
        "pattern": re.compile(
            r"(?:f['\"`].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)\s+.*\{"
            r"|(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)\s+.*"
            r"(?:['\"\s]*\+|\+\s*['\"]|\$\{|%s|\.format\())",
            re.IGNORECASE,
        ),
        "applies_to": "file-write",
        "extensions": None,
        "message": (
            "Code constructs SQL using string concatenation/interpolation. "
            "Use parameterized queries to prevent SQL injection."
        ),
    },
    {
        "id": "no-innerhtml",
        "pattern": re.compile(r"\.innerHTML\s*="),
        "applies_to": "file-write",
        "extensions": {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs", ".html"},
        "message": (
            "Code assigns to .innerHTML which enables XSS attacks. "
            "Use .textContent or a sanitization library instead."
        ),
    },
    {
        "id": "no-rm-rf",
        "pattern": re.compile(
            r"rm\s+(-[a-zA-Z]*)?r[a-zA-Z]*f[a-zA-Z]*\s+"
            r"(?:\/(?:\s|$|\*)|\$HOME|\$\{HOME\}|~\/|\/root|C:\\)",
            re.IGNORECASE,
        ),
        "applies_to": "bash",
        "extensions": None,
        "message": (
            "Command attempts destructive recursive delete on a critical path. "
            "This could destroy the system."
        ),
    },
    {
        "id": "no-chmod-777",
        "pattern": re.compile(r"chmod\s+(?:.*\s)?777\b"),
        "applies_to": "bash",
        "extensions": None,
        "message": (
            "Command sets world-writable permissions (777). "
            "Use more restrictive permissions (e.g. 755 or 644)."
        ),
    },
    {
        "id": "no-curl-pipe-sh",
        "pattern": re.compile(r"(?:curl|wget)\s+.*\|\s*(?:ba)?sh"),
        "applies_to": "bash",
        "extensions": None,
        "message": (
            "Command pipes downloaded content directly to a shell. "
            "Download first, inspect, then execute."
        ),
    },
    {
        "id": "no-insecure-url",
        "pattern": re.compile(
            r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])"
        ),
        "applies_to": "web",
        "extensions": None,
        "message": (
            "URL uses insecure HTTP instead of HTTPS. "
            "Use HTTPS for all non-localhost connections."
        ),
    },
]

# ─── Cycle 4: Research Claim Verification ─────────────────────────────────────

_VAGUE_PHRASES = [
    "studies show", "research indicates", "experts say",
    "according to research", "data suggests", "it is known that",
    "generally accepted", "industry reports", "recent surveys",
    "analysts estimate", "sources suggest", "widely reported",
    "it has been shown", "evidence suggests",
]

_VAGUE_PATTERN = re.compile(
    "|".join(p.replace(" ", r"\s+") for p in _VAGUE_PHRASES),
    re.IGNORECASE,
)

_CLAIM_PATTERNS = [
    re.compile(r"\d+(\.\d+)?\s*%"),
    re.compile(r"\d+(\.\d+)?x\b"),
    re.compile(r"\d+-fold\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(,\d{3})+\b"),
    re.compile(r"\$\s*\d+(\.\d+)?\s*(million|billion|trillion|[MBTmbt])\b", re.IGNORECASE),
    re.compile(r"\b(study|survey|report)\s+(by|from|at)\b", re.IGNORECASE),
    re.compile(r"\b[A-Z][a-z]+\s+(University|Institute|Lab)\b"),
    re.compile(
        r"\b\d+(\.\d+)?\s*times\s+(more|less|faster|slower|higher|lower|greater|better|worse)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(in|since|by|from)\s+\d{4}\b", re.IGNORECASE),
]

_SOURCE_PATTERNS = [
    re.compile(r"\[.*?\]\(https?://[^\s)]+\)"),
    re.compile(r"https?://[^\s)>\]]+"),
    re.compile(r"\[(Source|Ref|Verified):?[^\]]*\]", re.IGNORECASE),
]

_VERIFICATION_TAG = "<!-- PERPLEXITY_VERIFIED -->"
_SOURCE_PROXIMITY = 300


# ─── Rules Engine ─────────────────────────────────────────────────────────────

def _run_rules(rules: list, content: str, file_ext: str, context: str, disabled: set) -> list:
    violations = []
    for rule in rules:
        if rule["id"] in disabled:
            continue
        if rule["applies_to"] != "all" and rule["applies_to"] != context:
            continue
        exts = rule.get("extensions")
        if exts and file_ext and file_ext not in exts:
            continue
        if rule["pattern"].search(content):
            violations.append({"rule_id": rule["id"], "message": rule["message"]})
    return violations


def _run_cycle1(content: str, file_ext: str, context: str, disabled: set) -> list:
    return [
        {**v, "cycle": 1}
        for v in _run_rules(_CYCLE1_RULES, content, file_ext, context, disabled)
    ]


def _run_cycle2(content: str, file_ext: str, context: str, disabled: set) -> list:
    return [
        {**v, "cycle": 2}
        for v in _run_rules(_CYCLE2_RULES, content, file_ext, context, disabled)
    ]


def _extract_claims(content: str) -> list:
    claims = []
    seen: set[str] = set()
    for pattern in _CLAIM_PATTERNS:
        for m in re.finditer(pattern, content):
            key = f"{m.start()}:{m.group()}"
            if key not in seen:
                seen.add(key)
                claims.append({"text": m.group(), "index": m.start()})
    return claims


def _has_nearby_source(content: str, claim_index: int) -> bool:
    start = max(0, claim_index - _SOURCE_PROXIMITY)
    end = min(len(content), claim_index + _SOURCE_PROXIMITY)
    window = content[start:end]
    return any(p.search(window) for p in _SOURCE_PATTERNS)


def _run_cycle4(content: str, file_path: str, disabled: set = None) -> list:
    violations = []
    disabled = disabled or set()

    if not content or not isinstance(content, str):
        return violations

    if "no-vague-claims" not in disabled:
        m = _VAGUE_PATTERN.search(content)
        if m:
            violations.append({
                "cycle": 4,
                "rule_id": "no-vague-claims",
                "message": (
                    'Research file contains vague language (e.g. "studies show", "experts say"). '
                    "Replace with specific, sourced claims: name the study, author, institution, "
                    f'and year, then link the source.\n\nFound: "{m.group()}"'
                ),
            })
            return violations  # instant block

    claims = _extract_claims(content)
    if not claims:
        return violations

    has_tag = _VERIFICATION_TAG in content

    if not has_tag and "no-unverified-claims" not in disabled:
        violations.append({
            "cycle": 4,
            "rule_id": "no-unverified-claims",
            "message": (
                f"Research file contains statistical or factual claims but is missing the "
                f"{_VERIFICATION_TAG} tag. Verify all claims using Perplexity MCP tools "
                f"and add the tag to confirm verification.\n\nFound {len(claims)} claim(s)."
            ),
        })
        return violations

    if has_tag and "no-unsourced-claims" not in disabled:
        unsourced = [c for c in claims if not _has_nearby_source(content, c["index"])]
        if unsourced:
            violations.append({
                "cycle": 4,
                "rule_id": "no-unsourced-claims",
                "message": (
                    f"Research file has the {_VERIFICATION_TAG} tag but some claims lack a "
                    "source URL within 300 characters. Add a markdown link, bare URL, or "
                    f"[Source:]/[Ref:]/[Verified:] marker near each claim.\n\n"
                    f"Found {len(unsourced)} unsourced claim(s)."
                ),
            })

    return violations


# Cycle 4 rule definitions — mirrors getAllCycle4Rules() in research-verifier.mjs
_CYCLE4_RULES = [
    {"id": "no-vague-claims", "description": 'Block vague unsourced language like "studies show", "experts say"', "applies_to": "research-md"},
    {"id": "no-unverified-claims", "description": "Block statistical/factual claims without PERPLEXITY_VERIFIED tag", "applies_to": "research-md"},
    {"id": "no-unsourced-claims", "description": "Block claims that lack a nearby source URL (within 300 chars)", "applies_to": "research-md"},
]


def get_all_cycle4_rules() -> list:
    """Return all Cycle 4 rule definitions (mirrors getAllCycle4Rules() in JS)."""
    return [dict(r) for r in _CYCLE4_RULES]


# ─── Content Extraction ───────────────────────────────────────────────────────

def _get_file_ext(file_path: str) -> str:
    if not file_path:
        return ""
    suffix = Path(file_path).suffix
    return suffix.lower() if suffix else ""


def _is_research_file(file_path: str) -> bool:
    if not file_path or not isinstance(file_path, str):
        return False
    normalized = file_path.replace("\\", "/").lower()
    if not normalized.endswith(".md"):
        return False
    file_name = normalized.split("/")[-1]
    return (
        "/research/" in normalized
        or normalized.startswith("research/")
        or "research" in file_name
    )


def _extract_content(tool_name: str, tool_input: dict) -> tuple[str, str, str, str]:
    """
    Returns (content, context, file_ext, file_path).
    Mirrors the logic in pre-tool-gate.mjs extractContent().
    """
    name = tool_name.lower()
    file_path = tool_input.get("file_path", "")

    if name == "write":
        return tool_input.get("content", ""), "file-write", _get_file_ext(file_path), file_path

    if name == "edit":
        return tool_input.get("new_string", ""), "file-write", _get_file_ext(file_path), file_path

    if name == "bash":
        return tool_input.get("command", ""), "bash", "", ""

    if name in ("webfetch", "websearch"):
        return tool_input.get("url", tool_input.get("query", "")), "web", "", ""

    if name.startswith("mcp__") or name.startswith("mcp_"):
        # Concatenate all string values from the tool input
        values = "\n".join(v for v in tool_input.values() if isinstance(v, str))
        return values, "mcp", "", ""

    return "", "unknown", "", ""


# ─── Config ───────────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    if not isinstance(override, dict):
        return base
    if not isinstance(base, dict):
        return override
    result = dict(base)
    for key, val in override.items():
        if (
            isinstance(val, dict)
            and isinstance(result.get(key), dict)
        ):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def _load_json_file(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[quadruple-verify] Config warning: {path}: {e}", file=sys.stderr)
    return {}


def _load_config(plugin_root: Path | None = None) -> dict:
    defaults: dict = {}
    if plugin_root:
        defaults = _load_json_file(plugin_root / "config" / "default-rules.json")

    user_config = _load_json_file(
        Path.home() / ".claude" / "quadruple-verify-config.json"
    )

    project_root = Path.cwd()
    project_config = _load_json_file(
        project_root / ".claude" / "quadruple-verify-config.json"
    )

    return _deep_merge(_deep_merge(defaults, user_config), project_config)


# ─── Audit Logger ─────────────────────────────────────────────────────────────

_session_id: str | None = None


def _get_session_id() -> str:
    global _session_id
    if _session_id is None:
        _session_id = os.environ.get("CLAUDE_SESSION_ID") or f"session-{int(datetime.now().timestamp() * 1000)}"
    return _session_id


def _get_audit_path(config: dict) -> Path:
    audit_cfg = config.get("audit", {})
    if audit_cfg.get("logDir"):
        return Path(audit_cfg["logDir"])

    project_claude = Path.cwd() / ".claude"
    if project_claude.exists():
        return project_claude / "quadruple-verify-audit"

    return Path.home() / ".claude" / "quadruple-verify-audit"


def _log_entry(event: str, tool: str, decision: str, violations: list, metadata: dict, config: dict) -> None:
    if not config.get("audit", {}).get("enabled", True):
        return
    try:
        audit_dir = _get_audit_path(config)
        audit_dir.mkdir(parents=True, exist_ok=True)
        log_file = audit_dir / f"{_get_session_id()}.jsonl"
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sessionId": _get_session_id(),
            "event": event,
            "tool": tool,
            "decision": decision,
            "violations": violations,
            "metadata": metadata,
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[quadruple-verify] Audit log error: {e}", file=sys.stderr)


def _log_pre_tool(tool: str, decision: str, violations: list = None, metadata: dict = None, config: dict = None) -> None:
    _log_entry("pre-tool", tool, decision, violations or [], metadata or {}, config or {})


def _log_post_tool(tool: str, metadata: dict = None, config: dict = None) -> None:
    _log_entry("post-tool", tool, "log-only", [], metadata or {}, config or {})


def _log_stop(decision: str, metadata: dict = None, config: dict = None) -> None:
    _log_entry("stop", "Stop", decision, [], metadata or {}, config or {})


# ─── Hook Callbacks ───────────────────────────────────────────────────────────

def _make_pre_tool_hook(config: dict):
    disabled = set(config.get("disabledRules", []))
    cycle1_on = config.get("cycle1", {}).get("enabled", True)
    cycle2_on = config.get("cycle2", {}).get("enabled", True)
    cycle4_on = config.get("cycle4", {}).get("enabled", True)

    async def pre_tool_hook(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict:
        try:
            tool_name = input_data.get("tool_name", "")
            tool_input = input_data.get("tool_input", {})
            event_name = input_data.get("hook_event_name", "PreToolUse")

            content, ctx, file_ext, file_path = _extract_content(tool_name, tool_input)

            if not content:
                _log_entry("pre-tool", tool_name, "approve", [], {"reason": "no-content"}, config)
                return {}

            violations: list = []

            if _is_research_file(file_path) and cycle4_on:
                violations = _run_cycle4(content, file_path, disabled)
            else:
                if cycle1_on:
                    violations += _run_cycle1(content, file_ext, ctx, disabled)
                if cycle2_on:
                    violations += _run_cycle2(content, file_ext, ctx, disabled)

            if violations:
                reasons = "\n\n".join(
                    f"[Cycle {v['cycle']} - {v['rule_id']}] {v['message']}"
                    for v in violations
                )
                reason_text = (
                    f"Quadruple Verification BLOCKED this operation:\n\n{reasons}"
                    "\n\nFix these issues and try again."
                )
                _log_entry("pre-tool", tool_name, "block", violations, {"file_ext": file_ext, "context": ctx}, config)
                return {
                    "hookSpecificOutput": {
                        "hookEventName": event_name,
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason_text,
                    }
                }

            _log_entry("pre-tool", tool_name, "approve", [], {"file_ext": file_ext, "context": ctx}, config)
            return {}

        except Exception as e:
            # Fail open — never block Claude on a hook crash
            print(f"[quadruple-verify] pre-tool error (fail-open): {e}", file=sys.stderr)
            return {}

    return pre_tool_hook


def _make_post_tool_hook(config: dict):
    async def post_tool_hook(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict:
        try:
            tool_name = input_data.get("tool_name", "")
            _log_entry("post-tool", tool_name, "log-only", [], {}, config)
        except Exception as e:
            print(f"[quadruple-verify] post-tool error: {e}", file=sys.stderr)
        return {}

    return post_tool_hook


def _make_stop_hook(config: dict):
    cycle4_on = config.get("cycle4", {}).get("enabled", True)
    disabled = set(config.get("disabledRules", []))

    async def stop_hook(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict:
        try:
            event_name = input_data.get("hook_event_name", "Stop")

            if not cycle4_on:
                _log_entry("stop", "Stop", "approve", [], {}, config)
                return {}

            project_root = Path.cwd()
            search_dirs = [
                project_root / "docs" / "research",
                project_root / "research",
                project_root / "docs",
            ]

            all_violations = []

            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                for md_file in _find_markdown_files(search_dir, max_depth=5):
                    if not _is_research_file(str(md_file)):
                        continue
                    try:
                        content = md_file.read_text(encoding="utf-8")
                        file_violations = _run_cycle4(content, str(md_file), disabled)
                        if file_violations:
                            all_violations.append({"file": str(md_file), "violations": file_violations})
                    except Exception:
                        pass  # skip unreadable files

            if all_violations:
                summary_parts = []
                for item in all_violations:
                    msgs = "\n".join(
                        f"  [Cycle {v['cycle']} - {v['rule_id']}] {v['message']}"
                        for v in item["violations"]
                    )
                    summary_parts.append(f"File: {item['file']}\n{msgs}")
                summary = "\n\n".join(summary_parts)
                reason = (
                    f"Quadruple Verification BLOCKED session completion:\n\n{summary}"
                    "\n\nFix these research file issues before completing."
                )
                _log_entry("stop", "Stop", "block", all_violations, {}, config)
                return {
                    "hookSpecificOutput": {
                        "hookEventName": event_name,
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }

            _log_entry("stop", "Stop", "approve", [], {}, config)
            return {}

        except Exception as e:
            print(f"[quadruple-verify] stop error (fail-open): {e}", file=sys.stderr)
            return {}

    return stop_hook


def _find_markdown_files(directory: Path, max_depth: int, _depth: int = 0) -> list[Path]:
    if _depth >= max_depth:
        return []
    results = []
    try:
        for entry in directory.iterdir():
            if entry.name == "node_modules" or entry.name.startswith("."):
                continue
            if entry.is_dir():
                results.extend(_find_markdown_files(entry, max_depth, _depth + 1))
            elif entry.is_file() and entry.suffix == ".md":
                results.append(entry)
    except Exception:
        pass
    return results


# ─── Cycle 3: Stop Quality Prompt ─────────────────────────────────────────────

CYCLE3_SYSTEM_MESSAGE = """\
MANDATORY — You MUST display the Quadruple Verification Quality Gateway at the END of every response. No exceptions.

After your complete response, add this section:

---
**Quadruple Verification — Quality Gateway**

| Check | Status |
|-------|--------|
| **Completeness** — Fully addressed what was asked? No placeholders, stubs, or TODOs? | PASS or FAIL |
| **Quality** — Production-ready? Proper error handling, edge cases considered? | PASS or FAIL |
| **Correctness** — Solves the actual problem? No logical errors? | PASS or FAIL |
| **Security** — No hardcoded secrets, injection risks, or unsafe patterns? | PASS or FAIL |

Replace each status with the actual result. If ANY check is FAIL, fix the issues BEFORE presenting your response.

For simple conversational answers without code or research, display a condensed single-line: **Quadruple Verification: All checks passed**\
"""


# ─── Public API ───────────────────────────────────────────────────────────────

def make_hooks(plugin_root: str | Path | None = None) -> dict:
    """
    Build and return the hooks dict ready to pass to ClaudeAgentOptions.

    Usage:
        from quadruple_verification import make_hooks
        from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

        options = ClaudeAgentOptions(hooks=make_hooks())

    Args:
        plugin_root: Optional path to the JS repo root, used to load
                     default-rules.json. If None, only user/project
                     config files are loaded.
    """
    config = _load_config(Path(plugin_root) if plugin_root else None)

    # Lazy import so this file has no hard dependency on the SDK at import time
    try:
        from claude_agent_sdk import HookMatcher  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "claude_agent_sdk is not installed. "
            "Run: pip install claude-agent-sdk"
        ) from exc

    pre_tool = _make_pre_tool_hook(config)
    post_tool = _make_post_tool_hook(config)
    stop = _make_stop_hook(config)

    hooks: dict = {
        "PreToolUse": [HookMatcher(hooks=[pre_tool])],
        "PostToolUse": [HookMatcher(hooks=[post_tool])],
    }

    # Cycle 3 — inject quality gateway prompt into Stop hook
    cycle3_on = config.get("cycle3", {}).get("enabled", True)

    async def stop_with_cycle3(input_data, tool_use_id, context):
        result = await stop(input_data, tool_use_id, context)
        if cycle3_on:
            # Attach the quality gateway prompt as a system message
            result["systemMessage"] = CYCLE3_SYSTEM_MESSAGE
        return result

    hooks["Stop"] = [HookMatcher(hooks=[stop_with_cycle3])]

    return hooks
