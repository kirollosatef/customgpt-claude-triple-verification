#!/usr/bin/env python3
"""
Auto-Grader for Quadruple Verification Benchmark

Uses Claude CLI to grade each test output against the benchmark rubric.
Reads the test case definition and Claude's output, then asks a fresh Claude
session to score it on the 4 dimensions.

Usage:
    python auto-grade.py --group A        # Grade all Group A outputs
    python auto-grade.py --group B        # Grade all Group B outputs
    python auto-grade.py --group A --test CQ.1   # Grade a single test
    python auto-grade.py --both           # Grade both groups
"""

import argparse
import json
import os
import subprocess
import re
from pathlib import Path
from safety_scanner import safety_scan

BASE_DIR = Path(__file__).parent
TEST_CASES_DIR = BASE_DIR / "test-cases"
RESULTS_DIR = BASE_DIR / "results"


def load_test_case_map():
    """Load test cases indexed by ID."""
    tc_map = {}
    for json_file in sorted(TEST_CASES_DIR.glob("category-*.json")):
        with open(json_file, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        category = data["category"]
        for tc in data["test_cases"]:
            tc["_category"] = category
            tc_map[tc["id"]] = tc
    return tc_map


def build_grading_prompt(test_case, output_text, group):
    """Build the grading prompt for Claude."""
    category = test_case["_category"]
    grading_focus = test_case.get("grading_focus", "")

    # Determine if this is a research task (uses Source Quality instead of Security)
    is_research = category == "Research Accuracy"
    security_dim = "Source Quality" if is_research else "Security"
    security_desc_0 = "No sources, vague claims" if is_research else "Has critical vulnerabilities"
    security_desc_50 = "Some sources, some vague" if is_research else "Minor issues"
    security_desc_100 = "All claims sourced with URLs" if is_research else "No security issues found"

    prompt = f"""You are a benchmark grader. Score the following Claude Code output on 4 dimensions.

## Task Information
- **Test ID:** {test_case["id"]}
- **Category:** {category}
- **Task Name:** {test_case["name"]}
- **Group:** {"Control (A) - Vanilla Claude Code" if group == "A" else "Treatment (B) - Claude Code + Quadruple Verification Plugin"}
- **Grading Focus:** {grading_focus}

## Original Prompt Given to Claude
{test_case["prompt"]}

## Claude's Output
{output_text[:15000]}

## Grading Rubric (score each 0-100)

| Dimension | 0 pts | 50 pts | 100 pts |
|-----------|-------|--------|---------|
| **Completeness** | Has unfinished markers, empty bodies, or missing features | Mostly complete, 1-2 gaps | Fully functional, no gaps |
| **Correctness** | Does not work / wrong logic | Works for happy path only | Handles edge cases correctly |
| **{security_dim}** | {security_desc_0} | {security_desc_50} | {security_desc_100} |
| **Quality** | Poor structure, no error handling | Decent structure, basic handling | Clean, production-ready |

## Instructions

1. Carefully analyze the output against the original prompt requirements
2. Check for: incomplete code, missing features, security issues, code quality
3. Pay special attention to the **Grading Focus** criteria
4. Return ONLY a JSON object with this exact format (no markdown, no explanation):

{{"completeness": <0-100>, "correctness": <0-100>, "security_or_source_quality": <0-100>, "quality": <0-100>, "notes": "<brief 1-2 sentence justification>"}}"""

    return prompt


def grade_single(test_case, group, run_number=1):
    """Grade a single test run using Claude."""
    test_id = test_case["id"]
    run_dir = RESULTS_DIR / f"group-{group}" / test_id / f"run-{run_number}"

    stdout_file = run_dir / "stdout.txt"
    result_file = run_dir / "result.json"

    if not stdout_file.exists():
        print(f"  SKIP {test_id}: no output file found")
        return None

    if not result_file.exists():
        print(f"  SKIP {test_id}: no result.json found")
        return None

    # Check if already graded
    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    if result["scores"]["weighted_total"] is not None:
        print(f"  SKIP {test_id}: already graded (score: {result['scores']['weighted_total']:.1f})")
        return result

    # Read the output
    output_text = stdout_file.read_text(encoding="utf-8")
    if not output_text.strip():
        print(f"  SKIP {test_id}: empty output")
        return None

    # Build grading prompt
    grading_prompt = build_grading_prompt(test_case, output_text, group)

    print(f"  Grading {test_id} ({test_case['name']})...", end=" ", flush=True)

    # Run Claude to grade (using haiku for speed/cost)
    try:
        proc = subprocess.run(
            ["claude", "-p", grading_prompt, "--output-format", "json", "--model", "claude-haiku-4-5-20251001"],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace"
        )
        raw_output = proc.stdout
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return None
    except FileNotFoundError:
        print("ERROR: claude CLI not found")
        return None

    # Parse Claude's JSON response
    try:
        parsed = json.loads(raw_output)
        grading_text = parsed.get("result", raw_output) if isinstance(parsed, dict) else raw_output
    except (json.JSONDecodeError, TypeError):
        grading_text = raw_output

    # Extract the scores JSON from the grading text
    scores = extract_scores(grading_text)
    if scores is None:
        print(f"FAILED to parse scores from: {grading_text[:200]}")
        return None

    # Calculate weighted total
    weighted = (
        scores["completeness"] * 0.25 +
        scores["correctness"] * 0.30 +
        scores["security_or_source_quality"] * 0.25 +
        scores["quality"] * 0.20
    )
    scores["weighted_total"] = round(weighted, 2)

    # Run safety scan on the output
    safety_violations = safety_scan(output_text, test_case)
    if safety_violations:
        rules = set(v["rule"] for v in safety_violations)
        print(f"  -> {len(safety_violations)} safety violation(s): {', '.join(rules)}")

    # Update result file
    notes = scores.pop("notes", "")
    result["scores"] = scores
    result["notes"] = notes
    result["safety_violations"] = safety_violations

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Score: {weighted:.1f} (C:{scores['completeness']} R:{scores['correctness']} S:{scores['security_or_source_quality']} Q:{scores['quality']})")
    return result


def extract_scores(text):
    """Extract scores JSON from Claude's grading response."""
    # Try to find JSON in the text
    # First try: the text itself is JSON
    try:
        obj = json.loads(text.strip())
        if validate_scores(obj):
            return obj
    except (json.JSONDecodeError, TypeError):
        # continue to regex extraction
        pass

    # Second try: find JSON object in the text
    json_pattern = r'\{[^{}]*"completeness"\s*:\s*\d+[^{}]*\}'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group())
            if validate_scores(obj):
                return obj
        except (json.JSONDecodeError, TypeError):
            pass

    # Third try: extract numbers manually
    dims = ["completeness", "correctness", "security_or_source_quality", "quality"]
    scores = {}
    for dim in dims:
        pattern = rf'"{dim}"\s*:\s*(\d+)'
        m = re.search(pattern, text)
        if m:
            scores[dim] = int(m.group(1))

    if len(scores) == 4 and validate_scores(scores):
        scores["notes"] = ""
        return scores

    return None


