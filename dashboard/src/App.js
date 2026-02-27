import React, { useState, useEffect, useRef, useCallback } from 'react';
import './theme.css';
import TerminalLayout from './components/TerminalLayout';

const DEFAULT_FORM = {
  symbol: 'SPY',
  start_date: '2020-01-01',
  end_date: '2024-01-01',
  initial_capital: 100000,
};

function App() {
  const [equityData, setEquityData] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [strategies, setStrategies] = useState([]);
  const [isLive, setIsLive] = useState(false);
  const [portfolioValue, setPortfolioValue] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(true);
  const [form, setForm] = useState(DEFAULT_FORM);

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

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
              const updated = [...prev, { date: data.timestamp, value: data.value }];
              return updated.slice(-500); // Keep last 500 points
            });
            setPortfolioValue(data.value);
          } else if (data.type === 'metrics_update') {
            setMetrics(data.metrics);
          }
        } catch (e) {
          // Ignore parse errors
        }
      };

      ws.onerror = () => {
        setIsLive(false);
      };

      ws.onclose = () => {
        setIsLive(false);
        wsRef.current = null;
        // Auto-reconnect after 5 seconds
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

      if (result.equity_curve) setEquityData(result.equity_curve);
      if (result.metrics) setMetrics(result.metrics);
      if (result.strategies) setStrategies(result.strategies);
      if (result.portfolio_value) setPortfolioValue(result.portfolio_value);

      setShowForm(false);
    } catch (err) {
      setError(err.message || 'Research pipeline failed');
    } finally {
      setIsLoading(false);
    }
  };

  const inputStyle = {
    background: '#0d1117',
    border: '1px solid #1f2937',
    color: '#e2e8f0',
    padding: '4px 8px',
    fontFamily: 'Courier New, monospace',
    fontSize: '12px',
    borderRadius: '2px',
    width: '140px',
  };

  const labelStyle = {
    fontSize: '10px',
    color: '#6b7280',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    marginBottom: '2px',
    display: 'block',
  };

  return (
    <div style={{ height: '100vh', overflow: 'hidden', background: '#0b0f14' }}>
      {/* Collapsible Research Form */}
      <div style={{
        background: '#0d1117',
        borderBottom: '1px solid #1f2937',
        overflow: 'hidden',
        transition: 'max-height 0.3s ease',
        maxHeight: showForm ? '120px' : '32px',
        flexShrink: 0,
      }}>
        {/* Form Toggle Header */}
        <div
          onClick={() => setShowForm(!showForm)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 16px',
            cursor: 'pointer',
            borderBottom: showForm ? '1px solid #1f2937' : 'none',
            height: '32px',
          }}
        >
          <span style={{ fontSize: '10px', color: '#9ca3af', letterSpacing: '0.1em' }}>
            ▸ RESEARCH PARAMETERS
          </span>
          <span style={{ color: '#4b5563', fontSize: '12px' }}>
            {showForm ? '▲' : '▼'}
          </span>
        </div>

        {/* Form Fields */}
        {showForm && (
          <form onSubmit={handleRunResearch} style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '16px',
            padding: '8px 16px',
            flexWrap: 'wrap',
          }}>
            <div>
              <label style={labelStyle}>Symbol</label>
              <input style={inputStyle} name="symbol" value={form.symbol} onChange={handleFormChange} />
            </div>
            <div>
              <label style={labelStyle}>Start Date</label>
              <input style={inputStyle} name="start_date" value={form.start_date} onChange={handleFormChange} />
            </div>
            <div>
              <label style={labelStyle}>End Date</label>
              <input style={inputStyle} name="end_date" value={form.end_date} onChange={handleFormChange} />
            </div>
            <div>
              <label style={labelStyle}>Capital ($)</label>
              <input style={inputStyle} name="initial_capital" value={form.initial_capital} onChange={handleFormChange} type="number" />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                background: isLoading ? '#1f2937' : 'rgba(0, 255, 136, 0.1)',
                border: '1px solid',
                borderColor: isLoading ? '#374151' : '#00ff88',
                color: isLoading ? '#4b5563' : '#00ff88',
                padding: '4px 16px',
                fontFamily: 'Courier New, monospace',
                fontSize: '11px',
                letterSpacing: '0.1em',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                borderRadius: '2px',
                height: '26px',
              }}
            >
              {isLoading ? '◈ RUNNING...' : '▶ RUN RESEARCH'}
            </button>
          </form>
        )}
      </div>

      {/* Terminal Layout */}
      <div style={{ height: showForm ? 'calc(100vh - 120px)' : 'calc(100vh - 32px)', overflow: 'hidden' }}>
        <TerminalLayout
          equityData={equityData}
          metrics={metrics}
          strategies={strategies}
          isLive={isLive}
          portfolioValue={portfolioValue}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
}

export default App;
