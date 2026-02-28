import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

const CustomTooltip = ({ active, payload, label, metricLabel, color }) => {
  if (!active || !payload || !payload.length) return null;
  const val = payload[0]?.value;
  return (
    <div className="bq-tooltip">
      <div style={{ color: 'var(--text-muted)', marginBottom: '4px', fontSize: '10px' }}>{label}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
        <span style={{ color: 'var(--text-label)', fontSize: '10px' }}>{metricLabel}</span>
        <span style={{ color, fontWeight: '600' }}>
          {val != null ? val.toFixed(3) : '--'}
        </span>
      </div>
    </div>
  );
};

const RollingMetricsChart = ({ data, metric = 'sharpe', color = 'var(--accent-orange)' }) => {
  const metricLabel = metric === 'sharpe' ? 'ROLLING SHARPE' : 'ROLLING VOL';

  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      // Placeholder
      return Array.from({ length: 60 }, (_, i) => ({
        date: `T${i}`,
        value: metric === 'sharpe'
          ? Math.sin(i * 0.2) * 0.8 + 0.5
          : 0.15 + Math.abs(Math.sin(i * 0.15)) * 0.1,
      }));
    }
    return data
      .filter((d) => d[metric] != null)
      .map((d) => ({ date: d.date, value: d[metric] }));
  }, [data, metric]);

  const values = chartData.map((d) => d.value).filter((v) => v != null);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const padding = (maxVal - minVal) * 0.1 || 0.1;

  const yFmt = (v) => v.toFixed(2);
  const xFmt = (v) => {
    const n = parseInt(v?.replace('T', '') ?? '0', 10);
    if (n % Math.max(1, Math.floor(chartData.length / 6)) !== 0) return '';
    return `T${n}`;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
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
          domain={[minVal - padding, maxVal + padding]}
        />

        <Tooltip
          content={(props) => <CustomTooltip {...props} metricLabel={metricLabel} color={color} />}
          cursor={{ stroke: '#2d3f55', strokeWidth: 1, strokeDasharray: '3 3' }}
        />

        {/* Zero line for Sharpe */}
        {metric === 'sharpe' && (
          <ReferenceLine y={0} stroke="#2d3f55" strokeWidth={1} />
        )}
        {/* Sharpe = 1 reference */}
        {metric === 'sharpe' && (
          <ReferenceLine
            y={1}
            stroke={color}
            strokeDasharray="4 4"
            strokeOpacity={0.35}
            label={{ value: 'SR=1', fill: color, fontSize: 8, fontFamily: 'IBM Plex Mono, monospace', position: 'insideTopRight', opacity: 0.6 }}
          />
        )}

        <Line
          type="monotone"
          dataKey="value"
          name={metricLabel}
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          activeDot={{ r: 3, fill: color, stroke: 'var(--bg-primary)', strokeWidth: 2 }}
          isAnimationActive={false}
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default RollingMetricsChart;
