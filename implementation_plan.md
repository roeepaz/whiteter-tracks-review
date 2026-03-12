# Phase 1 Performance Testing — Implementation Plan

Implement the full Phase 1 testing infrastructure: generate benchmark datasets, instrument the frontend code with timing markers, and create an automated benchmark runner.

## Proposed Changes

### Component 1: Dataset Generation Script

We need standardized benchmark events at 10k, 50k, 100k, 250k, and 500k plot sizes. Event "250" already exists with 250k plots, so we leverage that and generate the remaining sizes.

#### [NEW] [generate_benchmark_datasets.py](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/back-end/scripts/generate_benchmark_datasets.py)

A standalone Python script that:
- Generates synthetic [plots.csv](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/back-end/resource/events/250/plots.csv) files with realistic data matching the existing CSV format (`system_id, plot_id, t, x, y, z, sig_x, sig_y, sig_z, target_id, latitude, longitude, altitude, STN`)
- Creates events named `benchmark_10k`, `benchmark_50k`, `benchmark_100k`, `benchmark_250k`, `benchmark_500k` in `resource/events/`
- Each event gets a [plots.csv](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/back-end/resource/events/250/plots.csv) and an empty [plots_correlations.csv](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/back-end/resource/events/10.10.2020/plots_correlations.csv) (header only)
- Coordinates are realistic — scattered across a geographic area around Israel (lat ~31–33, lon ~34–36) with varying altitudes
- Multiple sensors (system_id 1–5) and STN values for realistic distribution
- Time values (`t`) spread linearly across a realistic range

---

### Component 2: Frontend Performance Instrumentation

Inject `performance.now()` markers at critical pipeline stages to measure load time breakdown.

#### [MODIFY] [apiServer.ts](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/front-end/my-app/src/API/apiServer.ts)

- Add timing around the [fetch()](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/front-end/my-app/src/API/apiServer.ts#96-109) call and `response.json()` parsing in [fetchEventPlots()](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/front-end/my-app/src/API/apiServer.ts#21-36)
- Log `T1_FETCH_START`, `T2_RESPONSE_RECEIVED`, `T3_JSON_PARSED` to `window.__PERF_METRICS`
- Wrap in a `PERF_MODE` flag so instrumentation only runs when enabled

#### [MODIFY] [usePlots.ts](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/front-end/my-app/src/hooks/usePlots.ts)

- Add timing around [processPlotData()](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/front-end/my-app/src/hooks/usePlots.ts#15-64) call inside the `useMemo`
- Log `T4_PROCESSING_START`, `T5_PROCESSING_COMPLETE` to `window.__PERF_METRICS`
- Log the number of plots processed

#### [MODIFY] [Map.tsx](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/front-end/my-app/src/pages/Map.tsx)

- Add timing around layer construction in the `useMemo` for `layers`
- Log `T6_RENDER_START`, `T7_LAYERS_CONSTRUCTED`
- Add `onAfterRender` callback on DeckGL to capture `T_END` (first frame rendered)
- Inject `stats.js` FPS counter (toggled by `PERF_MODE`)

#### [NEW] [perfUtils.ts](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/front-end/my-app/src/utils/perfUtils.ts)

- Central performance utilities: `markPerf(label)`, `getMetrics()`, `resetMetrics()`, `exportMetricsCSV()`
- `window.__PERF_METRICS` object with timestamped entries
- `PERF_MODE` flag (read from env var `VITE_PERF_MODE=true`)

---

### Component 3: Backend Timing (Optional but Recommended)

#### [MODIFY] [routes.py](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/back-end/src/server/routes.py)

- Add `time.perf_counter()` around the [get_event_data()](file:///c:/Users/roeep/OneDrive/Desktop/code-review/whiteter-tracks-review/back-end/src/events_logic/events_api.py#31-55) call and `jsonify()` in the `/api/get-event/<id>` route
- Log backend timing in the response headers (`X-Backend-Load-Time-Ms`, `X-Backend-Serialize-Time-Ms`)
- This lets the frontend capture backend durations from `response.headers`

---

## User Review Required

> [!IMPORTANT]
> **Dataset Generation**: The script will create 5 new event folders inside `resource/events/`. The existing "250" event has 250k plots — should we reuse it as `benchmark_250k`, or generate a fresh one for consistency?

> [!IMPORTANT]
> **FPS Measurement**: The plan uses `stats.js` for FPS monitoring. We can also build a custom FPS counter using `requestAnimationFrame`. Do you have a preference? `stats.js` gives a visual overlay + logs, while a custom solution gives CSV-exportable data.

> [!IMPORTANT]
> **Automated Viewport Transitions**: For FPS benchmarking, we need to programmatically pan/zoom/rotate the map. This requires Deck.gl's `flyTo` transitions. Should we build this into the app as a "benchmark mode" button, or as a separate test script?

---

## Verification Plan

### Automated Tests

1. **Dataset validation**: After generating datasets, run a verification script that:
   ```
   cd back-end
   python scripts/generate_benchmark_datasets.py
   python -c "import pandas as pd; [print(f'{name}: {len(pd.read_csv(f\"resource/events/benchmark_{name}/plots.csv\"))} plots') for name in ['10k','50k','100k','250k','500k']]"
   ```
   Expected: each benchmark event has the correct number of rows.

2. **Backend load test**: Start the server and fetch each benchmark event, verifying response headers contain timing data:
   ```
   cd back-end/src
   python app.py &
   curl -k https://127.0.0.1:5000/api/get-event/benchmark_10k -w "\nHTTP code: %{http_code}\nTime: %{time_total}s\n"
   ```

3. **Frontend instrumentation**: Open the app in browser with `VITE_PERF_MODE=true`, select a benchmark event, and check `window.__PERF_METRICS` in the console for correct timing entries.

### Manual Verification

1. **Visual smoke test**: Open the app, select `benchmark_10k` → verify plots render on map without errors
2. **FPS overlay**: With perf mode on, verify the `stats.js` FPS counter appears on screen
3. **Metrics export**: After loading an event, run `window.__PERF_METRICS` in dev console, verify all timestamps (T0 through T_END) are populated, and that `exportMetricsCSV()` produces valid CSV output

> [!NOTE]
> We will run baseline tests (v1) across all 5 dataset sizes after instrumentation is complete. The results become the comparison target for future optimizations.
