# Plan: Build "Strategy Lab" (use obra/superpowers)
- Goal: produce a web UI + API that displays market data, runs backtests, and accepts strategy JSON (strict schema). No live trading.
- Prep: clone https://github.com/obra/superpowers and verify install per .codex/.opencode docs. Use the repo as the agent orchestration layer (skills: writing-plans, using-git-worktrees, test-driven-development, executing-plans).
- Repo: create branch feat/strategy-lab
- Deliverables:
  1. server/ (FastAPI) with endpoints: /api/market, /api/backtest, /api/strategy/validate
  2. web/ (React) minimal UI: symbol search, chart, backtest form, results (equity curve + metrics)
  3. docs/README, Dockerfile, CI (GitHub Actions) tests for endpoints
  4. sample_data/ OHLC CSV for at least 2 tickers
  5. schema/strategy_schema.json (strict)
- Workflow constraints:
  - Use Superpowers `writing-plans` to break work into 2–5 minute tasks.
  - Enforce TDD: every production code change must be accompanied by a failing unit test first.
  - Use `using-git-worktrees` skill: each feature/task in an isolated worktree branch.
  - For executing tasks, use subagent-driven-development with two-stage review. Human approval required before any code that could touch external systems is merged.
- Testing: produce unit tests and an example end-to-end run in CI.
- Commit frequently; create incremental PRs with worklog. Keep tasks < 700s per step to fit Kilo invocation limits.