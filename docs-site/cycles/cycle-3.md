# Cycle 3 — Output Quality

<span class="badge badge-cycle3">Stop Hook</span> <span class="badge badge-block">Prompt-based review</span>

Cycle 3 runs before Claude finishes responding (the **Stop** hook event). Instead of pattern matching, it uses a prompt-based review — asking Claude to self-verify its output meets quality standards.

## Why This Matters

Pattern matching (Cycles 1 and 2) catches known bad patterns, but can't evaluate whether the overall response is complete, correct, and production-ready. Cycle 3 fills this gap with a second AI review pass.

## How It Works

When Claude is about to finish responding, the Stop hook injects a review prompt. Claude then evaluates its own output against five criteria:

| Check | What It Verifies |
|-------|-----------------|
| **Completeness** | All requirements implemented, no stubs or placeholders left behind |
| **Quality** | Production-ready code with proper error handling |
| **Correctness** | Logic is sound, implementation actually solves the problem |
| **Security** | No hardcoded secrets or injection risks |
| **Tests** | If tests were expected, they exist and are meaningful |

## Quality Gateway Display

Cycle 3 produces a visible **Quality Gateway** table at the end of each Claude response:

```
┌─────────────────────────────────────────┐
│            QUALITY GATEWAY              │
├──────────────┬──────────────────────────┤
│ Completeness │ PASS                     │
│ Quality      │ PASS                     │
│ Correctness  │ PASS                     │
│ Security     │ PASS                     │
├──────────────┴──────────────────────────┤
│ Status: APPROVED                        │
└─────────────────────────────────────────┘
```

If any check fails, Claude will explain the issue and attempt to fix it before completing the response.

## Key Differences from Other Cycles

| Property | Cycles 1/2/4 | Cycle 3 |
|----------|-------------|---------|
| **Mechanism** | Regex pattern matching | AI self-review prompt |
| **Hook type** | Command (external script) | Prompt (injected text) |
| **Scope** | Specific tool inputs | Entire response |
| **Speed** | <50ms | Adds latency (AI review) |
| **False positives** | Possible (regex limits) | Rare (contextual understanding) |

## Configuration

Cycle 3 is always active when the plugin is installed. There are no individual rules to disable — it's an all-or-nothing review. The review prompt is defined in the plugin's Stop hook configuration.
