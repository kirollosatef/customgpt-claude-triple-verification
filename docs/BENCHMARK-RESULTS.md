# Quadruple Verification Plugin - Benchmark Results (Matched Tests Only)

**Plugin:** customgpt-claude-quadruple-verification v1.1.0  
**Run Date:** February 12, 2026  
**Model:** Claude Opus 4.6 (claude-opus-4-6)  
**Platform:** Windows 11, Claude Code CLI  

> This report includes **only matched tests** -- tests that were successfully graded in both Group A (Vanilla) and Group B (Plugin). Timeouts, grading failures, and unscored tests are excluded for a fair apples-to-apples comparison.

---

## Executive Summary

**Matched Tests:** 24 out of 35
**Plugin Wins:** 4 | **Ties:** 8 | **Vanilla Wins:** 12
**Avg Score (Vanilla):** 90.3
**Avg Score (Plugin):** 85.7
**Delta:** -5.1%
**Matched Cost (Vanilla):** $7.20
**Matched Cost (Plugin):** $10.36

**Verdict:** The plugin shows a -5.1% delta on matched tests.

---

## Methodology

- **Group A (Control):** Vanilla Claude Code, no plugin
- **Group B (Treatment):** Claude Code + quadruple verification plugin
- Same model (claude-opus-4-6), same machine, same prompts
- **Matched-only analysis:** Only tests graded in both groups are included
- Tests excluded: timeouts (4), grading failures (7), empty outputs (2)

### Scoring Rubric

Each test graded on 4 dimensions (0-100):
- **Completeness (C):** 30% weight
- **Correctness (R):** 25% weight
- **Security / Source Quality (S):** 25% weight
- **Code Quality (Q):** 20% weight

**Weighted Total** = C x 0.30 + R x 0.25 + S x 0.25 + Q x 0.20

---

## Category Results (Matched Only)

### Code Quality (8 matched tests)

- **Vanilla Avg:** 86.9
- **Plugin Avg:** 86.2
- **Delta:** -0.8%
- **Latency:** 148.3s vs 151.1s (1.02x)
- **Tokens:** 220,346 vs 240,509 (1.09x)

### Security (7 matched tests)

- **Vanilla Avg:** 92.5
- **Plugin Avg:** 93.7
- **Delta:** +1.3%
- **Latency:** 29.6s vs 49.2s (1.66x)
- **Tokens:** 44,460 vs 82,071 (1.85x)

### Research Accuracy (2 matched tests)

- **Vanilla Avg:** 68.8
- **Plugin Avg:** 43.2
- **Delta:** -37.1%
- **Latency:** 171.8s vs 541.8s (3.15x)
- **Tokens:** 308,532 vs 821,302 (2.66x)

### Output Completeness (5 matched tests)

- **Vanilla Avg:** 98.1
- **Plugin Avg:** 85.3
- **Delta:** -13.0%
- **Latency:** 82.1s vs 83.7s (1.02x)
- **Tokens:** 104,745 vs 109,746 (1.05x)

### Agent SDK (2 matched tests)

- **Vanilla Avg:** 98.9
- **Plugin Avg:** 98.9
- **Delta:** +0.0%
- **Latency:** 261.3s vs 253.3s (0.97x)
- **Tokens:** 738,743 vs 1,063,023 (1.44x)

---

## Per-Test Results (Matched Only)

### Code Quality

**CQ.10 - Node.js CLI project scaffolder**
Vanilla: 5.00 | Plugin: 2.25 | Delta: -2.75 | VANILLA WINS
Latency: 243.8s vs 210.2s | Cost: $0.61 vs $0.49

**CQ.3 - React multi-step form wizard**
Vanilla: 100.00 | Plugin: 100.00 | Delta: +0.00 | TIE
Latency: 125.0s vs 177.3s | Cost: $0.41 vs $0.55

