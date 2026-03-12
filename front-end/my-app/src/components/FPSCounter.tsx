import { useEffect, useRef, useState } from 'react';
import { PERF_MODE } from '../utils/perfUtils';

/**
 * Lightweight FPS counter overlay for performance benchmarking.
 * Only renders when VITE_PERF_MODE=true.
 * 
 * Tracks frames-per-second using requestAnimationFrame and displays
 * a live overlay with current, average, and minimum FPS.
 */
const FPSCounter: React.FC = () => {
  const [fps, setFps] = useState(0);
  const [avgFps, setAvgFps] = useState(0);
  const [minFps, setMinFps] = useState(Infinity);
  const frameCount = useRef(0);
  const lastTime = useRef(performance.now());
  const fpsHistory = useRef<number[]>([]);
  const rafId = useRef<number>(0);

  useEffect(() => {
    if (!PERF_MODE) return;

    const tick = () => {
      frameCount.current++;
      const now = performance.now();
      const delta = now - lastTime.current;

      // Update every 500ms
      if (delta >= 500) {
        const currentFps = Math.round((frameCount.current / delta) * 1000);
        setFps(currentFps);

        fpsHistory.current.push(currentFps);
        // Keep last 60 samples (~30 seconds)
        if (fpsHistory.current.length > 60) fpsHistory.current.shift();

        const avg = Math.round(
          fpsHistory.current.reduce((a, b) => a + b, 0) / fpsHistory.current.length
        );
        setAvgFps(avg);
        setMinFps(prev => Math.min(prev, currentFps));

        frameCount.current = 0;
        lastTime.current = now;
      }

      rafId.current = requestAnimationFrame(tick);
    };

    rafId.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId.current);
  }, []);

  if (!PERF_MODE) return null;

  const fpsColor = fps >= 50 ? '#00ff88' : fps >= 30 ? '#ffaa00' : '#ff4444';

  return (
    <div
      style={{
        position: 'fixed',
        top: 10,
        right: 10,
        background: 'rgba(0, 0, 0, 0.85)',
        color: '#fff',
        padding: '8px 12px',
        borderRadius: 8,
        fontFamily: 'monospace',
        fontSize: 13,
        zIndex: 99999,
        border: `1px solid ${fpsColor}`,
        minWidth: 120,
        pointerEvents: 'none',
        userSelect: 'none',
      }}
    >
      <div style={{ color: fpsColor, fontSize: 22, fontWeight: 'bold', lineHeight: 1 }}>
        {fps} FPS
      </div>
      <div style={{ marginTop: 4, opacity: 0.8, fontSize: 11 }}>
        avg: {avgFps} &nbsp; min: {minFps === Infinity ? '—' : minFps}
      </div>
      <div style={{ marginTop: 2, opacity: 0.5, fontSize: 10 }}>
        🔬 PERF MODE
      </div>
    </div>
  );
};

export default FPSCounter;
