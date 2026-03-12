"""
Benchmark Dataset Generator for Phase 1 Performance Testing.

Generates synthetic event datasets at standardized sizes (10k, 50k, 100k, 250k, 500k plots)
for reproducible performance benchmarking of the whiteter-tracks application.

Usage:
    python scripts/generate_benchmark_datasets.py

Output:
    Creates benchmark event folders in resource/events/:
        benchmark_10k/  benchmark_50k/  benchmark_100k/  benchmark_250k/  benchmark_500k/
    Each contains:
        - plots.csv (N rows matching the target size)
        - plots_correlations.csv (header only, no correlations)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import time

# --- Configuration ---
EVENTS_FOLDER = Path(__file__).resolve().parents[1] / "resource" / "events"

# Dataset sizes to generate
BENCHMARK_SIZES = {
    "benchmark_10k": 10_000,
    "benchmark_50k": 50_000,
    "benchmark_100k": 100_000,
    "benchmark_250k": 250_000,
    "benchmark_500k": 500_000,
}

# Realistic geographic bounds (Israel region)
LAT_MIN, LAT_MAX = 31.0, 33.0
LON_MIN, LON_MAX = 34.0, 36.0
ALT_MIN, ALT_MAX = 100.0, 15_000.0

# Sensor configuration
NUM_SENSORS = 5       # system_id 1..5
STN_PER_SENSOR = 10   # STN values 1..10 per sensor

# Coordinate uncertainty
SIG_X, SIG_Y, SIG_Z = 500, 500, 500

# Time range
T_START = 0.0
T_STEP = 1.5  # seconds between consecutive plots


def generate_benchmark_event(event_name: str, num_plots: int) -> None:
    """Generate a single benchmark event with the specified number of plots.

    Args:
        event_name: Name of the event folder (e.g., 'benchmark_10k')
        num_plots: Number of plot rows to generate
    """
    print(f"\n{'='*60}")
    print(f"  Generating: {event_name} ({num_plots:,} plots)")
    print(f"{'='*60}")

    event_dir = EVENTS_FOLDER / event_name
    event_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.perf_counter()

    # --- Generate plot data using numpy for speed ---
    rng = np.random.default_rng(seed=42)  # Fixed seed for reproducibility

    # Core identifiers
    system_ids = rng.integers(1, NUM_SENSORS + 1, size=num_plots)
    plot_ids = np.arange(1000, 1000 + num_plots)
    t_values = np.arange(num_plots) * T_STEP + T_START

    # Geographic coordinates (realistic scatter)
    latitudes = rng.uniform(LAT_MIN, LAT_MAX, size=num_plots)
    longitudes = rng.uniform(LON_MIN, LON_MAX, size=num_plots)
    altitudes = rng.uniform(ALT_MIN, ALT_MAX, size=num_plots)

    # Cartesian coordinates (derived from geographic for consistency)
    # Using simplified conversion: approximate ECEF from lat/lon/alt
    lat_rad = np.radians(latitudes)
    lon_rad = np.radians(longitudes)
    R = 6_371_000  # Earth radius in meters
    x = (R + altitudes) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (R + altitudes) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (R + altitudes) * np.sin(lat_rad)

    # Sensor tracking numbers
    stns = rng.integers(1, STN_PER_SENSOR + 1, size=num_plots)

    # Target IDs (simulate multiple targets being tracked)
    num_targets = max(1, num_plots // 200)
    target_ids = rng.integers(1, num_targets + 1, size=num_plots)

    gen_time = time.perf_counter() - start_time
    print(f"  [1/3] Data generated in {gen_time:.2f}s")

    # --- Build DataFrame ---
    df_start = time.perf_counter()
    df = pd.DataFrame({
        "system_id": system_ids,
        "plot_id": plot_ids,
        "t": t_values,
        "x": x,
        "y": y,
        "z": z,
        "sig_x": SIG_X,
        "sig_y": SIG_Y,
        "sig_z": SIG_Z,
        "target_id": target_ids,
        "latitude": latitudes,
        "longitude": longitudes,
        "altitude": altitudes,
        "STN": stns,
    })
    df_time = time.perf_counter() - df_start
    print(f"  [2/3] DataFrame built in {df_time:.2f}s")

    # --- Write to disk ---
    write_start = time.perf_counter()

    # Write plots.csv
    plots_path = event_dir / "plots.csv"
    df.to_csv(plots_path, index=False)

    # Write empty plots_correlations.csv (header only)
    correlations_path = event_dir / "plots_correlations.csv"
    pd.DataFrame(columns=["plot_id", "system_id", "track_id"]).to_csv(
        correlations_path, index=False
    )

    write_time = time.perf_counter() - write_start
    total_time = time.perf_counter() - start_time
    file_size_mb = plots_path.stat().st_size / (1024 * 1024)

    print(f"  [3/3] Written to disk in {write_time:.2f}s")
    print(f"  ────────────────────────────────────")
    print(f"  Total time:  {total_time:.2f}s")
    print(f"  File size:   {file_size_mb:.1f} MB")
    print(f"  Location:    {event_dir}")


def validate_datasets() -> None:
    """Validate all benchmark datasets exist and have correct row counts."""
    print(f"\n{'='*60}")
    print(f"  Validation Results")
    print(f"{'='*60}")

    all_valid = True
    for name, expected_count in BENCHMARK_SIZES.items():
        plots_path = EVENTS_FOLDER / name / "plots.csv"
        if not plots_path.exists():
            print(f"  ❌ {name}: plots.csv NOT FOUND")
            all_valid = False
            continue

        actual_count = sum(1 for _ in open(plots_path)) - 1  # subtract header
        status = "✅" if actual_count == expected_count else "❌"
        if actual_count != expected_count:
            all_valid = False
        print(f"  {status} {name}: {actual_count:>8,} plots (expected {expected_count:,})")

    print(f"\n  {'All datasets valid!' if all_valid else 'Some datasets failed validation!'}")


def main():
    print("=" * 60)
    print("  Phase 1 Benchmark Dataset Generator")
    print("  whiteter-tracks Performance Testing")
    print("=" * 60)
    print(f"  Output directory: {EVENTS_FOLDER}")

    total_start = time.perf_counter()

    for event_name, num_plots in BENCHMARK_SIZES.items():
        generate_benchmark_event(event_name, num_plots)

    total_time = time.perf_counter() - total_start
    print(f"\n  All datasets generated in {total_time:.1f}s total")

    # Validate
    validate_datasets()


if __name__ == "__main__":
    main()
