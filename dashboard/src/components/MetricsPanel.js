import React from 'react';

const MetricRow = ({ label, value, format = 'number', suffix = '' }) => {
  const formatValue = (val) => {
    if (val === undefined || val === null) return '--';
    if (typeof val !== 'number') return val;
    return val.toFixed(2);
  };

  const getColor = (val, metricType) => {
    if (val === undefined || val === null) return '#9ca3af';
    if (metricType === 'drawdown' || metricType === 'var') {
      return val < 0 ? '#ff4d4f' : '#9ca3af';
    }
    if (metricType === 'return' || metricType === 'cagr') {
      return val > 0 ? '#00ff88' : val < 0 ? '#ff4d4f' : '#9ca3af';
    }
    if (metricType === 'sharpe' || metricType === 'sortino') {
      return val > 1 ? '#00ff88' : val > 0 ? '#fbbf24' : '#ff4d4f';
    }
    return '#9ca3af';
  };

  const color = getColor(value, format);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '5px 12px',
      borderBottom: '1px solid rgba(31, 41, 55, 0.4)',
      fontFamily: 'Courier New, monospace',
    }}>
      <span style={{ fontSize: '11px', color: '#6b7280', letterSpacing: '0.05em' }}>
        {label}
      </span>
      <span style={{ fontSize: '12px', color, fontWeight: 'bold', letterSpacing: '0.05em' }}>
        {formatValue(value)}{suffix}
      </span>
    </div>
  );
};

const MetricsPanel = ({ metrics }) => {
  const m = metrics || {};

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <MetricRow label="TOTAL RETURN" value={m.total_return} format="return" suffix="%" />
      <MetricRow label="CAGR" value={m.cagr} format="cagr" suffix="%" />
      <MetricRow label="SHARPE RATIO" value={m.sharpe} format="sharpe" />
      <MetricRow label="SORTINO RATIO" value={m.sortino} format="sortino" />
      <MetricRow label="MAX DRAWDOWN" value={m.max_drawdown} format="drawdown" suffix="%" />
      <MetricRow label="VAR 95%" value={m.var_95_hist ?? m.var_95} format="var" suffix="%" />
      <MetricRow label="VOLATILITY" value={m.volatility} format="number" suffix="%" />
      <MetricRow label="WIN RATE" value={m.win_rate} format="return" suffix="%" />
      <MetricRow label="PROFIT FACTOR" value={m.profit_factor} format="sharpe" />
      <MetricRow label="TRADES" value={m.num_trades} format="neutral" />
    </div>
  );
};

export default MetricsPanel;
