import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import TerminalLayout from './components/TerminalLayout';
import EquityChart from './components/EquityChart';
import MetricsPanel from './components/MetricsPanel';
import StrategyTable from './components/StrategyTable';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL   = process.env.REACT_APP_WS_URL  || 'ws://localhost:8000/stream/equity';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const formatCurrency = (v) =>
  v != null ? `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—';

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
export default function App() {
  // Form state
  const [symbol, setSymbol]   = useState('AAPL');
  const [start,  setStart]    = useState('2020-01-01');
  const [end,    setEnd]      = useState('2023-01-01');
  const [capital, setCapital] = useState(10000);

  // Result state
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);
  const [result,     setResult]     = useState(null);
  const [liveEquity, setLiveEquity] = useState(null);
  const [wsStatus,   setWsStatus]   = useState('disconnected');

  // WebSocket ref
  const wsRef = useRef(null);

  // Connect WebSocket
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => setWsStatus('connected');
      ws.onclose = () => {
        setWsStatus('disconnected');
        setTimeout(connect, 3000); // auto-reconnect
      };
      ws.onerror = () => setWsStatus('error');
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === 'equity_update') {
            setLiveEquity(msg.equity);
          }
        } catch (_) {}
      };
    };
    connect();
    return () => wsRef.current?.close();
  }, []);

  // Run research
  const handleResearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.post(`${API_BASE}/research`, {
        symbol,
        start,
        end,
        initial_capital: capital,
        population_size: 8,
        generations: 3,
        seed: 42,
      });
      setResult(resp.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [symbol, start, end, capital]);

  // Derived data
  const equityData = (result?.equity_curve || []).map((v, i) => ({ index: i, equity: v }));
  const analytics  = result?.analytics || {};
  const strategies = result?.ranking_results || [];
  const bestGenome = result?.best_genome;
  const portfolioValue = liveEquity ?? (equityData.length > 0 ? equityData[equityData.length - 1]?.equity : null);

  // ---------------------------------------------------------------------------
  // Sub-components
  // ---------------------------------------------------------------------------

  const TopBar = (
    <>
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-green-400 animate-pulse' : 'bg-red-500'}`} />
        <span className="text-green-400 text-xs font-bold uppercase tracking-widest">
          Bloomberg Terminal
        </span>
        <span className="text-gray-600 text-xs">|</span>
        <span className="text-gray-400 text-xs">{symbol}</span>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="text-gray-500 text-xs">Portfolio Value</div>
          <div className="text-green-400 text-sm font-bold font-mono">
            {formatCurrency(portfolioValue)}
          </div>
        </div>
        <div className={`text-xs px-2 py-1 rounded border ${
          wsStatus === 'connected'
            ? 'border-green-700 text-green-400'
            : 'border-red-700 text-red-400'
        }`}>
          {wsStatus.toUpperCase()}
        </div>
      </div>
    </>
  );

  const Sidebar = (
    <div className="p-4 space-y-4">
      <div>
        <h3 className="text-yellow-500 text-xs font-bold uppercase tracking-wider mb-3">Research</h3>
        <div className="space-y-2">
          <div>
            <label className="text-gray-500 text-xs block mb-1">Symbol</label>
            <input
              className="w-full bg-gray-900 border border-green-900 text-green-400 text-xs px-2 py-1 rounded focus:outline-none focus:border-green-500"
              value={symbol}
              onChange={e => setSymbol(e.target.value.toUpperCase())}
            />
          </div>
          <div>
            <label className="text-gray-500 text-xs block mb-1">Start Date</label>
            <input
              type="date"
              className="w-full bg-gray-900 border border-green-900 text-green-400 text-xs px-2 py-1 rounded focus:outline-none focus:border-green-500"
              value={start}
              onChange={e => setStart(e.target.value)}
            />
          </div>
          <div>
            <label className="text-gray-500 text-xs block mb-1">End Date</label>
            <input
              type="date"
              className="w-full bg-gray-900 border border-green-900 text-green-400 text-xs px-2 py-1 rounded focus:outline-none focus:border-green-500"
              value={end}
              onChange={e => setEnd(e.target.value)}
            />
          </div>
          <div>
            <label className="text-gray-500 text-xs block mb-1">Capital ($)</label>
            <input
              type="number"
              className="w-full bg-gray-900 border border-green-900 text-green-400 text-xs px-2 py-1 rounded focus:outline-none focus:border-green-500"
              value={capital}
              onChange={e => setCapital(Number(e.target.value))}
            />
          </div>
          <button
            onClick={handleResearch}
            disabled={loading}
            className={`w-full py-2 text-xs font-bold uppercase tracking-wider rounded border transition-colors ${
              loading
                ? 'border-gray-700 text-gray-600 cursor-not-allowed'
                : 'border-green-600 text-green-400 hover:bg-green-900 cursor-pointer'
            }`}
          >
            {loading ? '⟳ Running...' : '▶ Run Research'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-2 bg-red-950 border border-red-700 rounded text-red-400 text-xs">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-1 text-xs">
          <div className="text-gray-500 uppercase tracking-wider text-xs mb-1">Last Run</div>
          <div className="flex justify-between">
            <span className="text-gray-500">Candles</span>
            <span className="text-green-400">{result.candle_count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Best Fitness</span>
            <span className="text-green-400">{result.best_fitness?.toFixed(4) ?? '—'}</span>
          </div>
        </div>
      )}
    </div>
  );

  const MainPanel = (
    <div>
      <EquityChart
        data={equityData}
        title={`${symbol} Portfolio Equity`}
        initialValue={capital}
      />
      <StrategyTable strategies={strategies} bestGenome={bestGenome} />
    </div>
  );

  const RightPanel = (
    <div>
      <h3 className="text-green-400 text-sm font-bold mb-4 uppercase tracking-wider">Analytics</h3>
      <MetricsPanel analytics={analytics} />
    </div>
  );

  return (
    <TerminalLayout
      topBar={TopBar}
      sidebar={Sidebar}
      main={MainPanel}
      rightPanel={RightPanel}
    />
  );
}
