# Performance Testing Guide

---

## What Is Performance Testing?

Performance testing is the practice of **measuring how a system behaves under controlled workloads** to answer one question: *does it meet its performance requirements?*

Unlike functional testing (does the button work?), performance testing asks how **fast**, how **smooth**, and how **scalable** the system is. It's about finding the limits before the user does.

There are several types of performance testing:

| Type | What it answers |
|---|---|
| **Load Testing** | Can the system handle expected traffic? |
| **Stress Testing** | Where does the system break? |
| **Scalability Testing** | Does performance degrade linearly or exponentially as data grows? |
| **Endurance Testing** | Does performance degrade over time (memory leaks)? |

### What we're doing here

In this project, we're running **scalability testing** — we increase the data size step by step (10k → 50k → 100k → 250k → 500k plots) and measure whether the system scales linearly or hits a wall. We test the **full vertical stack**: backend data loading, network transfer, browser parsing, data processing, and GPU rendering.

The goal is not just to find what's slow — it's to find **where in the pipeline** the bottleneck lives and **how it grows** with data size. A function that takes 50ms at 10k plots but 5000ms at 100k plots has a quadratic scaling problem (`O(N²)`) — and that's exactly the kind of insight this testing reveals.

---

## What We're Focusing On

Phase 1 testing focuses on the **Presentation of Multiple Objects** — specifically, how the system performs when loading and displaying large numbers of radar plots on the map.

### Two key metrics

**1. Data Load Time** — The total time from clicking an event to seeing a fully rendered map.

This is the end-to-end latency the user feels. It includes:
- Backend reading CSVs from disk
- Backend serializing data to JSON
- Network transfer to the browser
- Browser parsing the JSON
- JavaScript processing (colors, associations, filtering)
- Deck.gl constructing GPU layers
- GPU rendering the first frame

**Goal**: This should scale **linearly** — `O(N)`. If 10k plots take 500ms, then 100k plots should take roughly 5,000ms (10×), not 50,000ms (100×).

**2. UI Responsiveness (FPS)** — The frame rate during map interactions after loading.

Once the map is rendered, the user pans, zooms, and rotates. Each of these interactions requires Deck.gl to re-render all the points. If there are too many points, the frame rate drops and the map feels laggy.

**Goal**: Stable **60 FPS** during all map interactions, even with large datasets.

### Why these two metrics?

These are the two things the user directly experiences:
- **Load time** = "How long do I wait?"
- **FPS** = "Does this feel responsive?"

Everything else (memory usage, CPU spikes, backend throughput) is secondary — they only matter insofar as they affect these two user-facing metrics.

---

## The Testing Flow — How We Measure It

### The data pipeline

When a user selects an event, data flows through 5 layers. We've placed timing markers at each boundary to measure exactly how long each stage takes:

```
┌──────────────────────────────────────────────────────────────────┐
│                        FULL PIPELINE                             │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────────────┐ │
│  │   BACKEND    │──▶│   NETWORK    │──▶│       FRONTEND        │ │
│  │             │   │              │   │                       │ │
│  │ CSV → Dict  │   │ JSON over    │   │ Parse → Process →    │ │
│  │ Dict → JSON │   │ HTTPS        │   │ Construct → Render   │ │
│  └─────────────┘   └──────────────┘   └───────────────────────┘ │
│                                                                  │
│  Markers:                                                        │
│  [Backend Headers]  [T1]─────[T2]──[T3]──[T4]─[T5]─[T6][T7]─[T_END] │
└──────────────────────────────────────────────────────────────────┘
```

### Timing markers explained

Each marker captures an exact timestamp using `performance.now()`. The difference between markers gives us the duration of each stage:

