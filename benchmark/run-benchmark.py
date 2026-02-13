#!/usr/bin/env python3
"""
Quadruple Verification Plugin -- Benchmark Runner

Automates the benchmark execution for both Control (vanilla) and Treatment (plugin) groups.
Runs each test case, records timing and token data, and compiles results.

Usage:
    python run-benchmark.py --group A          # Run control group (vanilla)
    python run-benchmark.py --group B          # Run treatment group (plugin)
    python run-benchmark.py --compile          # Compile results from both groups
    python run-benchmark.py --group A --test CQ.1   # Run a single test

Prerequisites:
    - Claude CLI installed and authenticated
    - For Group A: No plugin installed (vanilla)
    - For Group B: customgpt-claude-quadruple-verification plugin installed
    - Python 3.10+
"""

import argparse
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEST_CASES_DIR = BASE_DIR / "test-cases"
RESULTS_DIR = BASE_DIR / "results"


def load_test_cases():
    """Load all test cases from JSON files."""
    all_cases = []
    for json_file in sorted(TEST_CASES_DIR.glob("category-*.json")):
        with open(json_file, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        category = data["category"]
        for tc in data["test_cases"]:
            tc["_category"] = category
            tc["_file"] = json_file.name
            all_cases.append(tc)
    return all_cases


def parse_violations(stderr_text):
    """Parse plugin violation messages from stderr.

    Looks for patterns like:
      [Cycle 2 - no-raw-sql] ...
      Quadruple Verification BLOCKED ...
    Returns a list of rule IDs that were triggered.
    """
    violations = []
    # Match [Cycle N - rule-name] patterns
    for match in re.finditer(r"\[Cycle \d+ - ([a-z0-9-]+)\]", stderr_text):
        rule = match.group(1)
        if rule not in violations:
            violations.append(rule)
    # Also check for generic BLOCKED messages
    if "BLOCKED" in stderr_text and not violations:
        violations.append("blocked-generic")
    return violations


def run_single_test(test_case, group, run_number=1):
    """
    Run a single test case using Claude CLI.
    Returns a result dict with timing, token count, and output.
    """
    test_id = test_case["id"]
    prompt = test_case["prompt"]

    print(f"\n{'='*60}")
    print(f"Running: {test_id} ({test_case['name']})")
    print(f"Group: {'Control (A) - Vanilla' if group == 'A' else 'Treatment (B) - Plugin'}")
    print(f"Run: {run_number}")
    print(f"{'='*60}")

    # Create output directory for this run
    run_dir = RESULTS_DIR / f"group-{group}" / test_id / f"run-{run_number}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save the prompt
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    # Record start time
    start_time = time.time()
    start_iso = datetime.now().isoformat()

    # Run Claude CLI in non-interactive mode
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=900,
            cwd=str(run_dir),
            encoding="utf-8",
            errors="replace"
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = "TIMEOUT: Test exceeded 15 minute limit"
        exit_code = -1
    except FileNotFoundError:
        print("ERROR: 'claude' CLI not found. Make sure it is installed and in PATH.")
        return None

    # Record end time
    end_time = time.time()
    end_iso = datetime.now().isoformat()
    wall_clock = end_time - start_time

    # Parse JSON output for detailed metrics
    token_count = None
    total_cost = None
    api_latency = None
    claude_output = stdout
    num_turns = None
    model_usage = {}
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict):
            claude_output = parsed.get("result", stdout)
            api_latency = parsed.get("duration_api_ms", None)
            total_cost = parsed.get("total_cost_usd", None)
            num_turns = parsed.get("num_turns", None)
            model_usage = parsed.get("modelUsage", {})
            usage = parsed.get("usage", {})
            token_count = (
                usage.get("input_tokens", 0) +
                usage.get("output_tokens", 0) +
                usage.get("cache_creation_input_tokens", 0) +
                usage.get("cache_read_input_tokens", 0)
            )
    except (json.JSONDecodeError, TypeError):
        token_count = None

    # Save outputs
    (run_dir / "stdout.txt").write_text(claude_output, encoding="utf-8")
    (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    if stdout != claude_output:
        (run_dir / "raw-json.json").write_text(stdout, encoding="utf-8")

    # Parse stderr for plugin violation catches (Group B only)
    violations_caught = parse_violations(stderr) if group == "B" else []

    # Build result record
    result_record = {
        "test_id": test_id,
        "test_name": test_case["name"],
        "category": test_case["_category"],
        "group": group,
        "run_number": run_number,
        "start_time": start_iso,
        "end_time": end_iso,
        "latency_seconds": round(wall_clock, 2),
        "api_latency_ms": api_latency,
        "token_count": token_count,
        "total_cost_usd": total_cost,
        "num_turns": num_turns,
        "model_usage": model_usage,
        "exit_code": exit_code,
        "output_path": str(run_dir),
        "scores": {
            "completeness": None,
            "correctness": None,
            "security_or_source_quality": None,
            "quality": None,
            "weighted_total": None
        },
        "violations_caught": violations_caught,
        "notes": ""
    }

    # Save individual result
    with open(run_dir / "result.json", "w", encoding="utf-8") as f:
        json.dump(result_record, f, indent=2)

    cost_str = f"${total_cost:.4f}" if total_cost else "N/A"
    violations_str = f" | Violations: {len(violations_caught)}" if violations_caught else ""
    print(f"  Completed in {wall_clock:.1f}s | Tokens: {token_count or 'N/A'} | Cost: {cost_str} | Exit: {exit_code}{violations_str}")
    return result_record


def run_group(group, test_filter=None, runs=1):
    """Run all (or filtered) test cases for a group."""
    all_cases = load_test_cases()

    if test_filter:
        all_cases = [tc for tc in all_cases if tc["id"] == test_filter]
        if not all_cases:
            print(f"ERROR: Test case '{test_filter}' not found.")
            return []

    print(f"\nBenchmark Group {'A (Control - Vanilla)' if group == 'A' else 'B (Treatment - Plugin)'}")
    print(f"Total test cases: {len(all_cases)}")
    print(f"Runs per test: {runs}")
    print(f"Total runs: {len(all_cases) * runs}")

    results = []
    for tc in all_cases:
        for run_num in range(1, runs + 1):
            result = run_single_test(tc, group, run_num)
            if result:
                results.append(result)

    # Save aggregated results for this group
    group_file = RESULTS_DIR / f"group-{group}-results.json"
    with open(group_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Group {group} complete. {len(results)} runs saved to {group_file}")
    return results


def calculate_weighted_score(scores):
    """Calculate weighted total from dimension scores."""
    if any(v is None for v in [scores.get("completeness"), scores.get("correctness"),
                                scores.get("security_or_source_quality"), scores.get("quality")]):
        return None
    return (
        scores["completeness"] * 0.25 +
        scores["correctness"] * 0.30 +
        scores["security_or_source_quality"] * 0.25 +
        scores["quality"] * 0.20
    )


def compile_results():
    """Compile results from both groups into the final summary."""
    group_a_file = RESULTS_DIR / "group-A-results.json"
    group_b_file = RESULTS_DIR / "group-B-results.json"

    if not group_a_file.exists() or not group_b_file.exists():
        print("ERROR: Both group-A-results.json and group-B-results.json must exist.")
        print("Run both groups first:")
        print("  python run-benchmark.py --group A")
        print("  python run-benchmark.py --group B")
        return

    with open(group_a_file, "r", encoding="utf-8") as f:
        group_a = json.load(f)
    with open(group_b_file, "r", encoding="utf-8") as f:
        group_b = json.load(f)

    # Check for ungraded results
    ungraded_a = [r for r in group_a if r["scores"]["weighted_total"] is None]
    ungraded_b = [r for r in group_b if r["scores"]["weighted_total"] is None]

    if ungraded_a or ungraded_b:
        print(f"WARNING: {len(ungraded_a)} Group A and {len(ungraded_b)} Group B results need grading.")
        print("Edit result.json files to set: completeness, correctness, security_or_source_quality, quality (0-100 each)")
        print()

    # Category mapping (all categories)
    category_map = {
        "Code Quality": "category_1_code_quality",
        "Security": "category_2_security",
        "Research Accuracy": "category_3_research",
        "Output Completeness": "category_4_completeness",
        "Agent SDK Integration": "category_5_agent_sdk",
        "Adversarial": "category_6_adversarial"
    }

    # Build index of scored tests by test_id for matched-only analysis
    a_by_id = {}
    for r in group_a:
        if r["scores"]["weighted_total"] is not None:
            a_by_id[r["test_id"]] = r
    b_by_id = {}
    for r in group_b:
        if r["scores"]["weighted_total"] is not None:
            b_by_id[r["test_id"]] = r

    # Matched tests: scored in BOTH groups
    matched_ids = set(a_by_id.keys()) & set(b_by_id.keys())
    total_a = len(group_a)
    total_b = len(group_b)
    print(f"Matched tests: {len(matched_ids)} of {max(total_a, total_b)}")

    # Violation tracking (Group B only)
    total_violations_b = 0
    tests_with_violations = 0
    all_rules_triggered = []
    for r in group_b:
        v = r.get("violations_caught", [])
        if v:
            total_violations_b += len(v)
            tests_with_violations += 1
            all_rules_triggered.extend(v)

    # Safety scan results (if present)
    a_safety_violations = sum(len(r.get("safety_violations", [])) for r in group_a)
    b_safety_violations = sum(len(r.get("safety_violations", [])) for r in group_b)

    summary = {}
    for cat_name, cat_key in category_map.items():
        # Matched-only: only tests graded in both groups
        cat_matched = [tid for tid in matched_ids
                       if a_by_id[tid]["category"] == cat_name]
        a_matched = [a_by_id[tid] for tid in cat_matched]
        b_matched = [b_by_id[tid] for tid in cat_matched]

        if not a_matched or not b_matched:
            summary[cat_key] = {"status": "incomplete", "matched": 0,
                                "message": f"No matched tests for {cat_name}"}
            continue

        avg_a = sum(r["scores"]["weighted_total"] for r in a_matched) / len(a_matched)
        avg_b = sum(r["scores"]["weighted_total"] for r in b_matched) / len(b_matched)
        improvement = ((avg_b - avg_a) / avg_a * 100) if avg_a > 0 else 0

        avg_lat_a = sum(r["latency_seconds"] for r in a_matched) / len(a_matched)
        avg_lat_b = sum(r["latency_seconds"] for r in b_matched) / len(b_matched)
        lat_ratio = avg_lat_b / avg_lat_a if avg_lat_a > 0 else 0

        tok_a = [r for r in a_matched if r["token_count"] is not None]
        tok_b = [r for r in b_matched if r["token_count"] is not None]
        avg_tok_a = sum(r["token_count"] for r in tok_a) / len(tok_a) if tok_a else 0
        avg_tok_b = sum(r["token_count"] for r in tok_b) / len(tok_b) if tok_b else 0
        tok_ratio = avg_tok_b / avg_tok_a if avg_tok_a > 0 else 0

        # Net Value Score = Quality Improvement % - (Latency Penalty + Token Penalty)
        latency_penalty = (lat_ratio - 1) * 10 if lat_ratio > 1 else 0
        token_penalty = (tok_ratio - 1) * 5 if tok_ratio > 1 else 0
        net_value = improvement - latency_penalty - token_penalty

        # Count violations in this category
        cat_violations = sum(len(b_by_id[tid].get("violations_caught", []))
                            for tid in cat_matched if tid in b_by_id)

        summary[cat_key] = {
            "matched_tests": len(a_matched),
            "avg_score_A": round(avg_a, 1),
            "avg_score_B": round(avg_b, 1),
            "improvement_pct": round(improvement, 1),
            "avg_latency_A": round(avg_lat_a, 1),
            "avg_latency_B": round(avg_lat_b, 1),
            "latency_ratio": round(lat_ratio, 2),
            "avg_tokens_A": round(avg_tok_a),
            "avg_tokens_B": round(avg_tok_b),
            "token_ratio": round(tok_ratio, 2),
            "net_value": round(net_value, 1),
            "violations_caught": cat_violations
        }

    # Overall summary across all categories
    graded_cats = {k: v for k, v in summary.items() if isinstance(v, dict) and "avg_score_A" in v}
    if graded_cats:
        overall_a = sum(v["avg_score_A"] for v in graded_cats.values()) / len(graded_cats)
        overall_b = sum(v["avg_score_B"] for v in graded_cats.values()) / len(graded_cats)
        overall_improvement = ((overall_b - overall_a) / overall_a * 100) if overall_a > 0 else 0
        overall_latency = sum(v["latency_ratio"] for v in graded_cats.values()) / len(graded_cats)
        overall_tokens = sum(v["token_ratio"] for v in graded_cats.values()) / len(graded_cats)
        overall_net = sum(v["net_value"] for v in graded_cats.values()) / len(graded_cats)

        any_regression = any(v["improvement_pct"] < 0 for v in graded_cats.values())
        verdict = overall_net >= 14 and not any_regression

        summary["overall"] = {
            "matched_tests": len(matched_ids),
            "total_tests": max(total_a, total_b),
            "avg_score_A": round(overall_a, 1),
            "avg_score_B": round(overall_b, 1),
            "improvement_pct": round(overall_improvement, 1),
            "latency_overhead": f"{overall_latency:.1f}x",
            "token_overhead": f"{overall_tokens:.1f}x",
            "net_value_score": round(overall_net, 1),
            "verdict": "CLEARED" if verdict else "BELOW_THRESHOLD",
            "any_regression": any_regression,
            "violations": {
                "total_plugin_catches": total_violations_b,
                "tests_with_catches": tests_with_violations,
                "rules_triggered": list(set(all_rules_triggered)),
                "vanilla_safety_violations": a_safety_violations,
                "plugin_safety_violations": b_safety_violations,
                "safety_gap": a_safety_violations - b_safety_violations
            }
        }

    # Save compiled results
    today = datetime.now().strftime("%Y-%m-%d")
    compiled_file = RESULTS_DIR / f"run-{today}.json"
    with open(compiled_file, "w", encoding="utf-8") as f:
        json.dump({"date": today, "summary": summary}, f, indent=2)

    # Print summary table
    print(f"\n{'='*80}")
    print(f"BENCHMARK RESULTS -- {today}")
    print(f"{'='*80}")
    header = f"{'Category':<22} {'Vanilla(A)':>10} {'Plugin(B)':>10} {'Improve%':>10} {'Latency':>8} {'Tokens':>8} {'NetValue':>10}"
    print(header)
    print(f"{'-'*80}")

    for cat_name, cat_key in category_map.items():
        s = summary.get(cat_key, {})
        if "avg_score_A" in s:
            row = f"{cat_name:<22} {s['avg_score_A']:>10.1f} {s['avg_score_B']:>10.1f} {s['improvement_pct']:>9.1f}% {s['latency_ratio']:>7.1f}x {s['token_ratio']:>7.1f}x {s['net_value']:>9.1f}%"
            print(row)
        else:
            print(f"{cat_name:<22} {'(not graded)':>50}")

    if "overall" in summary:
        s = summary["overall"]
        print(f"{'-'*80}")
        overall_row = f"{'OVERALL':<22} {s['avg_score_A']:>10.1f} {s['avg_score_B']:>10.1f} {s['improvement_pct']:>9.1f}% {s['latency_overhead']:>8} {s['token_overhead']:>8} {s['net_value_score']:>9.1f}%"
        print(overall_row)
        print(f"\nVerdict: {s['verdict']} (threshold: Net Value >= 14%)")

    # Print violation tracking
    if "overall" in summary and "violations" in summary["overall"]:
        v = summary["overall"]["violations"]
        print(f"\n{'='*80}")
        print("VIOLATION TRACKING")
        print(f"{'='*80}")
        print(f"  Plugin catches (blocks/corrections): {v['total_plugin_catches']} across {v['tests_with_catches']} tests")
        if v["rules_triggered"]:
            print(f"  Rules triggered: {', '.join(v['rules_triggered'])}")
        print(f"  Safety violations in vanilla output:  {v['vanilla_safety_violations']}")
        print(f"  Safety violations in plugin output:   {v['plugin_safety_violations']}")
        print(f"  Safety gap (vanilla - plugin):        {v['safety_gap']}")

    print(f"\nFull results saved to: {compiled_file}")


def main():
    arg_parser = argparse.ArgumentParser(description="Quadruple Verification Benchmark Runner")
    arg_parser.add_argument("--group", choices=["A", "B"], help="Run tests for group A (control) or B (treatment)")
    arg_parser.add_argument("--test", help="Run a specific test case by ID (e.g., CQ.1)")
    arg_parser.add_argument("--runs", type=int, default=1, help="Number of runs per test (default: 1 for quick mode)")
    arg_parser.add_argument("--compile", action="store_true", help="Compile and summarize results from both groups")
    arg_parser.add_argument("--list", action="store_true", help="List all test cases")

    args = arg_parser.parse_args()

    if args.list:
        cases = load_test_cases()
        for tc in cases:
            print(f"  {tc['id']:<8} {tc['_category']:<22} {tc['name']}")
        print(f"\nTotal: {len(cases)} test cases")
        return

    if args.compile:
        compile_results()
        return

    if args.group:
        run_group(args.group, test_filter=args.test, runs=args.runs)
        return

    arg_parser.print_help()


if __name__ == "__main__":
    main()
