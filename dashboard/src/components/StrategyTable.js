import React, { useState, useMemo } from 'react';

const COLS = [
  { key: 'rank',            label: '#',       align: 'center', width: '36px' },
  { key: 'name',            label: 'STRATEGY', align: 'left',   width: 'auto' },
  { key: 'composite_score', label: 'SCORE',   align: 'right',  width: '80px' },
  { key: 'sharpe',          label: 'SHARPE',  align: 'right',  width: '70px' },
  { key: 'return_pct',      label: 'RETURN',  align: 'right',  width: '70px' },
  { key: 'drawdown_pct',    label: 'MAX DD',  align: 'right',  width: '70px' },
  { key: 'robustness',      label: 'ROBUST',  align: 'right',  width: '70px' },
];

const COLS_EXPANDED = [
  ...COLS,
  { key: 'score_bar', label: 'SCORE BAR', align: 'left', width: '120px' },
];

const fmtNum = (v, d = 2) => v == null ? '--' : Number(v).toFixed(d);
const fmtPct = (v) => v == null ? '--' : `${Number(v) >= 0 ? '+' : ''}${Number(v).toFixed(1)}%`;

const scoreColor = (v) => {
  if (v == null) return 'var(--text-muted)';
  if (v > 1)   return 'var(--accent-green)';
  if (v > 0)   return 'var(--accent-yellow)';
  return 'var(--accent-red)';
};

const sharpeColor = (v) => {
  if (v == null) return 'var(--text-muted)';
  if (v > 1.5) return 'var(--accent-green)';
  if (v > 0.5) return 'var(--accent-yellow)';
  if (v > 0)   return 'var(--text-secondary)';
  return 'var(--accent-red)';
};

const returnColor = (v) => {
  if (v == null) return 'var(--text-muted)';
  return Number(v) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
};

const ScoreBar = ({ value, max }) => {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  const color = scoreColor(value);
  return (
    <div className="score-bar-container">
      <div className="score-bar-track" style={{ flex: 1 }}>
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span style={{ fontSize: '10px', color, minWidth: '32px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
        {fmtNum(value)}
      </span>
    </div>
  );
};

const StrategyTable = ({ strategies, expanded }) => {
  const [sortKey, setSortKey]   = useState('rank');
  const [sortDir, setSortDir]   = useState('asc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'rank' ? 'asc' : 'desc');
    }
  };

  const sorted = useMemo(() => {
    if (!strategies || strategies.length === 0) return [];
    return [...strategies].sort((a, b) => {
      const av = a[sortKey] ?? (sortKey === 'rank' ? 999 : -Infinity);
      const bv = b[sortKey] ?? (sortKey === 'rank' ? 999 : -Infinity);
      const cmp = typeof av === 'string' ? av.localeCompare(bv) : av - bv;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [strategies, sortKey, sortDir]);

  const maxScore = useMemo(() =>
    Math.max(0.001, ...sorted.map((s) => Math.abs(s.composite_score ?? 0))),
    [sorted]
  );

  const cols = expanded ? COLS_EXPANDED : COLS;

  if (!strategies || strategies.length === 0) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100%', flexDirection: 'column', gap: '8px',
      }}>
        <div style={{ fontSize: '20px', color: 'var(--border-bright)' }}>◆</div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
          NO DATA — RUN RESEARCH PIPELINE
        </div>
      </div>
    );
  }

  return (
    <table className="data-table" style={{ width: '100%' }}>
      <thead>
        <tr>
          {cols.map((col) => (
            <th
              key={col.key}
              style={{ textAlign: col.align, width: col.width, cursor: 'pointer' }}
              onClick={() => col.key !== 'score_bar' && handleSort(col.key)}
            >
              {col.label}
              {sortKey === col.key && (
                <span style={{ marginLeft: '4px', color: 'var(--accent-orange)' }}>
                  {sortDir === 'asc' ? '▲' : '▼'}
                </span>
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map((row, idx) => {
          const isTop = idx === 0;
          return (
            <tr key={idx} style={{ background: isTop ? 'rgba(255, 140, 0, 0.04)' : 'transparent' }}>
              {/* Rank */}
              <td style={{ textAlign: 'center', color: isTop ? 'var(--accent-orange)' : 'var(--text-muted)', fontWeight: isTop ? '700' : '400' }}>
                {isTop ? '★' : row.rank ?? idx + 1}
              </td>

              {/* Name */}
              <td style={{
                color: isTop ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: isTop ? '600' : '400',
                maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis',
              }}>
                {row.name || `Strategy ${idx + 1}`}
              </td>

              {/* Score */}
              <td style={{ textAlign: 'right', color: scoreColor(row.composite_score), fontWeight: '600' }}>
                {fmtNum(row.composite_score)}
              </td>

              {/* Sharpe */}
              <td style={{ textAlign: 'right', color: sharpeColor(row.sharpe) }}>
                {fmtNum(row.sharpe)}
              </td>

              {/* Return */}
              <td style={{ textAlign: 'right', color: returnColor(row.return_pct) }}>
                {fmtPct(row.return_pct)}
              </td>

              {/* Max DD */}
              <td style={{ textAlign: 'right', color: 'var(--accent-red)' }}>
                {row.drawdown_pct != null ? `${Number(row.drawdown_pct).toFixed(1)}%` : '--'}
              </td>

              {/* Robustness */}
              <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                {fmtNum(row.robustness)}
              </td>

              {/* Score bar (expanded only) */}
              {expanded && (
                <td style={{ paddingRight: '12px' }}>
                  <ScoreBar value={row.composite_score} max={maxScore} />
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default StrategyTable;
