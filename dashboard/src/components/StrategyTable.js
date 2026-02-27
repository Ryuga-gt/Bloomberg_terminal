import React from 'react';

/**
 * Strategy ranking table.
 *
 * Props:
 *   strategies: array of ranking result objects
 *   bestGenome: genome dict of the best evolved strategy
 */
const StrategyTable = ({ strategies = [], bestGenome = null }) => {
  return (
    <div className="bg-gray-950 border border-green-900 rounded p-4 mb-4">
      <h3 className="text-green-400 text-sm font-bold mb-3 uppercase tracking-wider">
        Strategy Rankings
      </h3>

      {/* Best Genome */}
      {bestGenome && (
        <div className="mb-3 p-2 bg-gray-900 border border-yellow-700 rounded text-xs">
          <span className="text-yellow-500 font-bold">BEST EVOLVED: </span>
          <span className="text-green-300">
            {bestGenome.type?.toUpperCase()}
            {bestGenome.short && ` (${bestGenome.short}/${bestGenome.long})`}
            {bestGenome.period && ` (RSI ${bestGenome.period})`}
            {bestGenome.window && ` (W${bestGenome.window})`}
          </span>
        </div>
      )}

      {strategies.length === 0 ? (
        <p className="text-gray-600 text-xs">No strategies ranked yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-green-900">
                <th className="text-left text-gray-500 py-1 pr-2">#</th>
                <th className="text-left text-gray-500 py-1 pr-2">Strategy</th>
                <th className="text-right text-gray-500 py-1 pr-2">Score</th>
                <th className="text-right text-gray-500 py-1 pr-2">Sharpe</th>
                <th className="text-right text-gray-500 py-1">MDD</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((s, i) => {
                const score = s.composite_score ?? 0;
                const sharpe = s.backtest?.sharpe_ratio ?? 0;
                const mdd = s.backtest?.max_drawdown_pct ?? 0;
                return (
                  <tr key={i} className="border-b border-gray-900 hover:bg-gray-900">
                    <td className="py-1 pr-2 text-yellow-500 font-bold">{s.rank ?? i + 1}</td>
                    <td className="py-1 pr-2 text-green-300 truncate max-w-24">{s.strategy_name}</td>
                    <td className={`py-1 pr-2 text-right font-mono ${score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {score.toFixed(3)}
                    </td>
                    <td className={`py-1 pr-2 text-right font-mono ${sharpe >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {sharpe.toFixed(3)}
                    </td>
                    <td className={`py-1 text-right font-mono ${mdd <= 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {(mdd * 100).toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default StrategyTable;
