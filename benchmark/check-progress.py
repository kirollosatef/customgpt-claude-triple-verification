"""Check benchmark progress."""
import json
import glob
import os

base = r"C:\Users\Felipe Pires\quadruple-verification-benchmark\results"

for group in ["B", "A"]:
    pattern = os.path.join(base, f"group-{group}", "*", "run-1", "result.json")
    files = sorted(glob.glob(pattern))
    if not files:
        continue

    print(f"\n=== Group {group} ===")
    total_cost = 0
    total_time = 0
    for f in files:
        r = json.load(open(f))
        cost = r.get("total_cost_usd") or 0
        total_cost += cost
        total_time += r["latency_seconds"]
        tok = r["token_count"] or "N/A"
        print(f"  {r['test_id']:>8} | {r['latency_seconds']:>7.1f}s | tokens: {str(tok):>10} | cost: ${cost:.4f}")

    print(f"  ---")
    print(f"  Done: {len(files)} tests | Time: {total_time:.0f}s ({total_time/60:.1f}min) | Cost: ${total_cost:.4f}")
    remaining = 35 - len(files)
    if len(files) > 0 and remaining > 0:
        avg_time = total_time / len(files)
        avg_cost = total_cost / len(files)
        print(f"  Remaining: {remaining} tests | ETA: ~{remaining * avg_time / 60:.0f}min | Est cost: ~${remaining * avg_cost:.2f}")
    elif remaining == 0:
        print(f"  COMPLETE!")
