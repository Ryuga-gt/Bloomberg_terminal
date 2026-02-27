import React, { useState, useEffect } from 'react';
import '../theme.css';
import EquityChart from './EquityChart';
import MetricsPanel from './MetricsPanel';
import StrategyTable from './StrategyTable';

const TerminalLayout = ({ equityData, metrics, strategies, isLive, portfolioValue, isLoading, error }) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) => {
    return date.toUTCString().replace('GMT', 'UTC');
  };

  const formatCurrency = (value) => {
    if (value === undefined || value === null) return '--';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      width: '100vw',
      background: 'var(--bg-primary)',
      fontFamily: 'var(--font-mono)',
      overflow: 'hidden',
    }}>
      {/* TOP BAR */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#0d1117',
        borderBottom: '1px solid var(--border-color)',
        padding: '6px 16px',
        height: '40px',
        flexShrink: 0,
      }}>
        {/* Left: Symbol + Live indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{
            color: 'var(--accent-green)',
            fontWeight: 'bold',
            fontSize: '14px',
            letterSpacing: '0.05em',
          }}>
            ◈ ALGO-TERMINAL
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isLive ? 'var(--accent-green)' : 'var(--accent-red)',
              animation: isLive ? 'blink-animation 1s step-end infinite' : 'none',
            }} />
            <span style={{
              fontSize: '10px',
              color: isLive ? 'var(--accent-green)' : 'var(--accent-red)',
              letterSpacing: '0.1em',
            }}>
              {isLive ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>

        {/* Center: Portfolio Value */}
        <div style={{ textAlign: 'center' }}>
          <span style={{ fontSize: '10px', color: 'var(--text-secondary)', letterSpacing: '0.1em' }}>
            PORTFOLIO VALUE
          </span>
          <span style={{
            marginLeft: '12px',
            fontSize: '14px',
            fontWeight: 'bold',
            color: 'var(--accent-green)',
          }}>
            {formatCurrency(portfolioValue)}
          </span>
        </div>

        {/* Right: Time */}
        <div style={{
          fontSize: '11px',
          color: 'var(--text-secondary)',
          letterSpacing: '0.05em',
        }}>
          {formatTime(currentTime)}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{
          background: 'rgba(255, 77, 79, 0.1)',
          border: '1px solid var(--accent-red)',
          color: 'var(--accent-red)',
          padding: '6px 16px',
          fontSize: '11px',
          letterSpacing: '0.05em',
          flexShrink: 0,
        }}>
          ⚠ ERROR: {error}
        </div>
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(11, 15, 20, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          flexDirection: 'column',
          gap: '12px',
        }}>
          <div style={{
            color: 'var(--accent-green)',
            fontSize: '14px',
            letterSpacing: '0.2em',
            animation: 'blink-animation 1s step-end infinite',
          }}>
            ◈ RUNNING RESEARCH PIPELINE...
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
            Analyzing strategies. Please wait.
          </div>
        </div>
      )}

      {/* MAIN GRID */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 380px',
        gridTemplateRows: '1fr 200px',
        gap: '4px',
        padding: '4px',
        flex: 1,
        overflow: 'hidden',
        minHeight: 0,
      }}>
        {/* Equity Chart - top left */}
        <div style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-color)',
          borderRadius: '2px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{
            padding: '6px 12px',
            borderBottom: '1px solid var(--border-color)',
            fontSize: '10px',
            color: 'var(--text-secondary)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            flexShrink: 0,
          }}>
            ▸ EQUITY CURVE
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            <EquityChart data={equityData} />
          </div>
        </div>

        {/* Strategy Table - top right */}
        <div style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-color)',
          borderRadius: '2px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{
            padding: '6px 12px',
            borderBottom: '1px solid var(--border-color)',
            fontSize: '10px',
            color: 'var(--text-secondary)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            flexShrink: 0,
          }}>
            ▸ STRATEGY RANKINGS
          </div>
          <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
            <StrategyTable strategies={strategies} />
          </div>
        </div>

        {/* Metrics Panel - bottom left */}
        <div style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-color)',
          borderRadius: '2px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{
            padding: '6px 12px',
            borderBottom: '1px solid var(--border-color)',
            fontSize: '10px',
            color: 'var(--text-secondary)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            flexShrink: 0,
          }}>
            ▸ PERFORMANCE METRICS
          </div>
          <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
            <MetricsPanel metrics={metrics} />
          </div>
        </div>

        {/* Execution Log - bottom right */}
        <div style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-color)',
          borderRadius: '2px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{
            padding: '6px 12px',
            borderBottom: '1px solid var(--border-color)',
            fontSize: '10px',
            color: 'var(--text-secondary)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            flexShrink: 0,
          }}>
            ▸ EXECUTION LOG
          </div>
          <div style={{
            flex: 1,
            overflow: 'auto',
            padding: '8px 12px',
            fontSize: '11px',
            color: 'var(--text-secondary)',
          }}>
            <div style={{ color: 'var(--accent-green)', marginBottom: '4px' }}>
              [SYS] Terminal initialized
            </div>
            <div style={{ marginBottom: '4px' }}>
              [INFO] Awaiting research pipeline...
            </div>
            <div style={{ color: 'var(--text-muted)' }}>
              [INFO] WebSocket: {isLive ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TerminalLayout;
