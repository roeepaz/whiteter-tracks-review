/**
 * Performance Measurement Utilities for Phase 1 Benchmarking.
 *
 * Provides centralized timing markers, FPS monitoring, and CSV export.
 * Enable by setting VITE_PERF_MODE=true in .env
 */

// --- Perf Mode Flag ---
export const PERF_MODE = import.meta.env.VITE_PERF_MODE === 'true';

// --- Types ---
interface PerfEntry {
  label: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

interface PerfMetrics {
  entries: PerfEntry[];
  sessionId: string;
  startTime: number;
}

// --- Global metrics store ---
const metrics: PerfMetrics = {
  entries: [],
  sessionId: `perf_${Date.now()}`,
  startTime: 0,
};

// Expose on window for dev console access
if (PERF_MODE && typeof window !== 'undefined') {
  (window as any).__PERF_METRICS = metrics;
  (window as any).__PERF_UTILS = {
    getMetrics,
    resetMetrics,
    exportMetricsCSV,
    printSummary,
  };
  console.log(
    '%c🔬 PERF MODE ENABLED — window.__PERF_METRICS / window.__PERF_UTILS available',
    'color: #00ff88; font-weight: bold; font-size: 14px;'
  );
}

/**
 * Record a timing marker with an optional metadata payload.
 */
export function markPerf(label: string, metadata?: Record<string, unknown>): void {
  if (!PERF_MODE) return;

  const timestamp = performance.now();
  metrics.entries.push({ label, timestamp, metadata });

  // Set session start on first marker
  if (metrics.entries.length === 1) {
    metrics.startTime = timestamp;
  }

  console.log(
    `%c⏱ ${label}: ${timestamp.toFixed(2)}ms`,
    'color: #ffa500; font-weight: bold;',
    metadata || ''
  );
}

/**
 * Return all collected metrics.
 */
export function getMetrics(): PerfMetrics {
  return { ...metrics };
}

/**
 * Reset all metrics for a new test run.
 */
export function resetMetrics(): void {
  metrics.entries = [];
  metrics.startTime = 0;
  metrics.sessionId = `perf_${Date.now()}`;
}

/**
 * Print a human-readable summary of load time segments.
 */
export function printSummary(): void {
  if (metrics.entries.length === 0) {
    console.log('No perf entries recorded.');
    return;
  }

  console.log('\n%c📊 Performance Summary', 'color: #00ccff; font-weight: bold; font-size: 16px;');
  console.log('─'.repeat(60));

  const find = (label: string) => metrics.entries.find(e => e.label === label)?.timestamp;

  const t1 = find('T1_FETCH_START');
  const t2 = find('T2_RESPONSE_RECEIVED');
  const t3 = find('T3_JSON_PARSED');
  const t4 = find('T4_PROCESSING_START');
  const t5 = find('T5_PROCESSING_COMPLETE');
  const t6 = find('T6_RENDER_START');
  const t7 = find('T7_LAYERS_CONSTRUCTED');
  const tEnd = find('T_END_FIRST_RENDER');

  const fmt = (a?: number, b?: number) =>
    a != null && b != null ? `${(b - a).toFixed(1)}ms` : 'N/A';

  console.table({
    'Network (fetch)':       { duration: fmt(t1, t2) },
    'JSON Parse':            { duration: fmt(t2, t3) },
    'Data Processing':       { duration: fmt(t4, t5) },
    'Layer Construction':    { duration: fmt(t6, t7) },
    'First Render':          { duration: fmt(t7, tEnd) },
    'TOTAL (T1 → T_END)':   { duration: fmt(t1, tEnd) },
  });

  // Plot count if available
  const plotCount = metrics.entries.find(
    e => e.label === 'T5_PROCESSING_COMPLETE'
  )?.metadata?.plotCount;
  if (plotCount) {
    console.log(`  Total plots processed: ${plotCount}`);
  }
}

/**
 * Export all metrics as a CSV string (also copies to clipboard).
 */
export function exportMetricsCSV(): string {
  const rows = metrics.entries.map(e => ({
    session_id: metrics.sessionId,
    label: e.label,
    timestamp_ms: e.timestamp.toFixed(2),
    relative_ms: (e.timestamp - metrics.startTime).toFixed(2),
    metadata: e.metadata ? JSON.stringify(e.metadata) : '',
  }));

  const headers = Object.keys(rows[0] || {}).join(',');
  const csvRows = rows.map(r => Object.values(r).join(','));
  const csv = [headers, ...csvRows].join('\n');

  // Copy to clipboard if available
  if (navigator.clipboard) {
    navigator.clipboard.writeText(csv).then(() => {
      console.log('%c📋 CSV copied to clipboard!', 'color: #00ff88;');
    });
  }

  console.log(csv);
  return csv;
}
