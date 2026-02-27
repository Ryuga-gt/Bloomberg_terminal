import React, { useMemo } from 'react';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  const equity = payload.find((p) => p.dataKey === 'value');
  const val = equity?.value;
  const color = val == null ? '#9ca3af' : val >= (payload[0]?.payload?.initial ?? val) ? '#00d4aa' : '#ff4d4f';

  return (
    <div className="bq-tooltip">
      <div style={{ color: 'var(--text-muted)', marginBottom: '6px', fontSize: '10px' }}>{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', marginBottom: '2px' }}>
          <span style={{ color: 'var(--text-label)', fontSize: '10px' }}>{p.name}</span>
          <span style={{ color: p.color, fontWeight: '600' }}>
            {p.dataKey === 'value'
              ? `$${typeof p.value === 'number' ? p.value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) : '--'}`
              : typeof p.value === 'number' ? p.value.toFixed(4) : '--'}
          </span>
        </div>
      ))}
    </div>
  );
};

const EquityChart = ({ data, initialCapital }) => {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      // Placeholder
      return Array.from({ length: 60 }, (_, i) => ({
        date: `T${i}`,
        value: 100000 + Math.sin(i * 0.25) * 8000 + i * 300,
        initial: 100000,
      }));
    }
    const ic = initialCapital ?? data[0]?.value ?? 100000;
    return data.map((d) => ({ ...d, initial: ic }));
  }, [data, initialCapital]);

  const ic = chartData[0]?.initial ?? 100000;
  const lastVal = chartData[chartData.length - 1]?.value ?? ic;
  const isPositive = lastVal >= ic;
  const strokeColor = isPositive ? '#00d4aa' : '#ff4d4f';
  const gradId = isPositive ? 'eqGreen' : 'eqRed';

  // Tick formatter
  const yFmt = (v) => `$${(v / 1000).toFixed(0)}k`;
  const xFmt = (v) => {
    const n = parseInt(v?.replace('T', '') ?? '0', 10);
    if (n % Math.max(1, Math.floor(chartData.length / 6)) !== 0) return '';
    return `T${n}`;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
        <defs>
          <linearGradient id="eqGreen" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#00d4aa" stopOpacity={0.18} />
            <stop offset="95%" stopColor="#00d4aa" stopOpacity={0.01} />
          </linearGradient>
          <linearGradient id="eqRed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#ff4d4f" stopOpacity={0.18} />
            <stop offset="95%" stopColor="#ff4d4f" stopOpacity={0.01} />
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
          width={52}
        />

        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#2d3f55', strokeWidth: 1, strokeDasharray: '3 3' }} />

        <ReferenceLine
          y={ic}
          stroke="#2d3f55"
          strokeDasharray="4 4"
          label={{ value: 'INITIAL', fill: '#4b5563', fontSize: 8, fontFamily: 'IBM Plex Mono, monospace', position: 'insideTopRight' }}
        />

        <Area
          type="monotone"
          dataKey="value"
          name="Equity"
          stroke={strokeColor}
          strokeWidth={1.5}
          fill={`url(#${gradId})`}
          dot={false}
          activeDot={{ r: 3, fill: strokeColor, stroke: 'var(--bg-primary)', strokeWidth: 2 }}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default EquityChart;
