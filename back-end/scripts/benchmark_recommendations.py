"""
Recommendation System Benchmark — Phase 1 Performance Testing.

Benchmarks all 4 recommendation strategies across multiple dataset sizes.
Picks random seed plots from each event and measures execution time.

Usage:
    cd back-end/src
    python ../scripts/benchmark_recommendations.py

Prerequisites:
    - Benchmark events must exist in resource/events/ (run generate_benchmark_datasets.py first)
    - All dependencies must be installed (numpy, pandas, scikit-learn, etc.)

Output:
    - Console: formatted table of results
    - CSV:     benchmark_results/recommendation_benchmarks.csv
"""

import sys
import time
import csv
import traceback
from pathlib import Path

# Add src to path so we can import project modules
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import pandas as pd
from events_logic.event_cache import load_event, clear_event
from recommendation.recomendations_manager import get_recommendation_base_on_strategy

# --- Configuration ---
EVENTS_FOLDER = Path(__file__).resolve().parents[1] / "resource" / "events"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "benchmark_results"

# Benchmark events to test (must exist in resource/events/)
BENCHMARK_EVENTS = [
    "benchmark_10k",
    "benchmark_50k",
    "benchmark_100k",
    "benchmark_250k",
    "benchmark_500k",
]

# All recommendation strategies to benchmark
STRATEGIES = ["stn", "trackid", "dbscan", "motion_vector"]

# Number of seed plots to select for each recommendation call
NUM_SEED_PLOTS = 5

# Number of times to repeat each test for statistical reliability
NUM_RUNS = 3


def pick_seed_plots(event_id: str, num_plots: int = NUM_SEED_PLOTS) -> list[dict]:
    """Pick random seed plots from an event for use as recommendation input.

    Selects plots that are close together in time to simulate realistic user selection.

    Args:
        event_id: The event to sample from.
        num_plots: Number of seed plots to pick.

    Returns:
        List of plot dicts matching the expected input format.
    """
    event = load_event(event_id)
    df = event.df_plots.copy()

    # Pick a random starting time and select nearby plots
    if len(df) <= num_plots:
        sample = df
    else:
        # Sort by time and pick a contiguous block — more realistic than random scatter
        df_sorted = df.sort_values("t").reset_index(drop=True)
        start_idx = max(0, len(df_sorted) // 3)  # Start at ~1/3 of the time range
        sample = df_sorted.iloc[start_idx : start_idx + num_plots]

    return sample.to_dict(orient="records")


def run_single_benchmark(
    strategy_name: str, event_id: str, seed_plots: list[dict]
) -> dict:
    """Run a single benchmark: one strategy, one event, one set of seed plots.

    Returns:
        Dict with timing results and metadata.
    """
    result = {
        "strategy": strategy_name,
        "event_id": event_id,
        "num_seed_plots": len(seed_plots),
        "execution_time_ms": None,
        "num_results": None,
        "status": "success",
        "error": None,
    }

    try:
        start = time.perf_counter()
        recommended = get_recommendation_base_on_strategy(
            strategy_name, event_id, seed_plots
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        result["execution_time_ms"] = round(elapsed_ms, 2)
        result["num_results"] = len(recommended) if recommended else 0
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        traceback.print_exc()

    return result


def run_benchmarks():
    """Run all benchmarks across all strategies and event sizes."""
    print("=" * 70)
    print("  Recommendation System Benchmark")
    print("  Phase 1 Performance Testing")
    print("=" * 70)

    all_results = []

    for event_id in BENCHMARK_EVENTS:
        event_dir = EVENTS_FOLDER / event_id
        if not event_dir.exists():
            print(f"\n⚠️  Skipping {event_id}: event folder not found")
            print(f"   Run generate_benchmark_datasets.py first!")
            continue

        # Count plots
        plots_csv = event_dir / "plots.csv"
        plot_count = sum(1 for _ in open(plots_csv)) - 1 if plots_csv.exists() else 0

        print(f"\n{'─'*70}")
        print(f"  Event: {event_id}  ({plot_count:,} plots)")
        print(f"{'─'*70}")

        # Pre-load event into cache
        print(f"  Loading event into cache...", end=" ", flush=True)
        t0 = time.perf_counter()
        load_event(event_id)
        cache_time = (time.perf_counter() - t0) * 1000
        print(f"done ({cache_time:.0f}ms)")

        # Pick seed plots (same seeds for all strategies in this event)
        seed_plots = pick_seed_plots(event_id)
        print(f"  Seed plots: {len(seed_plots)} (from t={seed_plots[0]['t']:.1f} to t={seed_plots[-1]['t']:.1f})")

        for strategy_name in STRATEGIES:
            times = []
            last_result = None

            for run_idx in range(NUM_RUNS):
                result = run_single_benchmark(strategy_name, event_id, seed_plots)
                result["run"] = run_idx + 1
                result["event_plot_count"] = plot_count
                result["cache_load_ms"] = round(cache_time, 2)
                all_results.append(result)

                if result["status"] == "success":
                    times.append(result["execution_time_ms"])
                last_result = result

            # Print summary for this strategy+event combination
            if times:
                avg_ms = sum(times) / len(times)
                min_ms = min(times)
                max_ms = max(times)
                status_str = f"avg={avg_ms:>8.1f}ms  min={min_ms:>8.1f}ms  max={max_ms:>8.1f}ms  results={last_result['num_results']}"
            else:
                status_str = f"❌ FAILED: {last_result['error'][:60]}"

            print(f"  {strategy_name:<16} {status_str}")

        # Clear cache between events to avoid memory issues
        clear_event(event_id)

    return all_results


def save_results_csv(results: list[dict]):
    """Save benchmark results to CSV."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "recommendation_benchmarks.csv"

    if not results:
        print("\nNo results to save.")
        return

    fieldnames = [
        "strategy", "event_id", "event_plot_count", "run",
        "num_seed_plots", "execution_time_ms", "num_results",
        "cache_load_ms", "status", "error",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n📄 Results saved to: {output_path}")


def print_summary_table(results: list[dict]):
    """Print a summary table of average execution times."""
    print(f"\n{'='*70}")
    print(f"  Summary: Average Execution Time (ms)")
    print(f"{'='*70}")

    # Header
    event_names = sorted(set(r["event_id"] for r in results if r["status"] == "success"))
    header = f"{'Strategy':<16}"
    for name in event_names:
        short_name = name.replace("benchmark_", "")
        header += f" {short_name:>10}"
    print(header)
    print("─" * len(header))

    # Rows
    for strategy in STRATEGIES:
        row = f"{strategy:<16}"
        for event_id in event_names:
            runs = [
                r["execution_time_ms"]
                for r in results
                if r["strategy"] == strategy
                and r["event_id"] == event_id
                and r["status"] == "success"
            ]
            if runs:
                avg = sum(runs) / len(runs)
                row += f" {avg:>9.1f}ms" if avg < 100_000 else f" {avg/1000:>8.1f}s"
            else:
                row += f" {'FAILED':>10}"
        print(row)


def main():
    results = run_benchmarks()
    save_results_csv(results)
    print_summary_table(results)


if __name__ == "__main__":
    main()