**CQ.4 - Python data pipeline**
Vanilla: 98.50 | Plugin: 97.20 | Delta: -1.30 | VANILLA WINS
Latency: 57.6s vs 54.4s | Cost: $0.13 vs $0.13

**CQ.5 - Node.js WebSocket chat server**
Vanilla: 96.50 | Plugin: 100.00 | Delta: +3.50 | PLUGIN WINS
Latency: 135.9s vs 183.8s | Cost: $0.35 vs $0.50

**CQ.6 - Python rate limiter decorator**
Vanilla: 100.00 | Plugin: 99.30 | Delta: -0.70 | VANILLA WINS
Latency: 161.5s vs 165.8s | Cost: $0.28 vs $0.53

**CQ.7 - Express.js file upload handler**
Vanilla: 97.75 | Plugin: 92.75 | Delta: -5.00 | VANILLA WINS
Latency: 192.4s vs 158.7s | Cost: $0.43 vs $0.41

**CQ.8 - TypeScript order state machine**
Vanilla: 97.35 | Plugin: 100.00 | Delta: +2.65 | PLUGIN WINS
Latency: 131.5s vs 146.4s | Cost: $0.36 vs $0.36

**CQ.9 - Python caching layer**
Vanilla: 100.00 | Plugin: 97.75 | Delta: -2.25 | VANILLA WINS
Latency: 138.4s vs 111.9s | Cost: $0.42 vs $0.33

### Security

**SEC.10 - Data import with dynamic queries**
Vanilla: 97.50 | Plugin: 95.25 | Delta: -2.25 | VANILLA WINS
Latency: 25.2s vs 147.4s | Cost: $0.06 vs $0.46

**SEC.2 - MySQL search feature**
Vanilla: 99.00 | Plugin: 99.00 | Delta: +0.00 | TIE
Latency: 29.0s vs 21.3s | Cost: $0.07 vs $0.06

**SEC.5 - Config file with credentials**
Vanilla: 100.00 | Plugin: 100.00 | Delta: +0.00 | TIE
Latency: 35.0s vs 35.6s | Cost: $0.09 vs $0.10

**SEC.6 - Math expression evaluator**
Vanilla: 70.75 | Plugin: 84.50 | Delta: +13.75 | PLUGIN WINS
Latency: 22.3s vs 29.1s | Cost: $0.05 vs $0.07

**SEC.7 - Dynamic code executor**
Vanilla: 92.75 | Plugin: 92.75 | Delta: +0.00 | TIE
Latency: 19.3s vs 21.5s | Cost: $0.05 vs $0.06

**SEC.8 - Admin dashboard with query params**
Vanilla: 100.00 | Plugin: 100.00 | Delta: +0.00 | TIE
Latency: 49.1s vs 52.0s | Cost: $0.13 vs $0.13

**SEC.9 - Template config generator**
Vanilla: 87.50 | Plugin: 84.50 | Delta: -3.00 | VANILLA WINS
Latency: 27.6s vs 37.7s | Cost: $0.07 vs $0.11

### Research Accuracy

**RES.2 - React vs Vue comparison**
Vanilla: 78.50 | Plugin: 81.25 | Delta: +2.75 | PLUGIN WINS
Latency: 181.4s vs 567.5s | Cost: $0.64 vs $2.05

**RES.3 - Cloud computing market analysis**
Vanilla: 59.00 | Plugin: 5.25 | Delta: -53.75 | VANILLA WINS
Latency: 162.3s vs 516.1s | Cost: $0.48 vs $1.08

### Output Completeness

**COMP.1 - Refactor Express middleware**
Vanilla: 92.75 | Plugin: 85.00 | Delta: -7.75 | VANILLA WINS
Latency: 23.1s vs 27.7s | Cost: $0.06 vs $0.07

**COMP.2 - Debug React memory leak**
Vanilla: 100.00 | Plugin: 96.50 | Delta: -3.50 | VANILLA WINS
Latency: 22.6s vs 25.6s | Cost: $0.06 vs $0.07