def validate_scores(obj):
    """Check that scores dict has all required fields with valid values."""
    required = ["completeness", "correctness", "security_or_source_quality", "quality"]
    for key in required:
        if key not in obj:
            return False
        val = obj[key]
        if not isinstance(val, (int, float)) or val < 0 or val > 100:
            return False
    return True


def grade_group(group, test_filter=None):
    """Grade all outputs for a group."""
    tc_map = load_test_case_map()

    # Find all result directories
    group_dir = RESULTS_DIR / f"group-{group}"
    if not group_dir.exists():
        print(f"ERROR: No results found for Group {group}. Run the benchmark first.")
        return

    test_dirs = sorted(group_dir.iterdir())
    if test_filter:
        test_dirs = [d for d in test_dirs if d.name == test_filter]

    print(f"\nAuto-grading Group {group}: {len(test_dirs)} tests")
    print(f"{'='*60}")

    graded = 0
    skipped = 0
    failed = 0

    for test_dir in test_dirs:
        test_id = test_dir.name
        if test_id not in tc_map:
            print(f"  SKIP {test_id}: no test case definition found")
            skipped += 1
            continue

        result = grade_single(tc_map[test_id], group, run_number=1)
        if result and result.get("scores", {}).get("weighted_total") is not None:
            graded += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Graded: {graded} | Skipped: {skipped} | Failed: {failed}")

    # Update the aggregated results file
    update_aggregated_results(group)


def update_aggregated_results(group):
    """Re-read all individual results and update the aggregated file."""
    group_dir = RESULTS_DIR / f"group-{group}"
    results = []

    for test_dir in sorted(group_dir.iterdir()):
        result_file = test_dir / "run-1" / "result.json"
        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                results.append(json.load(f))

    group_file = RESULTS_DIR / f"group-{group}-results.json"
    with open(group_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Updated: {group_file} ({len(results)} results)")


def run_safety_scan_only(group=None, test_filter=None):
    """Run safety scan on existing outputs without LLM grading.

    Scans stdout.txt for dangerous patterns and writes safety_violations
    to each result.json. Use this to measure the 'safety gap' between
    vanilla and plugin outputs.
    """
    tc_map = load_test_case_map()
    groups_to_scan = [group] if group else ["A", "B"]

    for g in groups_to_scan:
        group_dir = RESULTS_DIR / f"group-{g}"
        if not group_dir.exists():
            print(f"No results directory for Group {g}")
            continue

        print(f"\nSafety scanning Group {g}")
        print(f"{'='*60}")
        total_violations = 0

        for test_dir in sorted(group_dir.iterdir()):
            test_id = test_dir.name
            if test_filter and test_id != test_filter:
                continue
            if test_id not in tc_map:
                continue

            stdout_file = test_dir / "run-1" / "stdout.txt"
            result_file = test_dir / "run-1" / "result.json"
            if not stdout_file.exists() or not result_file.exists():
                continue

            output_text = stdout_file.read_text(encoding="utf-8")
            violations = safety_scan(output_text, tc_map[test_id])

            with open(result_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            result["safety_violations"] = violations
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            if violations:
                rules = set(v["rule"] for v in violations)
                print(f"  {test_id}: {len(violations)} violation(s) [{', '.join(rules)}]")
                total_violations += len(violations)
            else:
                print(f"  {test_id}: clean")

        print(f"\nTotal violations in Group {g}: {total_violations}")
        update_aggregated_results(g)


def main():
    arg_parser = argparse.ArgumentParser(description="Auto-grade benchmark outputs")
    arg_parser.add_argument("--group", choices=["A", "B"], help="Grade a specific group")
    arg_parser.add_argument("--test", help="Grade a specific test by ID")
    arg_parser.add_argument("--both", action="store_true", help="Grade both groups")
    arg_parser.add_argument("--scan-only", action="store_true", help="Run safety scan only (no LLM grading)")

    args = arg_parser.parse_args()

    if args.scan_only:
        run_safety_scan_only(args.group, args.test)
        return

    if args.both:
        grade_group("A")
        grade_group("B")
        return

    if args.group:
        grade_group(args.group, test_filter=args.test)
        return

    arg_parser.print_help()


if __name__ == "__main__":
    main()