| Marker | Where | What it captures |
|---|---|---|
| `X-Backend-Load-Time-Ms` | `routes.py` | Time to read CSVs and build event data |
| `X-Backend-Serialize-Time-Ms` | `routes.py` | Time to convert Python dicts → JSON |
| **T1** `FETCH_START` | `apiServer.ts` | Browser starts the fetch request |
| **T2** `RESPONSE_RECEIVED` | `apiServer.ts` | Server response headers arrive |
| **T3** `JSON_PARSED` | `apiServer.ts` | Browser finishes parsing JSON body |
| **T4** `PROCESSING_START` | `usePlots.ts` | Start processing raw plot data |
| **T5** `PROCESSING_COMPLETE` | `usePlots.ts` | Done: colors assigned, plots filtered |
| **T6** `RENDER_START` | `Map.tsx` | Deck.gl layer construction begins |
| **T7** `LAYERS_CONSTRUCTED` | `Map.tsx` | Layer objects created (before GPU upload) |
| **T_END** `FIRST_RENDER` | `Map.tsx` | First frame painted on screen |

### What we calculate from the markers

| Measurement | Formula | What it tells you |
|---|---|---|
| Network transfer | `T2 − T1` | How long to download the response |
| JSON parsing | `T3 − T2` | How long to parse the JSON payload |
| Data processing | `T5 − T4` | How long to process plots in JavaScript |
| Layer construction | `T7 − T6` | How long to create Deck.gl layer objects |
| GPU render | `T_END − T7` | How long to upload to GPU + first paint |
| **Total load time** | `T_END − T1` | **End-to-end user-facing latency** |

### How to identify bottlenecks

Run the same test across all 5 dataset sizes and compare:

```
Dataset    Network    Parse    Process    Render    TOTAL
──────────────────────────────────────────────────────────
10k          50ms      30ms      20ms      15ms     115ms
50k         200ms     150ms      90ms      40ms     480ms  ← 5× data, ~4× time ✓ linear
100k        400ms     300ms     180ms      70ms     950ms  ← 2× data, ~2× time ✓ linear
250k       1000ms     750ms    1200ms     150ms    3100ms  ← 2.5× data, processing jumped! ⚠️
500k       2000ms    1500ms    4800ms     280ms    8580ms  ← 2× data, processing 4×! 🔴 O(N²)
```

In this example, the **Process** column grows quadratically — that's your bottleneck. Everything else is linear. You now know exactly where to optimize.

---

## Prerequisites

Before testing, generate the benchmark datasets:

```bash
cd back-end
python scripts/generate_benchmark_datasets.py
```

This creates 5 events in `resource/events/`:
| Event | Plots | Purpose |
|---|---|---|
| `benchmark_10k` | 10,000 | Smoke test — should be instant |
| `benchmark_50k` | 50,000 | Typical production size |
| `benchmark_100k` | 100,000 | Moderate stress |
| `benchmark_250k` | 250,000 | Heavy load |
| `benchmark_500k` | 500,000 | Stress test / breaking point |

---

## Layer 1: Backend — Recommendation System

**What you're testing:** How long each recommendation algorithm takes as the event size grows.

### Run

```bash
cd back-end/src
python ../scripts/benchmark_recommendations.py
```

### What it does

- Tests all 4 strategies: `stn`, `trackid`, `dbscan`, `motion_vector`
- Uses 5 randomly picked seed plots from each benchmark event
- Runs each test 3 times and reports average/min/max
- Saves results to `benchmark_results/recommendation_benchmarks.csv`

### How to read the results

The console output shows a summary table:

```
Strategy          10k        50k       100k       250k       500k
─────────────────────────────────────────────────────────────────
stn                12ms       35ms       80ms      250ms      600ms
trackid             8ms       22ms       50ms      140ms      310ms
dbscan            250ms     1200ms     3500ms    12000ms    35000ms
motion_vector     800ms     4500ms    15000ms    50000ms   120000ms
```

#### What to look for

- **Linear growth** (`O(N)`): Time doubles when data doubles → acceptable
- **Quadratic growth** (`O(N²)`): Time quadruples when data doubles → bottleneck!
- **Strategy comparison**: `stn` and `trackid` should be fast (simple lookups). `dbscan` and `motion_vector` are computationally heavy — watch these closely
- **CSV analysis**: Open `benchmark_results/recommendation_benchmarks.csv` in Excel/Google Sheets and plot Dataset Size (X) vs Time (Y) for each strategy