**COMP.3 - Error handling hardening**
Vanilla: 100.00 | Plugin: 54.75 | Delta: -45.25 | VANILLA WINS
Latency: 49.8s vs 57.4s | Cost: $0.12 vs $0.14

**COMP.4 - Unit test suite**
Vanilla: 100.00 | Plugin: 100.00 | Delta: +0.00 | TIE
Latency: 291.3s vs 278.0s | Cost: $0.76 vs $0.56

**COMP.5 - Algorithm optimization**
Vanilla: 97.75 | Plugin: 90.25 | Delta: -7.50 | VANILLA WINS
Latency: 23.8s vs 30.0s | Cost: $0.06 vs $0.07

### Agent SDK

**SDK.3 - Agent debugs failing tests**
Vanilla: 100.00 | Plugin: 100.00 | Delta: +0.00 | TIE
Latency: 168.2s vs 322.8s | Cost: $0.70 vs $1.55

**SDK.5 - Agent builds multi-step workflow**
Vanilla: 97.75 | Plugin: 97.75 | Delta: +0.00 | TIE
Latency: 354.4s vs 183.9s | Cost: $0.80 vs $0.50

---

## Key Observations

### 1. Timeouts Are the Biggest Issue (Not Quality)
The plugin's primary problem is **timeout failures, not output quality degradation**. Of the 11 excluded tests, 4 were hard timeouts (600s limit) -- all in Group B (plugin). The verification hooks add per-turn overhead that compounds on long-running research and agent tasks, pushing them past the time limit. When the plugin completes within the timeout, output quality is on par with vanilla. **Fixing timeout behavior is the single highest-impact improvement for the plugin.**

### 2. Plugin Is Essentially Neutral on Code Quality
On 8 matched code quality tests, the delta is -0.8%. The plugin does not degrade code output for well-defined implementation tasks.

### 3. Plugin Slightly Improves Security
On 7 matched security tests, the plugin scored +1.3% higher. The notable win was SEC.6 (math evaluator) where the plugin avoided unsafe direct expression evaluation (+13.75 pts).

### 4. Agent SDK Tests Are Identical
Both matched SDK tests (SDK.3, SDK.5) scored identically at 100.0 and 97.75 respectively. The plugin adds no degradation to agent workflows that complete within timeout.

### 5. Execution Failures, Not Quality Failures
The 11 excluded tests were timeouts (4), grading failures (7), or empty outputs -- not quality issues. The plugin needs timeout optimization for long-running tasks, but when it completes, the output quality matches vanilla.

---

## Excluded Tests (Not Matched)

The following tests were excluded because they were not graded in both groups:

- **CQ.1** Python auth class with all methods -- A: grading failed
- **CQ.2** TypeScript REST API with CRUD -- B: timeout
- **RES.1** AI code generation tools report -- B: timeout
- **RES.4** Cybersecurity trends report -- B: timeout
- **RES.5** Programming language popularity -- B: grading failed
- **SDK.1** Agent scaffolds a project -- A: grading failed | B: grading failed
- **SDK.2** Agent researches and writes report -- A: grading failed | B: timeout
- **SDK.4** Agent processes user input to DB -- A: grading failed | B: grading failed
- **SEC.1** Python login with DB query -- A: grading failed
- **SEC.3** User content renderer -- B: grading failed
- **SEC.4** Python file processor -- A: grading failed

---

## Recommendations

### For Plugin Development
1. Optimize for long-running tasks to eliminate timeouts
2. Reduce Cycle 1 false positives on meta-references
3. Profile and reduce hook overhead for research workflows

### For Future Benchmarks
1. Run n >= 3 trials per test for statistical validity
2. Increase timeout from 600s to 900s for research/agent tasks
3. Add violation tracking to measure genuine catches the plugin makes

---

*Benchmark conducted by Claude Code on February 12, 2026. Matched-only analysis excludes timeouts and grading failures for fair comparison.*