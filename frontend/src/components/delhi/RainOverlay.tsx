import { useEffect, useRef } from 'react';

// Subtle, data-driven rainfall animation over the map.
//
// Rules (design mandate):
// - intensity (mm/h) comes ONLY from actual model/forcing data
// - UNKNOWN or zero rainfall  -> no animation at all (no invented rain)
// - honors prefers-reduced-motion (renders nothing)
// - never blocks interaction (pointer-events: none) and never hides
//   information (low opacity streaks behind panel layers)

interface RainOverlayProps {
  intensityMmH: number | null; // null = UNKNOWN/unavailable -> no rain
}

const STREAK_COUNT = 90;
const MAX_SPEED = 340; // px/s at the strongest modeled intensity
const MAX_INTENSITY = 30; // mm/h mapped to MAX_SPEED (capped, linear below)

const RainOverlay = ({ intensityMmH }: RainOverlayProps) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const intensityRef = useRef<number>(0);
  const rafRef = useRef<number | null>(null);

  intensityRef.current =
    intensityMmH === null || intensityMmH <= 0
      ? 0
      : Math.min(intensityMmH, MAX_INTENSITY);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return; // static indicator is handled by the parent chip

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let streaks: { x: number; y: number; len: number; speed: number }[] = [];
    let running = true;
    let lastTs = 0;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
      streaks = Array.from({ length: STREAK_COUNT }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        len: 9 + Math.random() * 14,
        speed: 0.5 + Math.random() * 0.5,
      }));
    };
    resize();
    const observer = new ResizeObserver(resize);
    if (canvas.parentElement) observer.observe(canvas.parentElement);

    const frame = (ts: number) => {
      if (!running) return;
      const dt = Math.min((ts - lastTs) / 1000, 0.05);
      lastTs = ts;
      const intensity = intensityRef.current;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (intensity > 0) {
        const alpha = 0.10 + 0.14 * (intensity / MAX_INTENSITY);
        ctx.strokeStyle = `rgba(56, 155, 220, ${alpha.toFixed(3)})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (const s of streaks) {
          const v = MAX_SPEED * (intensity / MAX_INTENSITY) * s.speed;
          const y2 = s.y + s.len;
          ctx.moveTo(s.x, s.y);
          ctx.lineTo(s.x + 1.5, y2);
          s.y += v * dt;
          s.x += v * dt * 0.06;
          if (s.y > canvas.height) {
            s.y = -s.len;
            s.x = Math.random() * canvas.width;
          }
          if (s.x > canvas.width) s.x = 0;
        }
        ctx.stroke();
      }
      rafRef.current = requestAnimationFrame(frame);
    };
    rafRef.current = requestAnimationFrame(frame);

    return () => {
      running = false;
      observer.disconnect();
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const raining = intensityMmH !== null && intensityMmH > 0;
  return (
    <canvas
      ref={canvasRef}
      className={`rain-overlay ${raining ? 'raining' : ''}`}
      aria-hidden="true"
    />
  );
};

export default RainOverlay;
