import React from 'react';

/**
 * Right-panel metrics display.
 * Shows key risk/return metrics in Bloomberg terminal style.
 *
 * Props:
 *   analytics: object from /portfolio/analytics
 */
const MetricRow = ({ label, value, positive, negative, format = 'number' }) => {
  let displayValue = '—';
  let colorClass = 'text-green-400';

  if (value !== null && value !== undefined) {
    if (format === 'pct') {
      displayValue = `${(value * 100).toFixed(2)}%`;
    } else if (format === 'currency') {
      displayValue = `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else {
      displayValue = typeof value === 'number' ? value.toFixed(4) : String(value);
    }

    if (positive !== undefined) {
      colorClass = value >= 0 ? 'text-green-400' : 'text-red-400';
    }
    if (negative !== undefined) {
      colorClass = value <= 0 ? 'text-red-400' : 'text-green-400';
    }
  }

  return (
    <div className="flex justify-between items-center py-1 border-b border-gray-800">
      <span className="text-gray-500 text-xs uppercase tracking-wide">{label}</span>
      <span className={`text-xs font-bold font-mono ${colorClass}`}>{displayValue}</span>
    </div>
  );
};

const MetricsPanel = ({ analytics = {} }) => {
  return (
    <div className="space-y-4">
      {/* Returns */}
      <div>
        <h4 className="text-yellow-500 text-xs font-bold uppercase tracking-wider mb-2">Returns</h4>
        <MetricRow label="Total Return"  value={analytics.total_return}  format="pct" positive />
        <MetricRow label="CAGR"          value={analytics.cagr}          format="pct" positive />
      </div>

      {/* Risk */}
      <div>
        <h4 className="text-yellow-500 text-xs font-bold uppercase tracking-wider mb-2">Risk</h4>
        <MetricRow label="Volatility"    value={analytics.volatility}    format="pct" />
        <MetricRow label="Max Drawdown"  value={analytics.max_drawdown}  format="pct" negative />
        <MetricRow label="DD Duration"   value={analytics.max_drawdown_duration} />
      </div>

      {/* Ratios */}
      <div>
        <h4 className="text-yellow-500 text-xs font-bold uppercase tracking-wider mb-2">Ratios</h4>
        <MetricRow label="Sharpe"        value={analytics.sharpe}        positive />
        <MetricRow label="Sortino"       value={analytics.sortino}       positive />
      </div>

      {/* VaR */}
      <div>
        <h4 className="text-yellow-500 text-xs font-bold uppercase tracking-wider mb-2">Value at Risk (95%)</h4>
        <MetricRow label="Historical"    value={analytics.var_95_hist}   format="pct" negative />
        <MetricRow label="Parametric"    value={analytics.var_95_param}  format="pct" negative />
      </div>
    </div>
  );
};

export default MetricsPanel;