---

## Layer 2: Backend — Data Serving

**What you're testing:** How long the backend takes to load an event from disk and serialize it to JSON.

### Run

Start the server:

```bash
cd back-end/src
python app.py
```

In another terminal, test each benchmark event:

```bash
curl -k https://127.0.0.1:5000/api/get-event/benchmark_10k -o /dev/null -w "Event: benchmark_10k\nHTTP: %{http_code}\nTotal: %{time_total}s\nTTFB: %{time_starttransfer}s\nSize: %{size_download} bytes\n\n" -s
```

Repeat for `benchmark_50k`, `benchmark_100k`, `benchmark_250k`, `benchmark_500k`.

### How to read the results

The backend adds timing headers to each response:
- **`X-Backend-Load-Time-Ms`**: Time to read CSVs from disk + build the event object
- **`X-Backend-Serialize-Time-Ms`**: Time to convert Python dicts to JSON

To see these headers:

```bash
curl -k https://127.0.0.1:5000/api/get-event/benchmark_10k -s -D - -o /dev/null | findstr "X-Backend"
```

#### What to look for

- **Load time scaling**: Should grow roughly linearly with plot count
- **Serialize time**: JSON serialization of 500k× 14 fields is expensive. If this dominates, binary serialization (MessagePack/Protobuf) would help
- **Response size**: Check how many MB the JSON payload is. Compression or binary formats can reduce this

---

## Layer 3: Frontend — Network + Parsing

**What you're testing:** How long the browser takes to download the response and parse the JSON.

### Setup

Make sure performance mode is enabled:

1. Check that `VITE_PERF_MODE=true` is set in `front-end/my-app/src/.env`
2. Restart the dev server: `cd front-end/my-app && npm run dev`
3. Open the app in your browser

### Run

1. Open browser DevTools (F12) → Console tab
2. Select a benchmark event from the events list
3. Watch the console for timing markers

### How to read the results

The console shows timestamped markers in orange:

```
⏱ T1_FETCH_START: 1234.56ms          { eventId: "benchmark_50k" }
⏱ T2_RESPONSE_RECEIVED: 2345.67ms    { status: 200, contentLength: "...", backendLoadMs: "..." }
⏱ T3_JSON_PARSED: 3456.78ms
```

**Key metric:** `T3 - T1` = Total network + parse time

This breaks down into:
- `T2 - T1` = Network transfer time (fetch)
- `T3 - T2` = JSON parsing time (`response.json()`)

#### What to look for

- **JSON parse time**: For large events, `response.json()` can take several seconds because it blocks the main thread. If `T3 - T2` is large, binary serialization would help enormously
- **Transfer time**: If `T2 - T1` is large, the payload size is the issue — consider gzip compression or binary formats

---

## Layer 4: Frontend — Data Processing

**What you're testing:** How long `processPlotData()` takes to assign colors, compute associations, and split plots into filtered arrays.

### How to read the results

Continue watching the console after. The next markers are:

```
⏱ T4_PROCESSING_START: 3456.78ms     { plotCount: 50000 }
⏱ T5_PROCESSING_COMPLETE: 3856.78ms  { plotCount: 50000 }
```

**Key metric:** `T5 - T4` = Data processing time

#### What to look for

- **Multiple iterations**: `processPlotData()` currently iterates through all plots multiple times (unique tracks, unique sensors, color map, association check). With 500k plots, this adds up
- **Re-processing**: This runs inside `useMemo`, so it only re-runs when raw data changes — not on every render. Verify this by checking that T4/T5 don't repeat without new data

---

## Layer 5: Frontend — Rendering (Deck.gl)

**What you're testing:** How long it takes Deck.gl to construct GPU layers and render the first frame.

### How to read the results

The final timing markers are:

```
⏱ T6_RENDER_START: 3856.78ms         { plotCount: 50000 }
⏱ T7_LAYERS_CONSTRUCTED: 3860.12ms   { plotCount: 50000 }
⏱ T_END_FIRST_RENDER: 3950.45ms      { plotCount: 50000 }
```

