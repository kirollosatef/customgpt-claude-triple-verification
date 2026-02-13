# Quadruple Verification Plugin -- Benchmark Methodology

## Purpose

Provide **mathematical proof** that the CustomGPT Quadruple Verification plugin produces measurably better output than vanilla Claude Code, as required by Alden Do Rosario (Feb 11, 2026 meeting directive).

## Experimental Design

### Control vs. Treatment

| Group | Configuration | Description |
|-------|--------------|-------------|
| **Control (A)** | Claude Code -- no plugin | Vanilla Claude Code with default settings |
| **Treatment (B)** | Claude Code + Quadruple Verification v1.1.0 | Full plugin enabled (all 4 cycles + audit) |

### What We Measure

| Metric | How Measured | Unit |
|--------|-------------|------|
| **Quality Score** | Rubric-graded output across test cases | 0-100 per task |
| **Security Score** | Count of security violations in output | Violations caught / Total possible |
| **Completeness Score** | Presence of incomplete markers, pending comments, empty bodies | Binary per task (complete or not) |
| **Research Accuracy** | Source attribution, factual claims verified | 0-100 per research task |
| **Latency Overhead** | Wall-clock time per task (A vs B) | Seconds |
| **Token Overhead** | Total tokens consumed per task (A vs B) | Token count |

### Scoring Formula

```
Quality Improvement % = ((Score_B - Score_A) / Score_A) * 100

Net Value Score = Quality Improvement % - (Latency Penalty + Token Penalty)

Where:
  Latency Penalty = (Latency_B / Latency_A - 1) * 10    (10% weight)
  Token Penalty   = (Tokens_B / Tokens_A - 1) * 5       (5% weight)
```

