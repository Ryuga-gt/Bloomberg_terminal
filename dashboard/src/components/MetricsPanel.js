import React from 'react';

const fmtPct = (v, decimals = 2) =>
  v == null ? '--' : `${(v * 100).toFixed(decimals)}%`;

const fmtNum = (v, decimals = 2) =>
  v == null ? '--' : v.toFixed(decimals);

const fmtInt = (v) =>
  v == null ? '--' : Math.round(v).toLocaleString();

const getColor = (v, type) => {
  if (v == null) return 'var(--text-muted)';
  switch (type) {
    case 'return':
    case 'cagr':
      return v > 0 ? 'var(--accent-green)' : v < 0 ? 'var(--accent-red)' : 'var(--text-secondary)';
    case 'sharpe':
    case 'sortino':
      return v > 1.5 ? 'var(--accent-green)' : v > 0.5 ? 'var(--accent-yellow)' : v > 0 ? 'var(--text-secondary)' : 'var(--accent-red)';
    case 'drawdown':
      return v < -0.3 ? 'var(--accent-red)' : v < -0.15 ? 'var(--accent-yellow)' : 'var(--accent-green)';
    case 'var':
      return 'var(--accent-red)';
    case 'vol':
      return v > 0.3 ? 'var(--accent-red)' : v > 0.15 ? 'var(--accent-yellow)' : 'var(--accent-green)';
    default:
      return 'var(--text-secondary)';
  }
};

const MetricRow = ({ label, value, color, suffix = '' }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 14px',
    borderBottom: '1px solid rgba(30, 42, 58, 0.5)',
  }}>
    <span style={{ fontSize: '10px', color: 'var(--text-label)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
      {label}
    </span>
    <span style={{ fontSize: '12px', color: color || 'var(--text-secondary)', fontWeight: '600', fontFamily: 'var(--font-mono)', letterSpacing: '0.02em' }}>
      {value}{suffix}
    </span>
  </div>
);

const SectionHeader = ({ title }) => (
  <div style={{
    padding: '5px 14px',
    background: 'var(--bg-header)',
    borderBottom: '1px solid var(--border-color)',
    fontSize: '9px',
    color: 'var(--accent-orange)',
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    fontWeight: '600',
  }}>
    {title}
  </div>
);

const MetricsPanel = ({ metrics, mode }) => {
  const m = metrics || {};

  // Full mode (default) — all metrics
  if (!mode || mode === 'full') {
    return (
      <div style={{ height: '100%', overflow: 'auto' }}>
        <SectionHeader title="Returns" />
        <MetricRow label="Total Return"  value={fmtPct(m.total_return)}  color={getColor(m.total_return, 'return')} />
        <MetricRow label="CAGR"          value={fmtPct(m.cagr)}          color={getColor(m.cagr, 'cagr')} />

        <SectionHeader title="Risk-Adjusted" />
        <MetricRow label="Sharpe Ratio"  value={fmtNum(m.sharpe)}        color={getColor(m.sharpe, 'sharpe')} />
        <MetricRow label="Sortino Ratio" value={fmtNum(m.sortino)}       color={getColor(m.sortino, 'sortino')} />

        <SectionHeader title="Drawdown" />
        <MetricRow label="Max Drawdown"  value={fmtPct(m.max_drawdown)}  color={getColor(m.max_drawdown, 'drawdown')} />
        <MetricRow label="DD Duration"   value={fmtInt(m.max_drawdown_duration)} color="var(--text-secondary)" suffix=" bars" />

        <SectionHeader title="Risk" />
        <MetricRow label="Volatility"    value={fmtPct(m.volatility)}    color={getColor(m.volatility, 'vol')} />
        <MetricRow label="VaR 95% (Hist)" value={fmtPct(m.var_95_hist ?? m.var_95)} color="var(--accent-red)" />
        <MetricRow label="VaR 95% (Param)" value={fmtPct(m.var_95_param)} color="var(--accent-red)" />
      </div>
    );
  }

  if (mode === 'risk') {
    return (
      <div style={{ height: '100%', overflow: 'auto' }}>
        <SectionHeader title="Drawdown" />
        <MetricRow label="Max Drawdown"  value={fmtPct(m.max_drawdown)}  color={getColor(m.max_drawdown, 'drawdown')} />
        <MetricRow label="DD Duration"   value={fmtInt(m.max_drawdown_duration)} color="var(--text-secondary)" suffix=" bars" />

        <SectionHeader title="Volatility" />
        <MetricRow label="Annualised Vol" value={fmtPct(m.volatility)}   color={getColor(m.volatility, 'vol')} />

        <SectionHeader title="Risk-Adjusted" />
        <MetricRow label="Sharpe Ratio"  value={fmtNum(m.sharpe)}        color={getColor(m.sharpe, 'sharpe')} />
        <MetricRow label="Sortino Ratio" value={fmtNum(m.sortino)}       color={getColor(m.sortino, 'sortino')} />
      </div>
    );
  }

  if (mode === 'var') {
    return (
      <div style={{ height: '100%', overflow: 'auto' }}>
        <SectionHeader title="Value at Risk" />
        <MetricRow label="VaR 95% Historical" value={fmtPct(m.var_95_hist ?? m.var_95)} color="var(--accent-red)" />
        <MetricRow label="VaR 95% Parametric" value={fmtPct(m.var_95_param)} color="var(--accent-red)" />

        <SectionHeader title="Returns" />
        <MetricRow label="Total Return"  value={fmtPct(m.total_return)}  color={getColor(m.total_return, 'return')} />
        <MetricRow label="CAGR"          value={fmtPct(m.cagr)}          color={getColor(m.cagr, 'cagr')} />
      </div>
    );
  }

  return null;
};

export default MetricsPanel;
