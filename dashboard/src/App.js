import React, { useState, useEffect, useRef, useCallback } from 'react';
import './theme.css';
import EquityChart from './components/EquityChart';
import MetricsPanel from './components/MetricsPanel';
import StrategyTable from './components/StrategyTable';
import DrawdownChart from './components/DrawdownChart';
import RollingMetricsChart from './components/RollingMetricsChart';

const DEFAULT_FORM = {
  symbol: 'SPY',
  start_date: '2020-01-01',
  end_date: '2024-01-01',
  initial_capital: 100000,
};

const TABS = [
  { id: 'overview',    label: 'OVERVIEW',    icon: '◈' },
  { id: 'analytics',  label: 'ANALYTICS',   icon: '▸' },
  { id: 'strategies', label: 'STRATEGIES',  icon: '◆' },
  { id: 'risk',       label: 'RISK',        icon: '⚠' },
];

function App() {
  const [activeTab, setActiveTab]         = useState('overview');
  const [equityData, setEquityData]       = useState([]);
  const [metrics, setMetrics]             = useState({});
  const [strategies, setStrategies]       = useState([]);
  const [rollingData, setRollingData]     = useState([]);
  const [isLive, setIsLive]               = useState(false);
  const [portfolioValue, setPortfolioValue] = useState(null);
  const [initialCapital, setInitialCapital] = useState(null);
  const [isLoading, setIsLoading]         = useState(false);
  const [error, setError]                 = useState(null);
  const [showForm, setShowForm]           = useState(true);
  const [form, setForm]                   = useState(DEFAULT_FORM);
  const [currentTime, setCurrentTime]     = useState(new Date());
  const [lastRunSymbol, setLastRunSymbol] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  // Clock
  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;
    try {
      const ws = new WebSocket('ws://localhost:8000/stream/equity');
      ws.onopen = () => {
        setIsLive(true);
        setError(null);
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'equity_update') {
            setEquityData((prev) => {
              const updated = [...prev, { date: `T${prev.length}`, value: data.value }];
              return updated.slice(-500);
            });
            setPortfolioValue(data.value);
          }
        } catch (e) { /* ignore */ }
      };
      ws.onerror = () => setIsLive(false);
      ws.onclose = () => {
        setIsLive(false);
        wsRef.current = null;
        reconnectTimerRef.current = setTimeout(connectWebSocket, 5000);
      };
      wsRef.current = ws;
    } catch (e) {
      setIsLive(false);
      reconnectTimerRef.current = setTimeout(connectWebSocket, 5000);
    }
  }, []);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    };
  }, [connectWebSocket]);

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleRunResearch = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: form.symbol,
          start: form.start_date,
          end: form.end_date,
          initial_capital: Number(form.initial_capital),
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const detail = errData.detail;
        const msg = Array.isArray(detail)
          ? detail.map((e) => `${e.loc ? e.loc.join('.') : ''}: ${e.msg}`).join('; ')
          : (typeof detail === 'string' ? detail : `HTTP ${response.status}`);
        throw new Error(msg);
      }

      const result = await response.json();

      // Map equity_curve: API returns List[float], chart expects [{date, value}]
      if (result.equity_curve && result.equity_curve.length > 0) {
        const mapped = result.equity_curve.map((v, i) => ({ date: `T${i}`, value: v }));
        setEquityData(mapped);
        setPortfolioValue(result.equity_curve[result.equity_curve.length - 1]);
        setInitialCapital(result.equity_curve[0]);
      }

      // Map analytics → metrics
      if (result.analytics) setMetrics(result.analytics);

      // Build rolling metrics data from analytics
      if (result.analytics) {
        const rs = result.analytics.rolling_sharpe_20 || [];
        const rv = result.analytics.rolling_vol_20 || [];
        const maxLen = Math.max(rs.length, rv.length);
        if (maxLen > 0) {
          const rolling = Array.from({ length: maxLen }, (_, i) => ({
            date: `T${i}`,
            sharpe: rs[i] ?? null,
            vol: rv[i] ?? null,
          }));
          setRollingData(rolling);
        }
      }

      // Map ranking_results → strategies
      if (result.ranking_results && result.ranking_results.length > 0) {
        const mappedStrategies = result.ranking_results.map((r, i) => ({
          name: r.strategy_name || `Strategy ${i + 1}`,
          sharpe: r.backtest?.sharpe_ratio ?? r.sharpe ?? null,
          return_pct: r.backtest?.return_pct ?? r.return_pct ?? null,
          drawdown_pct: r.backtest?.max_drawdown_pct ?? r.drawdown_pct ?? null,
          composite_score: r.composite_score ?? null,
          robustness: r.robustness ?? null,
          rank: r.rank ?? i + 1,
          genome_type: r.genome_type ?? null,
        }));
        setStrategies(mappedStrategies);
      }

      setLastRunSymbol(form.symbol);
      setShowForm(false);
      setActiveTab('overview');
    } catch (err) {
      setError(err.message || 'Research pipeline failed');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Derived stats ──
  const pnl = portfolioValue != null && initialCapital != null
    ? portfolioValue - initialCapital : null;
  const pnlPct = pnl != null && initialCapital > 0
    ? (pnl / initialCapital) * 100 : null;
  const isPositive = pnl == null || pnl >= 0;

  const fmtCurrency = (v) => v == null ? '--'
    : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);
  const fmtPct = (v) => v == null ? '--' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
  const fmtTime = (d) => d.toUTCString().replace(' GMT', ' UTC');

  // ── Styles ──
  const S = {
    root: {
      display: 'flex', flexDirection: 'column',
      height: '100vh', width: '100vw',
      background: 'var(--bg-primary)',
      fontFamily: 'var(--font-mono)',
      overflow: 'hidden',
    },
    // Top header bar
    header: {
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: 'var(--bg-header)',
      borderBottom: '2px solid var(--accent-orange)',
      padding: '0 16px',
      height: 'var(--header-height)',
      flexShrink: 0,
      gap: '24px',
    },
    headerLeft: { display: 'flex', alignItems: 'center', gap: '16px' },
    logo: {
      fontSize: '14px', fontWeight: '600',
      color: 'var(--accent-orange)',
      letterSpacing: '0.08em',
      display: 'flex', alignItems: 'center', gap: '8px',
    },
    logoSep: { color: 'var(--border-bright)', fontSize: '16px' },
    symbolBadge: {
      background: 'var(--bg-selected)',
      border: '1px solid var(--border-orange)',
      color: 'var(--accent-orange)',
      padding: '2px 10px',
      fontSize: '13px', fontWeight: '600',
      letterSpacing: '0.1em',
    },
    headerCenter: {
      display: 'flex', alignItems: 'center', gap: '24px',
      flex: 1, justifyContent: 'center',
    },
    kpiMini: { textAlign: 'center' },
    kpiMiniLabel: { fontSize: '9px', color: 'var(--text-label)', letterSpacing: '0.1em', display: 'block' },
    kpiMiniValue: { fontSize: '14px', fontWeight: '600', letterSpacing: '-0.01em' },
    headerRight: { display: 'flex', alignItems: 'center', gap: '12px' },
    liveIndicator: { display: 'flex', alignItems: 'center', gap: '6px' },
    liveDot: (live) => ({
      width: '7px', height: '7px', borderRadius: '50%',
      background: live ? 'var(--accent-green)' : 'var(--accent-red)',
      animation: live ? 'blink 1.5s ease-in-out infinite' : 'none',
    }),
    liveText: (live) => ({
      fontSize: '10px', fontWeight: '600', letterSpacing: '0.1em',
      color: live ? 'var(--accent-green)' : 'var(--accent-red)',
    }),
    clock: { fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.04em' },
    // Tab bar
    tabBar: {
      display: 'flex', alignItems: 'center',
      background: 'var(--bg-header)',
      borderBottom: '1px solid var(--border-color)',
      height: 'var(--tab-height)',
      flexShrink: 0,
    },
    // Content area
    content: { flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0 },
    // Error banner
    errorBanner: {
      background: 'rgba(255, 77, 79, 0.08)',
      borderBottom: '1px solid var(--accent-red)',
      color: 'var(--accent-red)',
      padding: '5px 16px',
      fontSize: '11px',
      letterSpacing: '0.04em',
      flexShrink: 0,
    },
    // Status bar
    statusBar: {
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: 'var(--bg-header)',
      borderTop: '1px solid var(--border-color)',
      padding: '0 16px',
      height: 'var(--statusbar-height)',
      flexShrink: 0,
      fontSize: '10px', color: 'var(--text-muted)',
      letterSpacing: '0.04em',
    },
  };

  // ── Form overlay ──
  const renderForm = () => (
    <div style={{
      position: 'absolute', inset: 0,
      background: 'rgba(10, 14, 23, 0.92)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 200,
      backdropFilter: 'blur(2px)',
    }}>
      <div style={{
        background: 'var(--bg-panel)',
        border: '1px solid var(--border-orange)',
        width: '420px',
        animation: 'slide-in 0.2s ease',
      }}>
        {/* Form header */}
        <div style={{
          background: 'var(--bg-header)',
          borderBottom: '2px solid var(--accent-orange)',
          padding: '10px 16px',
          display: 'flex', alignItems: 'center', gap: '8px',
        }}>
          <span style={{ color: 'var(--accent-orange)', fontSize: '12px', fontWeight: '600', letterSpacing: '0.1em' }}>
            ◈ RESEARCH PARAMETERS
          </span>
        </div>

        <form onSubmit={handleRunResearch} style={{ padding: '20px 16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {[
            { label: 'SYMBOL', name: 'symbol', type: 'text', placeholder: 'e.g. SPY, AAPL' },
            { label: 'START DATE', name: 'start_date', type: 'date' },
            { label: 'END DATE', name: 'end_date', type: 'date' },
            { label: 'INITIAL CAPITAL (USD)', name: 'initial_capital', type: 'number' },
          ].map(({ label, name, type, placeholder }) => (
            <div key={name} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '9px', color: 'var(--text-label)', letterSpacing: '0.12em' }}>{label}</label>
              <input
                type={type}
                name={name}
                value={form[name]}
                onChange={handleFormChange}
                placeholder={placeholder}
                required
                style={{
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-primary)',
                  padding: '7px 10px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  outline: 'none',
                  width: '100%',
                  transition: 'border-color 0.15s',
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--accent-orange)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
              />
            </div>
          ))}

          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '6px',
              background: isLoading ? 'var(--bg-primary)' : 'var(--accent-orange)',
              color: isLoading ? 'var(--text-muted)' : '#000',
              border: `1px solid ${isLoading ? 'var(--border-color)' : 'var(--accent-orange)'}`,
              padding: '9px 0',
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              fontWeight: '600',
              letterSpacing: '0.12em',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              transition: 'all 0.15s',
            }}
          >
            {isLoading ? (
              <><div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }} /> RUNNING PIPELINE...</>
            ) : '▶ RUN RESEARCH'}
          </button>

          {!showForm && (
            <button
              type="button"
              onClick={() => setShowForm(false)}
              style={{
                background: 'transparent',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-color)',
                padding: '6px 0',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                cursor: 'pointer',
                letterSpacing: '0.08em',
              }}
            >
              CANCEL
            </button>
          )}
        </form>
      </div>
    </div>
  );

  // ── Loading overlay ──
  const renderLoading = () => (
    <div style={{
      position: 'absolute', inset: 0,
      background: 'rgba(10, 14, 23, 0.88)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 300, flexDirection: 'column', gap: '16px',
    }}>
      <div className="spinner" style={{ width: '32px', height: '32px', borderWidth: '3px' }} />
      <div style={{ color: 'var(--accent-orange)', fontSize: '13px', letterSpacing: '0.15em', fontWeight: '600' }}>
        RUNNING RESEARCH PIPELINE
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
        Evolving strategies · Backtesting · Computing analytics
      </div>
    </div>
  );

  // ── Tab content ──
  const renderOverview = () => (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: '1fr 1fr',
      gap: '4px', padding: '4px',
      flex: 1, overflow: 'hidden', minHeight: 0,
    }}>
      {/* Equity Curve */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />EQUITY CURVE</div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <EquityChart data={equityData} initialCapital={initialCapital} />
        </div>
      </div>

      {/* Metrics KPI */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />PERFORMANCE METRICS</div>
        <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <MetricsPanel metrics={metrics} />
        </div>
      </div>

      {/* Drawdown */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />DRAWDOWN ANALYSIS</div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <DrawdownChart data={equityData} />
        </div>
      </div>

      {/* Strategy Rankings */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />STRATEGY RANKINGS</div>
        <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <StrategyTable strategies={strategies} />
        </div>
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: '1fr 1fr',
      gap: '4px', padding: '4px',
      flex: 1, overflow: 'hidden', minHeight: 0,
    }}>
      {/* Equity Curve full */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden', gridColumn: '1 / -1' }}>
        <div className="panel-header"><span className="panel-title-dot" />EQUITY CURVE — FULL HISTORY</div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <EquityChart data={equityData} initialCapital={initialCapital} showVolume />
        </div>
      </div>

      {/* Rolling Sharpe */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />ROLLING SHARPE (20-PERIOD)</div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <RollingMetricsChart data={rollingData} metric="sharpe" color="var(--accent-orange)" />
        </div>
      </div>

      {/* Rolling Vol */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />ROLLING VOLATILITY (20-PERIOD)</div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <RollingMetricsChart data={rollingData} metric="vol" color="var(--accent-purple)" />
        </div>
      </div>
    </div>
  );

  const renderStrategies = () => (
    <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: '4px', minHeight: 0 }}>
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />STRATEGY RANKING ENGINE — FULL RESULTS</div>
        <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <StrategyTable strategies={strategies} expanded />
        </div>
      </div>
    </div>
  );

  const renderRisk = () => (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gridTemplateRows: '1fr 1fr',
      gap: '4px', padding: '4px',
      flex: 1, overflow: 'hidden', minHeight: 0,
    }}>
      {/* Drawdown full */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden', gridColumn: '1 / -1' }}>
        <div className="panel-header"><span className="panel-title-dot" />DRAWDOWN CURVE</div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <DrawdownChart data={equityData} />
        </div>
      </div>

      {/* Risk metrics */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />RISK METRICS</div>
        <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <MetricsPanel metrics={metrics} mode="risk" />
        </div>
      </div>

      {/* VaR */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-header"><span className="panel-title-dot" />VALUE AT RISK</div>
        <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <MetricsPanel metrics={metrics} mode="var" />
        </div>
      </div>
    </div>
  );

  const tabContent = {
    overview:   renderOverview,
    analytics:  renderAnalytics,
    strategies: renderStrategies,
    risk:       renderRisk,
  };

  return (
    <div style={{ ...S.root, position: 'relative' }}>
      {/* ── TOP HEADER ── */}
      <div style={S.header}>
        {/* Left */}
        <div style={S.headerLeft}>
          <div style={S.logo}>
            <span style={{ color: 'var(--accent-orange)', fontSize: '18px' }}>◈</span>
            <span>BQUANT</span>
            <span style={S.logoSep}>|</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '11px', fontWeight: '400' }}>ALGO TERMINAL</span>
          </div>
          {lastRunSymbol && (
            <div style={S.symbolBadge}>{lastRunSymbol}</div>
          )}
        </div>

        {/* Center KPIs */}
        <div style={S.headerCenter}>
          <div style={S.kpiMini}>
            <span style={S.kpiMiniLabel}>PORTFOLIO VALUE</span>
            <span style={{ ...S.kpiMiniValue, color: 'var(--text-primary)' }}>{fmtCurrency(portfolioValue)}</span>
          </div>
          <div style={{ width: '1px', height: '24px', background: 'var(--border-color)' }} />
          <div style={S.kpiMini}>
            <span style={S.kpiMiniLabel}>P&amp;L</span>
            <span style={{ ...S.kpiMiniValue, color: isPositive ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {fmtCurrency(pnl)}
            </span>
          </div>
          <div style={{ width: '1px', height: '24px', background: 'var(--border-color)' }} />
          <div style={S.kpiMini}>
            <span style={S.kpiMiniLabel}>RETURN</span>
            <span style={{ ...S.kpiMiniValue, color: isPositive ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {fmtPct(pnlPct)}
            </span>
          </div>
          {metrics.sharpe != null && (
            <>
              <div style={{ width: '1px', height: '24px', background: 'var(--border-color)' }} />
              <div style={S.kpiMini}>
                <span style={S.kpiMiniLabel}>SHARPE</span>
                <span style={{ ...S.kpiMiniValue, color: metrics.sharpe > 1 ? 'var(--accent-green)' : metrics.sharpe > 0 ? 'var(--accent-yellow)' : 'var(--accent-red)' }}>
                  {metrics.sharpe.toFixed(2)}
                </span>
              </div>
            </>
          )}
          {metrics.max_drawdown != null && (
            <>
              <div style={{ width: '1px', height: '24px', background: 'var(--border-color)' }} />
              <div style={S.kpiMini}>
                <span style={S.kpiMiniLabel}>MAX DD</span>
                <span style={{ ...S.kpiMiniValue, color: 'var(--accent-red)' }}>
                  {(metrics.max_drawdown * 100).toFixed(1)}%
                </span>
              </div>
            </>
          )}
        </div>

        {/* Right */}
        <div style={S.headerRight}>
          <div style={S.liveIndicator}>
            <div style={S.liveDot(isLive)} />
            <span style={S.liveText(isLive)}>{isLive ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <div style={{ width: '1px', height: '20px', background: 'var(--border-color)' }} />
          <div style={S.clock}>{fmtTime(currentTime)}</div>
          <div style={{ width: '1px', height: '20px', background: 'var(--border-color)' }} />
          <button
            onClick={() => setShowForm(true)}
            style={{
              background: 'var(--accent-orange)',
              color: '#000',
              border: 'none',
              padding: '5px 12px',
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              fontWeight: '700',
              letterSpacing: '0.1em',
              cursor: 'pointer',
            }}
          >
            ▶ NEW RUN
          </button>
        </div>
      </div>

      {/* ── TAB BAR ── */}
      <div style={S.tabBar}>
        {TABS.map((tab) => (
          <div
            key={tab.id}
            className={`tab-item${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </div>
        ))}
        <div style={{ flex: 1 }} />
        {/* Right side of tab bar */}
        <div style={{ padding: '0 16px', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
          {equityData.length > 0 ? `${equityData.length} DATA POINTS` : 'NO DATA'}
        </div>
      </div>

      {/* ── ERROR BANNER ── */}
      {error && (
        <div style={S.errorBanner}>
          ⚠ {error}
          <button
            onClick={() => setError(null)}
            style={{ marginLeft: '12px', background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer', fontSize: '11px' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* ── MAIN CONTENT ── */}
      <div style={S.content}>
        {equityData.length === 0 && !showForm ? (
          <div style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexDirection: 'column', gap: '16px',
          }}>
            <div style={{ fontSize: '32px', color: 'var(--border-bright)' }}>◈</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', letterSpacing: '0.1em' }}>
              NO DATA — CLICK ▶ NEW RUN TO START
            </div>
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
            {(tabContent[activeTab] || renderOverview)()}
          </div>
        )}
      </div>

      {/* ── STATUS BAR ── */}
      <div style={S.statusBar}>
        <span>BQUANT ALGO TERMINAL v2.0</span>
        <span>
          {strategies.length > 0 ? `${strategies.length} STRATEGIES RANKED` : 'AWAITING PIPELINE'}
          {' · '}
          {metrics.total_return != null
            ? `TOTAL RETURN: ${(metrics.total_return * 100).toFixed(2)}%`
            : 'RUN RESEARCH TO POPULATE'}
        </span>
        <span>WS: {isLive ? 'CONNECTED' : 'DISCONNECTED'}</span>
      </div>

      {/* ── OVERLAYS ── */}
      {isLoading && renderLoading()}
      {showForm && !isLoading && renderForm()}
    </div>
  );
}

export default App;
