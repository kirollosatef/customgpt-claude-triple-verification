import re
import json
from pathlib import Path

_PATTERNS_FILE = Path(__file__).parent / "safety_patterns.json"
_BUILTIN_CHECKS = None


def _load_patterns():
    global _BUILTIN_CHECKS
    if _BUILTIN_CHECKS is None:
        with open(_PATTERNS_FILE, "r", encoding="utf-8") as f:
            _BUILTIN_CHECKS = json.load(f)
    return _BUILTIN_CHECKS


def safety_scan(output_text, test_case):
    """Scan output for dangerous code patterns using regex.

    Returns a list of safety violation dicts with rule name and matched snippet.
    This measures the safety gap: dangerous patterns that vanilla ships
    but the plugin would have caught.
    """
    violations = []

    # Check custom patterns from test case definition
    custom_patterns = test_case.get("safety_patterns_to_detect", [])
    for pattern in custom_patterns:
        if pattern in output_text:
            idx = output_text.index(pattern)
            snippet = output_text[max(0, idx - 30):idx + len(pattern) + 30]
            violations.append({
                "rule": "custom-pattern",
                "pattern": pattern,
                "snippet": snippet.strip()
            })

    # Built-in dangerous pattern checks
    for rule_name, pattern, description in _load_patterns():
        try:
            matches = list(re.finditer(pattern, output_text, re.IGNORECASE))
        except re.error:
            continue
        for m in matches[:3]:  # Cap at 3 matches per rule
            start = max(0, m.start() - 20)
            end = min(len(output_text), m.end() + 20)
            violations.append({
                "rule": rule_name,
                "description": description,
                "snippet": output_text[start:end].strip()
            })

    return violations
