# Performance Testing & Benchmarking Plan

To accurately measure the impact of our performance improvements and ensure they scale efficiently, we need a reproducible testing framework. This plan outlines the generation of test datasets, the metrics we will track, and how we will report them.

---

## General Guidelines
1. **Reproducibility Above All**: Every single test, from dataset generation to the final execution of the benchmark scripts, must be fully documented and automated. If an experiment cannot be run by executing a single script/command after making code changes, it is invalid.
2. **Event Scenario Generation**: The existing [generation_event_senario.ipynb](file:///c:/Users/itama/.gemini/antigravity/scratch/whiteter-paths/back-end/src/events_senario_generation/generation_event_senario.ipynb) script should be heavily leveraged as the primary tool to generate all mock data, inject synthetic noise, and create realistic dense tracks, rather than writing new mock data generators from scratch.
3. **AI Agent Assistant**: When executing these guidelines or refactoring code for performance, an AI Code Agent (like myself) should be utilized to quickly scaffold the benchmark scripts, inject the logging points, and draft the Numpy/Numba vectorization updates.

---

## Phase 1 Testing: Presentation of Multiple Objects

### 1. Event Data Generation (Scalability Testing)
We will generate synthetic events with a linearly growing number of [Plot](file:///c:/Users/itama/.gemini/antigravity/scratch/whiteter-paths/front-end/my-app/src/hooks/usePlots.ts#55-147) entities and sensors. This allows us to test if performance degrades linearly or exponentially as data scales.
- **Datasets**: 10k, 50k, 100k, 250k, and 500k plots.
- **Data Properties**: Random but realistic [(x, y, z, t)](file:///c:/Users/itama/.gemini/antigravity/scratch/whiteter-paths/front-end/my-app/src/pages/Map.tsx#41-493) coordinates spread across multiple sensors (systems).

### 2. Metric 1: Data Upload / Load Time (Browser)
- **Definition**: The total time it takes from the moment an event is selected in the UI until the 3D map fully renders all plots.
- **Goal**: Minimize this duration and ensure it scales **at most linearly** `O(N)` with respect to the number of plots.
- **Measurement Method**: We will inject `performance.now()` markers in the frontend (from the start of the API call to the `onLoad` event of the Deck.gl layer) to log the load times programmatically.

### 3. Metric 2: UI Responsiveness (Frames Per Second - FPS)
- **Definition**: The frame rate of the application during active user interactions with the map (lateral panning, zooming in/out, rotating).
- **Goal**: Maintain a stable **60 FPS** regardless of dataset size.
- **Measurement Method**: Use browser developer tools (or an injected FPS monitor like `stats.js`) to record the average FPS during a standardized sequence of automated deck.gl viewport transitions.

---

## Phase 2 Testing: Recommendation System

### 1. Benchmark Data Generation (Signal vs. Noise)
We need a specialized dataset explicitly designed to test the clustering and motion-vector algorithms without testing the frontend presentation limit.
- **Tool**: Use the [generation_event_senario.ipynb](file:///c:/Users/itama/.gemini/antigravity/scratch/whiteter-paths/back-end/src/events_senario_generation/generation_event_senario.ipynb) helper to explicitly generate "clusterable datasets" mapping known track paths, while actively flooding the surrounding area with randomized background data.
- **Datasets**: Linearly growing datasets where the total size reaches up to 500k plots.
- **Data Properties**:
  - **Signal (Clusters)**: Small, tightly grouped adjacent plots that *should* be clustered (e.g., 500 to 5,000 plots max), representing actual track trajectories over time.
  - **Noise**: Completely random scattered points that *should not* be clustered. The noise sets will grow linearly (10k, 50k, 100k, 250k, 500k).

### 2. Metric 3: Recommendation Execution Time
- **Definition**: The time taken by the Python backend to receive the selected "seed" plots, execute the specified recommendation algorithm, and return the matched clusters.
- **Measurement Method**: We will create a standalone Python benchmark script using the [time](file:///c:/Users/itama/.gemini/antigravity/scratch/whiteter-paths/back-end/src/api_utils.py#11-32) module (or `timeit`) that directly invokes the [get_recommendation_base_on_strategy()](file:///c:/Users/itama/.gemini/antigravity/scratch/whiteter-paths/back-end/src/recommendation/recomendations_manager.py#14-23) function across different dataset sizes and recommendation types (`dbscan`, `motion_vector`, etc.).
- **Goal**: Measure baseline algorithm duration. After implementing vectorized/Numba improvements, we expect a massive drop in execution time.

---

## Phase 3: Reporting & Reproducibility

*Reminder: Data generation, logging hooks, and benchmarks must be scriptable and reproducible out-of-the-box for any future developer testing performance optimizations.*

### 1. Automated Benchmark Script
We will build a master benchmark script (e.g., `run_benchmarks.py`) that executes both the data generation and the recommendation timings across identical benchmark events configuration, outputting results to a CSV format.

### 2. Version Tracking and Comparison
To make informed decisions, the final report must provide a side-by-side comparison of execution times and FPS for different codebase iterations.
- The current, pre-optimized codebase will be labeled **v1**. Our initial report will only feature `v1` to establish a baseline of where we currently stand.
- Subsequent improvements (e.g., swapping to binary serialization or applying Numba JIT) will be tracked as **v1.1, v1.2, etc**.
- The testing framework must support running these specific historical versions against the exact same seed scenarios for a 1:1 comparison.

### 3. Interactive Performance Dashboard
Instead of generating static images, it is highly recommended to use **[Panel](https://panel.holoviz.org/)** (or a similar interactive visualization library) to build a dynamic report dashboard.
- A dynamic Panel application will allow us to use dedicated widgets (dropdowns, checkboxes) to selectively compare two or more specific versions (e.g., comparing `v1` natively against `v1.2`).
- The interactive graphs will plot **Dataset Size (X-axis)** versus **Time/FPS (Y-axis)**, dynamically plotting the selected version lines to instantly visualize where the bottlenecks break and how much performance was gained.

This approach strictly tracks our performance metrics, making every optimization visually verifiable and reproducible.
