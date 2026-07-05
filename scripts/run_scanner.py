import subprocess
import sys
import time
import pandas as pd


STEPS = [
    ("Build F&O universe", "build_universe.py"),
    ("Scan option chains", "option_chain_scanner.py"),
    ("Generate trade candidates", "daily_scanner_v8.py"),
]

CANDIDATES_FILE = "trade_candidates.csv"


def run_step(title, script):
    print("")
    print("=" * 80)
    print(title)
    print("=" * 80)

    start = time.time()

    result = subprocess.run(
        [sys.executable, script],
        text=True,
        capture_output=True,
    )

    elapsed = round(time.time() - start, 2)

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print(f"FAILED: {script}")
        sys.exit(result.returncode)

    print(f"Completed {script} in {elapsed} seconds")


def show_final_candidates():
    print("")
    print("=" * 80)
    print("FINAL TRADE CANDIDATES")
    print("=" * 80)

    df = pd.read_csv(CANDIDATES_FILE)

    if df.empty:
        print("No trade candidates found.")
        return

    preview_cols = [
        "symbol",
        "rank_score",
        "confidence_grade",
        "candidate_quality",
        "suggested_action",
        "tradable_strike",
        "estimated_premium",
        "lot_size",
        "estimated_max_loss",
        "option_stop_loss",
        "option_target_1",
        "option_target_2",
        "spot",
        "breakeven_pct",
    ]

    preview_cols = [c for c in preview_cols if c in df.columns]

    print(df[preview_cols].head(20).to_string(index=False))


def main():
    total_start = time.time()

    for title, script in STEPS:
        run_step(title, script)

    show_final_candidates()

    total_elapsed = round(time.time() - total_start, 2)

    print("")
    print("=" * 80)
    print("SCANNER COMPLETE")
    print("=" * 80)
    print(f"Total elapsed seconds: {total_elapsed}")
    print(f"Saved: {CANDIDATES_FILE}")


if __name__ == "__main__":
    main()