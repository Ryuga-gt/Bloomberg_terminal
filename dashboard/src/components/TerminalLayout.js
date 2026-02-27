import React from 'react';

/**
 * Bloomberg-style terminal layout.
 * Dark background, green/red color scheme.
 *
 * Layout:
 *   ┌─────────────────────────────────────────────────────┐
 *   │  TOP BAR: Live indicator | Portfolio value | Status  │
 *   ├──────────┬──────────────────────────┬───────────────┤
 *   │ SIDEBAR  │     MAIN PANEL           │  RIGHT PANEL  │
 *   │ Symbol   │  Equity Chart            │  Metrics      │
 *   │ Research │  Rolling Sharpe          │  VaR          │
 *   │ Strategy │  Drawdown                │  Allocation   │
 *   └──────────┴──────────────────────────┴───────────────┘
 */
const TerminalLayout = ({ sidebar, main, rightPanel, topBar }) => {
  return (
    <div className="min-h-screen bg-black text-green-400 font-mono flex flex-col">
      {/* Top Bar */}
      <div className="bg-gray-900 border-b border-green-800 px-4 py-2 flex items-center justify-between">
        {topBar}
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <div className="w-64 bg-gray-950 border-r border-green-900 flex flex-col overflow-y-auto">
          {sidebar}
        </div>

        {/* Center Panel */}
        <div className="flex-1 overflow-y-auto bg-black p-4">
          {main}
        </div>

        {/* Right Panel */}
        <div className="w-72 bg-gray-950 border-l border-green-900 overflow-y-auto p-4">
          {rightPanel}
        </div>
      </div>
    </div>
  );
};

export default TerminalLayout;
