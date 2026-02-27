import React from 'react';

const StrategyTable = ({ strategies }) => {
  const data = strategies || [];

  const headerStyle = {
    padding: '6px 8px',
    fontSize: '9px',
    color: '#6b7280',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    borderBottom: '1px solid #1f2937',
    background: '#0d1117',
    position: 'sticky',
    top: 0,
    zIndex: 1,
    fontFamily: 'Courier New, monospace',
    whiteSpace: 'nowrap',
  };

  const cellStyle = {
    padding: '5px 8px',
    fontSize: '11px',
    fontFamily: 'Courier New, monospace',
    borderBottom: '1px solid rgba(31, 41, 55, 0.3)',
    whiteSpace: 'nowrap',
  };

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        tableLayout: 'fixed',
      }}>
        <thead>
          <tr>
            <th style={{ ...headerStyle, width: '30px' }}>#</th>
            <th style={{ ...headerStyle, width: 'auto', textAlign: 'left' }}>STRATEGY</th>
            <th style={{ ...headerStyle, width: '55px', textAlign: 'right' }}>SHARPE</th>
            <th style={{ ...headerStyle, width: '60px', textAlign: 'right' }}>RETURN</th>
            <th style={{ ...headerStyle, width: '60px', textAlign: 'right' }}>DD%</th>
            <th style={{ ...headerStyle, width: '55px', textAlign: 'right' }}>SCORE</th>
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={6} style={{
                ...cellStyle,
                textAlign: 'center',
                color: '#4b5563',
                padding: '20px',
              }}>
                NO DATA — RUN RESEARCH PIPELINE
              </td>
            </tr>
          ) : (
            data.map((row, idx) => {
              const isTop = idx === 0;
              const rowBg = isTop ? 'rgba(0, 255, 136, 0.05)' : 'transparent';
              const rankColor = isTop ? '#00ff88' : '#9ca3af';

              return (
                <tr key={idx} style={{ background: rowBg }}>
                  <td style={{ ...cellStyle, color: rankColor, fontWeight: isTop ? 'bold' : 'normal', textAlign: 'center' }}>
                    {isTop ? '★' : idx + 1}
                  </td>
                  <td style={{ ...cellStyle, color: isTop ? '#e2e8f0' : '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {row.name || row.strategy_name || `Strategy ${idx + 1}`}
                  </td>
                  <td style={{
                    ...cellStyle,
                    textAlign: 'right',
                    color: (row.sharpe || 0) > 1 ? '#00ff88' : (row.sharpe || 0) > 0 ? '#fbbf24' : '#ff4d4f',
                  }}>
                    {typeof row.sharpe === 'number' ? row.sharpe.toFixed(2) : '--'}
                  </td>
                  <td style={{
                    ...cellStyle,
                    textAlign: 'right',
                    color: (row.return_pct || 0) >= 0 ? '#00ff88' : '#ff4d4f',
                  }}>
                    {typeof row.return_pct === 'number' ? `${row.return_pct.toFixed(1)}%` : '--'}
                  </td>
                  <td style={{
                    ...cellStyle,
                    textAlign: 'right',
                    color: '#ff4d4f',
                  }}>
                    {typeof row.drawdown_pct === 'number' ? `${row.drawdown_pct.toFixed(1)}%` : '--'}
                  </td>
                  <td style={{
                    ...cellStyle,
                    textAlign: 'right',
                    color: isTop ? '#00ff88' : '#9ca3af',
                    fontWeight: isTop ? 'bold' : 'normal',
                  }}>
                    {typeof row.composite_score === 'number' ? row.composite_score.toFixed(2) : '--'}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};

export default StrategyTable;
