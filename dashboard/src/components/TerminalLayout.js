/**
 * TerminalLayout — legacy wrapper (no longer used as primary layout).
 * App.js now handles the full BQuant-style layout directly.
 * Kept for backward compatibility.
 */
import React from 'react';

const TerminalLayout = ({ children }) => (
  <div style={{ width: '100%', height: '100%' }}>{children}</div>
);

export default TerminalLayout;
