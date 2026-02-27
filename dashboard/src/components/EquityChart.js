import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

/**
 * Equity curve chart with Bloomberg-style dark theme.
 *
 * Props:
 *   data        : array of { index: number, equity: number }
 *   title       : string
 *   color       : string (default '#00ff88')
 *   initialValue: number (reference line for break-even)
 */
const EquityChart = ({ data = [], title = 'Portfolio Equity', color = '#00ff88', initialValue }) => {
  const isPositive = data.length > 0 && data[data.length - 1]?.equity >= (initialValue || data[0]?.equity);
  const lineColor = isPositive ? '#00ff88' : '#ff4444';

  const formatValue = (v) => `$${v?.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const val = payload[0].value;
      const diff = initialValue ? val - initialValue : 0;
      const pct = initialValue ? ((diff / initialValue) * 100).toFixed(2) : 0;
      return (
        <div className="bg-gray-900 border border-green-700 p-2 text-xs">
          <p className="text-gray-400">Step {label}</p>
          <p className="text-green-400 font-bold">{formatValue(val)}</p>
          {initialValue && (
            <p className={diff >= 0 ? 'text-green-400' : 'text-red-400'}>
              {diff >= 0 ? '+' : ''}{formatValue(diff)} ({pct}%)
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-950 border border-green-900 rounded p-4 mb-4">
      <h3 className="text-green-400 text-sm font-bold mb-3 uppercase tracking-wider">{title}</h3>
      {data.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-600 text-sm">
          No data — run research to populate chart
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={lineColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={lineColor} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2a1a" />
            <XAxis dataKey="index" tick={{ fill: '#4a7a4a', fontSize: 10 }} />
            <YAxis tickFormatter={formatValue} tick={{ fill: '#4a7a4a', fontSize: 10 }} width={80} />
            <Tooltip content={<CustomTooltip />} />
            {initialValue && (
              <ReferenceLine y={initialValue} stroke="#666" strokeDasharray="4 4" />
            )}
            <Area
              type="monotone"
              dataKey="equity"
              stroke={lineColor}
              strokeWidth={2}
              fill="url(#equityGradient)"
              dot={false}
              activeDot={{ r: 4, fill: lineColor }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default EquityChart;
