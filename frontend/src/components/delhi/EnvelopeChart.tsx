import { useMemo, useState } from 'react';

// Compact SVG chart for ensemble envelopes and hydrographs.
// Deliberately dependency-free: renders deterministic data with explicit
// UNKNOWN handling (null values produce gaps with visible markers —
// never zero-filled points), real timestamps, and hover tooltips.

export interface EnvelopePoint {
  time_start: string;
  min_m3_s: number | null;
  median_m3_s: number | null;
  max_m3_s: number | null;
}

export interface SeriesPoint {
  time: string;
  value: number | null;
}

interface EnvelopeChartProps {
  envelope?: EnvelopePoint[];
  series?: { points: SeriesPoint[]; color: string; dash?: boolean }[];
  height?: number;
  yLabel?: string;
  timeLabel?: (iso: string) => string;
}

function fmtTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const EnvelopeChart = ({
  envelope,
  series,
  height = 170,
  yLabel = 'm³/s',
  timeLabel = fmtTime,
}: EnvelopeChartProps) => {
  const width = 640;
  const padL = 46;
  const padR = 12;
  const padT = 14;
  const padB = 26;
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const xValues: string[] = useMemo(() => {
    const set: string[] = [];
    if (envelope) envelope.forEach((p) => set.push(p.time_start));
    series?.forEach((s) =>
      s.points.forEach((p) => {
        if (!set.includes(p.time)) set.push(p.time);
      }),
    );
    return set.sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
  }, [envelope, series]);

  const xPx = (i: number) => padL + ((width - padL - padR) * i) / Math.max(xValues.length - 1, 1);

  let yMax = 0;
  envelope?.forEach((p) => {
    if (p.max_m3_s !== null) yMax = Math.max(yMax, p.max_m3_s);
  });
  series?.forEach((s) =>
    s.points.forEach((p) => {
      if (p.value !== null) yMax = Math.max(yMax, p.value);
    }),
  );
  if (yMax === 0) yMax = 1;
  yMax *= 1.12;

  const innerH = height - padT - padB;
  const yPx = (v: number) => padT + innerH - (innerH * v) / yMax;

  const linePath = (pts: (number | null)[]) => {
    let d = '';
    let pen = false;
    pts.forEach((v, i) => {
      if (v === null) {
        pen = false;
        return;
      }
      d += `${pen ? 'L' : 'M'}${xPx(i).toFixed(1)},${yPx(v).toFixed(1)} `;
      pen = true;
    });
    return d.trim();
  };

  // Envelope band: upper bounds forward, then lower bounds reversed, closed.
  // If any bound is UNKNOWN (null), no band is drawn — never guessed.
  const bandPath = (env: EnvelopePoint[]) => {
    const pts = env.map((e) => ({
      x: xPx(xValues.indexOf(e.time_start)),
      up: e.max_m3_s,
      lo: e.min_m3_s,
    }));
    if (pts.length < 2 || pts.some((p) => p.up === null || p.lo === null)) return '';
    const upper = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${yPx(p.up!)}`).join(' ');
    const lower = [...pts]
      .reverse()
      .map((p) => `L${p.x},${yPx(p.lo!)}`)
      .join(' ');
    return `${upper} ${lower} Z`;
  };

  const yTicks = 4;

  // Tooltip content for the hovered column.
  const hoverData = (() => {
    if (hoverIdx === null || !xValues[hoverIdx]) return null;
    const t = xValues[hoverIdx];
    const env = envelope?.find((e) => e.time_start === t);
    const vals = (series ?? [])
      .map((s) => {
        const p = s.points.find((q) => q.time === t);
        return { color: s.color, value: p?.value ?? null };
      })
      .filter((v) => v.value !== null);
    return { t, env, vals };
  })();

  return (
    <div className="chart-wrap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="delhi-chart"
        role="img"
        aria-label="Inflow chart"
        onMouseLeave={() => setHoverIdx(null)}
      >
        {Array.from({ length: yTicks + 1 }, (_, i) => {
          const v = (yMax * i) / yTicks;
          return (
            <g key={i}>
              <line x1={padL} x2={width - padR} y1={yPx(v)} y2={yPx(v)} stroke="#eef2f7" strokeWidth={1} />
              <text x={padL - 6} y={yPx(v) + 3.5} textAnchor="end" fontSize={10} fill="#64748b">
                {v >= 100 ? v.toFixed(0) : v.toFixed(1)}
              </text>
            </g>
          );
        })}
        {xValues.map((t, i) =>
          i % Math.ceil(xValues.length / 6) === 0 ? (
            <text key={t} x={xPx(i)} y={height - 8} textAnchor="middle" fontSize={10} fill="#64748b">
              {timeLabel(t)}
            </text>
          ) : null,
        )}

        {/* hover hit areas */}
        {xValues.map((t, i) => (
          <rect
            key={`hit-${t}`}
            x={xPx(i) - (width - padL - padR) / (2 * Math.max(xValues.length - 1, 1))}
            y={padT}
            width={(width - padL - padR) / Math.max(xValues.length - 1, 1)}
            height={innerH}
            fill="transparent"
            onMouseEnter={() => setHoverIdx(i)}
          />
        ))}

        {hoverIdx !== null && (
          <line
            x1={xPx(hoverIdx)}
            x2={xPx(hoverIdx)}
            y1={padT}
            y2={padT + innerH}
            stroke="#94a3b8"
            strokeWidth={1}
            strokeDasharray="3 3"
          />
        )}

        {envelope && envelope.length > 0 && (
          <>
            <path d={bandPath(envelope)} fill="#0284c7" fillOpacity={0.14} stroke="none" />
            <path
              d={linePath(envelope.map((e) => e.median_m3_s))}
              fill="none"
              stroke="#0284c7"
              strokeWidth={2}
            />
          </>
        )}
        {series?.map((s, idx) => (
          <path
            key={idx}
            d={linePath(s.points.map((p) => p.value))}
            fill="none"
            stroke={s.color}
            strokeWidth={1.4}
            strokeDasharray={s.dash ? '4 3' : undefined}
            opacity={0.85}
          />
        ))}

        {/* UNKNOWN markers: nulls are gaps, visually distinct from zero */}
        {xValues.map((t, i) => {
          const envNull = envelope?.find((e) => e.time_start === t)?.median_m3_s === null;
          const seriesAllNull =
            series && series.length > 0 &&
            series.every((s) => {
              const p = s.points.find((q) => q.time === t);
              return p ? p.value === null : false;
            });
          if (!envNull && !seriesAllNull) return null;
          return (
            <g key={`unk-${t}`}>
              <line
                x1={xPx(i)}
                x2={xPx(i)}
                y1={padT + innerH - 8}
                y2={padT + innerH}
                stroke="#b45309"
                strokeWidth={1.5}
                strokeDasharray="2 2"
              />
              <text x={xPx(i)} y={padT + innerH - 11} textAnchor="middle" fontSize={8.5} fill="#b45309">
                UNKNOWN
              </text>
            </g>
          );
        })}
        <text x={4} y={padT + 8} fontSize={10} fill="#334155">
          {yLabel}
        </text>
      </svg>

      {hoverData && (
        <div
          className="chart-tooltip"
          style={{
            left: `${(xPx(hoverIdx!) / width) * 100}%`,
          }}
        >
          <div className="tt-time">{timeLabel(hoverData.t)}</div>
          {hoverData.env && (
            <div className="tt-row">
              <span className="tt-swatch" style={{ background: '#0284c7' }} />
              ensemble {hoverData.env.min_m3_s === null
                ? 'UNKNOWN'
                : `${hoverData.env.min_m3_s.toFixed(1)}–${hoverData.env.max_m3_s?.toFixed(1)}`}
              {hoverData.env.median_m3_s !== null && (
                <span className="tt-median"> · med {hoverData.env.median_m3_s.toFixed(1)}</span>
              )}
            </div>
          )}
          {hoverData.vals.slice(0, 3).map((v, i) => (
            <div key={i} className="tt-row">
              <span className="tt-swatch" style={{ background: v.color }} />
              {v.value!.toFixed(1)} {yLabel}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EnvelopeChart;
