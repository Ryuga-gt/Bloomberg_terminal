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
  if (active && payload && payload.length) {
    const value = payload[0].value;
    const color = value >= 0 ? '#00ff88' : '#ff4d4f';
    return (
      <div style={{
        background: '#0d1117',
        border: '1px solid #1f2937',
        padding: '8px 12px',
        fontFamily: 'Courier New, monospace',
        fontSize: '11px',
      }}>
        <div style={{ color: '#9ca3af', marginBottom: '4px' }}>{label}</div>
        <div style={{ color }}>
          ${typeof value === 'number' ? value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : value}
        </div>
      </div>
    );
  }
  return null;
};

const EquityChart = ({ data }) => {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      // Generate placeholder data
      return Array.from({ length: 50 }, (_, i) => ({
        date: `Day ${i + 1}`,
        value: 100000 + Math.sin(i * 0.3) * 5000 + i * 200,
      }));
    }
    return data;
  }, [data]);

  const initialValue = chartData.length > 0 ? chartData[0].value : 100000;
  const lastValue = chartData.length > 0 ? chartData[chartData.length - 1].value : 100000;
  const isPositive = lastValue >= initialValue;

  const gradientId = isPositive ? 'greenGradient' : 'redGradient';
  const strokeColor = isPositive ? '#00ff88' : '#ff4d4f';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={chartData}
        margin={{ top: 10, right: 10, left: 10, bottom: 5 }}
      >
        <defs>
          <linearGradient id="greenGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#00ff88" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#00ff88" stopOpacity={0.02} />
          </linearGradient>
          <linearGradient id="redGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ff4d4f" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#ff4d4f" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(31, 41, 55, 0.5)"
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tick={{ fill: '#4b5563', fontSize: 10, fontFamily: 'Courier New' }}
          axisLine={{ stroke: '#1f2937' }}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: '#4b5563', fontSize: 10, fontFamily: 'Courier New' }}
          axisLine={{ stroke: '#1f2937' }}
          tickLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          width={55}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#374151', strokeWidth: 1 }} />
        <ReferenceLine
          y={initialValue}
          stroke="#374151"
          strokeDasharray="4 4"
          label={{ value: 'INITIAL', fill: '#4b5563', fontSize: 9, fontFamily: 'Courier New' }}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke={strokeColor}
          strokeWidth={1.5}
          fill={`url(#${gradientId})`}
          dot={false}
          activeDot={{ r: 3, fill: strokeColor, stroke: 'none' }}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default EquityChart;
