import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  const dd = payload[0]?.value;
  return (
    <div className="bq-tooltip">
      <div style={{ color: 'var(--text-muted)', marginBottom: '4px', fontSize: '10px' }}>{label}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
        <span style={{ color: 'var(--text-label)', fontSize: '10px' }}>DRAWDOWN</span>
        <span style={{ color: 'var(--accent-red)', fontWeight: '600' }}>
          {dd != null ? `${(dd * 100).toFixed(2)}%` : '--'}
        </span>
      </div>
    </div>
  );
};

/**
 * Computes the running drawdown series from an equity curve [{date, value}].
 * Returns [{date, drawdown}] where drawdown is a negative fraction (e.g. -0.15 = -15%).
 */
function computeDrawdown(data) {
  if (!data || data.length === 0) return [];
  let peak = data[0].value;
  return data.map((d) => {
    if (d.value > peak) peak = d.value;
    const dd = peak > 0 ? (d.value - peak) / peak : 0;
    return { date: d.date, drawdown: dd };
  });
}

const DrawdownChart = ({ data }) => {
  const ddData = useMemo(() => {
    if (!data || data.length === 0) {
      // Placeholder
      return Array.from({ length: 60 }, (_, i) => ({
        date: `T${i}`,
        drawdown: -Math.abs(Math.sin(i * 0.2) * 0.12),
      }));
    }
    return computeDrawdown(data);
  }, [data]);

  const minDD = useMemo(() =>
    Math.min(0, ...ddData.map((d) => d.drawdown ?? 0)),
    [ddData]
  );

  const yFmt = (v) => `${(v * 100).toFixed(0)}%`;
  const xFmt = (v) => {
    const n = parseInt(v?.replace('T', '') ?? '0', 10);
    if (n % Math.max(1, Math.floor(ddData.length / 6)) !== 0) return '';
    return `T${n}`;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={ddData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
        <defs>
          <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#ff4d4f" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#ff4d4f" stopOpacity={0.02} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="2 4" stroke="rgba(30,42,58,0.6)" vertical={false} />

        <XAxis
          dataKey="date"
          tickFormatter={xFmt}
          tick={{ fill: '#4b5563', fontSize: 9, fontFamily: 'IBM Plex Mono, monospace' }}
          axisLine={{ stroke: '#1e2a3a' }}
          tickLine={false}
        />
        <YAxis
          tickFormatter={yFmt}
          tick={{ fill: '#4b5563', fontSize: 9, fontFamily: 'IBM Plex Mono, monospace' }}
          axisLine={false}
          tickLine={false}
          width={44}
          domain={[minDD * 1.1, 0.01]}
        />

        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#2d3f55', strokeWidth: 1, strokeDasharray: '3 3' }} />

        <ReferenceLine y={0} stroke="#2d3f55" strokeWidth={1} />

        {/* Max drawdown reference line */}
        {minDD < 0 && (
          <ReferenceLine
            y={minDD}
            stroke="#ff4d4f"
            strokeDasharray="4 4"
            strokeOpacity={0.5}
            label={{ value: `MAX DD ${(minDD * 100).toFixed(1)}%`, fill: '#ff4d4f', fontSize: 8, fontFamily: 'IBM Plex Mono, monospace', position: 'insideBottomRight' }}
          />
        )}

        <Area
          type="monotone"
          dataKey="drawdown"
          name="Drawdown"
          stroke="#ff4d4f"
          strokeWidth={1.5}
          fill="url(#ddGrad)"
          dot={false}
          activeDot={{ r: 3, fill: '#ff4d4f', stroke: 'var(--bg-primary)', strokeWidth: 2 }}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default DrawdownChart;