**Key metrics:**
- `T7 - T6` = Layer object construction time
- `T_END - T7` = GPU buffer upload + first paint

#### What to look for

- **Layer construction**: This is JavaScript — creating the `PointCloudLayer` object, setting up accessors
- **GPU rendering**: `T_END - T7` includes uploading vertex data to the GPU. For 500k points, this can be significant

---

## Full Pipeline Summary

After loading finishes, a formatted summary table automatically prints:

```
📊 Performance Summary
────────────────────────────────────────────────────────────
                          duration
Network (fetch)           1100.5ms
JSON Parse                 800.3ms
Data Processing            400.2ms
Layer Construction           3.3ms
First Render                93.9ms
TOTAL (T1 → T_END)        2716.2ms
  Total plots processed: 50000
```

### Console commands

| Command | What it does |
|---|---|
| `window.__PERF_UTILS.printSummary()` | Print the summary table again |
| `window.__PERF_UTILS.exportMetricsCSV()` | Export all markers as CSV (copies to clipboard) |
| `window.__PERF_UTILS.getMetrics()` | Get raw metrics object |
| `window.__PERF_UTILS.resetMetrics()` | Reset for a new test |
| `window.__PERF_METRICS` | Direct access to the metrics store |

---

## FPS Counter

When `VITE_PERF_MODE=true`, a live FPS counter appears in the top-right corner of the map:

- **Green (≥50 FPS)**: Smooth performance
- **Orange (30–49 FPS)**: Noticeable lag
- **Red (<30 FPS)**: Severe performance issues

### How to test FPS

Once the map is loaded with a benchmark event:
1. Watch the FPS counter
2. Pan the map left and right
3. Zoom in and out
4. Rotate the view
5. Note the minimum FPS — this is your worst-case rendering performance

#### What to look for

- **Target**: 60 FPS during all interactions
- **Degradation**: Does FPS drop when zoomed into dense areas?
- **Dataset size impact**: Compare FPS across 10k → 500k

---

## Running a Full Benchmark Session

Here's the recommended workflow for a complete v1 baseline:

### Step 1: Generate data  

```bash
cd back-end
python scripts/generate_benchmark_datasets.py
```

### Step 2: Benchmark recommendations  

```bash
cd back-end/src
python ../scripts/benchmark_recommendations.py
```

Save the output and CSV.

### Step 3: Start the backend  

```bash
cd back-end/src
python app.py
```

### Step 4: Start the frontend  

```bash
cd front-end/my-app
npm run dev
```

### Step 5: Test each event in the browser  

Open the app, then for each benchmark event (`benchmark_10k` through `benchmark_500k`):
1. Select the event
2. Wait for map to fully render
3. Copy the performance summary from console
4. Note the FPS during map interaction
5. Run `window.__PERF_UTILS.exportMetricsCSV()` and save the CSV

### Step 6: Compile results  

Create a spreadsheet with columns:
| Event | Plots | Network (ms) | JSON Parse (ms) | Processing (ms) | Render (ms) | Total (ms) | FPS (avg) | FPS (min) |
|---|---|---|---|---|---|---|---|---|

Plot **Plots (X-axis) vs Time (Y-axis)** to see which stages scale linearly vs exponentially.

---

## Disabling Performance Mode

When done testing, set `VITE_PERF_MODE=false` (or remove the line) in `.env` to disable all instrumentation:
- FPS counter will not render
- No timing markers in console
- Zero performance overhead in production

---

## File Reference

| File | Location | Purpose |
|---|---|---|
| `generate_benchmark_datasets.py` | `back-end/scripts/` | Generate benchmark events |
| `benchmark_recommendations.py` | `back-end/scripts/` | Benchmark recommendation algorithms |
| `perfUtils.ts` | `front-end/my-app/src/utils/` | Central timing utilities |
| `FPSCounter.tsx` | `front-end/my-app/src/components/` | Live FPS overlay |
| `.env` | `front-end/my-app/src/` | `VITE_PERF_MODE` toggle |
| Backend timing | `routes.py` | `X-Backend-*` response headers |