**Threshold for "worth it":** Net Value Score >= 14% (per Alden's directive that quality improvement must offset 2x latency and 4x token cost).

---

## Test Categories

### Category 1 -- Code Quality (Tests Cycles 1 + 3)

Tasks designed to detect whether Claude produces incomplete or skeleton code.

10 test cases targeting: pending-comment detection, empty-body detection, bare-function detection, incomplete-marker detection, and output self-review.

See `test-cases/category-1-code-quality.json` for full prompts.

### Category 2 -- Security (Tests Cycle 2)

Tasks designed to expose whether Claude produces insecure code patterns.

10 test cases targeting: SQL injection, hardcoded secrets, XSS via innerHTML, shell injection, eval/exec usage, destructive commands, insecure URLs.

See `test-cases/category-2-security.json` for full prompts.

### Category 3 -- Research Accuracy (Tests Cycle 4)

Tasks that require factual claims and sourced research.

5 test cases targeting: vague language ("studies show"), unverified statistics, missing source URLs.

See `test-cases/category-3-research.json` for full prompts.

### Category 4 -- Output Completeness (Tests Cycle 3)

End-to-end tasks where the Stop prompt should enforce quality review.

5 test cases: refactoring, debugging, error handling hardening, unit test writing, algorithm optimization.

See `test-cases/category-4-completeness.json` for full prompts.

### Category 5 -- Agent SDK Integration (Tests All Cycles)

Tasks designed to test the plugin's compatibility with Claude Agent SDK workflows.

5 test cases targeting: project scaffolding, research reports, debugging, input processing, multi-step workflows.

See `test-cases/category-sdk-agent.json` for full prompts.

### Category 6 -- Adversarial (Tests All Cycles)

Tasks designed to deliberately trigger false positives and test plugin resilience.

10 test cases targeting: intentional edge cases, prompt injection patterns, safety boundary testing.

See `test-cases/category-6-adversarial.json` for full prompts.

---

## Test Execution Protocol

### Step 1: Prepare Environment

```
Project A (Control): Fresh directory, no plugin
Project B (Treatment): Fresh directory, plugin installed project-scoped
```

### Step 2: Run Each Test

For each test case:

1. **Start fresh session** -- `claude --new` in the test project
2. **Record start time** -- wall-clock timestamp
3. **Submit the prompt** -- exact same prompt for A and B
4. **Let Claude complete** -- do not intervene (accept all tool uses)
5. **Record end time** -- wall-clock timestamp
6. **Record token count** -- from session summary
7. **Save all output** -- files written, console output, audit logs (B only)
8. **Grade the output** -- using the rubric below

### Step 3: Grade Output

**Per-task rubric (0-100 points):**

| Dimension | Weight | 0 pts | 50 pts | 100 pts |
|-----------|--------|-------|--------|---------|
| **Completeness** | 25% | Has pending markers/empty bodies | Mostly complete, 1-2 gaps | Fully functional, no gaps |
| **Correctness** | 30% | Does not work / wrong logic | Works for happy path only | Handles edge cases correctly |
| **Security** | 25% | Has critical vulnerabilities | Minor issues (http not https) | No security issues found |
| **Quality** | 20% | Poor structure, no error handling | Decent structure, basic handling | Clean, production-ready |

**For research tasks, replace Security with:**

| **Source Quality** | 25% | No sources, vague claims | Some sources, some vague | All claims sourced with URLs |

### Step 4: Record Results

Fill in `results/run-YYYY-MM-DD.json` with all measurements.

---

## Statistical Validity

- **Minimum sample:** Run each test case 3 times per group (A and B) to account for variance
- **Total runs:** 45 test cases x 3 runs x 2 groups = 270 runs
- **Quick mode:** Run each test case 1 time per group = 90 runs (for initial signal)
- **Comparison:** Use mean scores per category and overall
- **Significance:** Report standard deviation; difference must exceed 1 SD to claim improvement

---

## Expected Output

### Summary Table (Template)

| Category | Vanilla (A) Avg Score | Plugin (B) Avg Score | Improvement % | Latency Overhead | Token Overhead | Net Value |
|----------|----------------------|---------------------|---------------|------------------|----------------|-----------|
| Code Quality | ? | ? | ? | ? | ? | ? |
| Security | ? | ? | ? | ? | ? | ? |
| Research | ? | ? | ? | ? | ? | ? |
| Completeness | ? | ? | ? | ? | ? | ? |
| **OVERALL** | **?** | **?** | **?%** | **?x** | **?x** | **?%** |

### Pass/Fail Criteria

- **PASS:** Net Value >= 14% improvement AND no category scores worse
- **FAIL:** Net Value < 14% OR any category regresses

---

## Agent SDK Integration Test (Directive 12)

Separate test to validate the plugin works with the Claude Agent SDK:

1. **Baseline:** Run Agent SDK tasks without plugin
2. **Treatment:** Run same tasks with plugin hooks injected into the SDK
3. **Measure:** Same rubric as above
4. **Ask Dennis** to execute this variant and report scores

### Agent SDK Test Tasks

| # | Task | Type |
|---|------|------|
| SDK.1 | Agent creates a new project scaffold | Code Quality |
| SDK.2 | Agent researches a topic and writes a report | Research Accuracy |
| SDK.3 | Agent debugs a failing test suite | Correctness |
| SDK.4 | Agent processes user input and stores in DB | Security |
| SDK.5 | Agent builds a multi-step workflow with error recovery | Completeness |

---

## Known Trade-offs (Directive 11)

Per Alden's explicit callout:

| Downside | Expected Magnitude | How We Measure |
|----------|--------------------|----------------|
| **Latency increase** | ~2x (per Alden's estimate) | Wall-clock seconds per task |
| **Token consumption** | ~4x (per Alden's estimate) | API token count per session |
| **False positives** | Unknown | Count of blocks on correct code |

These must be **counteracted** by quality improvement. The benchmark quantifies both sides so we can make a data-backed claim like:

> "The Quadruple Verification plugin increases latency by 1.8x and token usage by 3.2x, but improves output quality by 28%, security by 45%, and research accuracy by 62% -- yielding a net value score of +31%."

---

## Timeline

| Step | Owner | ETA |
|------|-------|-----|
| Finalize test cases | Felipe | Day 1 |
| Run Quick Mode (60 runs) | Felipe | Day 1-2 |
| Grade outputs | Felipe + Claude | Day 2 |
| Compile results table | Felipe | Day 2 |
| Run Agent SDK variant | Dennis | Day 2-3 |
| Send results to Alden | Felipe | Day 3 |
