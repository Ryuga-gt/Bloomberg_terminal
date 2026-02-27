"""
api.main
========

FastAPI application for the Bloomberg Terminal backend.

Endpoints
---------
GET  /health                — Health check
POST /research              — Run full research pipeline
GET  /portfolio/summary     — Last lifecycle result summary
GET  /portfolio/analytics   — Full analytics report
WS   /stream/equity         — WebSocket equity curve stream

Run with:
    uvicorn api.main:app --reload --port 8000
"""

import asyncio
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    HealthResponse,
    ResearchRequest,
    ResearchResponse,
    PortfolioSummaryResponse,
    PortfolioAnalyticsResponse,
)
from api.websocket_manager import WebSocketManager
from data.yahoo_provider import YahooProvider
from data.cache import JSONFileCache
from pipeline.research_pipeline import run_full_pipeline

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bloomberg Terminal API",
    description="Institutional trading research and portfolio analytics backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory state (no external DB)
# ---------------------------------------------------------------------------

_last_pipeline_result: Optional[dict] = None
_ws_manager = WebSocketManager()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Run the full automated research pipeline for a given symbol and date range.

    Returns analytics summary, best strategy genome, and equity curve.
    """
    global _last_pipeline_result

    cache = JSONFileCache(cache_dir=".market_cache")
    provider = YahooProvider(cache=cache)

    try:
        result = run_full_pipeline(
            symbol=request.symbol,
            start=request.start,
            end=request.end,
            provider=provider,
            initial_capital=request.initial_capital,
            population_size=request.population_size,
            generations=request.generations,
            rebalance_interval=request.rebalance_interval,
            allocator_mode=request.allocator_mode,
            seed=request.seed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    _last_pipeline_result = result

    equity_curve = result.get("portfolio_result", {}).get("equity_curve", [])

    # Broadcast equity curve update to WebSocket subscribers
    if equity_curve:
        asyncio.create_task(
            _ws_manager.broadcast({
                "type":        "equity_update",
                "symbol":      request.symbol,
                "equity":      equity_curve[-1],
                "equity_curve": equity_curve[-50:],  # last 50 points
            })
        )

    return ResearchResponse(
        symbol=result["symbol"],
        candle_count=result["candle_count"],
        best_genome=result.get("best_genome"),
        best_fitness=result.get("best_fitness"),
        ranking_results=result.get("ranking_results", []),
        equity_curve=equity_curve,
        analytics=result.get("analytics_report"),
        error=result.get("error"),
    )


@app.get("/portfolio/summary", response_model=PortfolioSummaryResponse)
async def portfolio_summary():
    """Return a summary of the last lifecycle manager result."""
    if _last_pipeline_result is None:
        raise HTTPException(
            status_code=404,
            detail="No pipeline result available. Run POST /research first."
        )
    pr = _last_pipeline_result.get("portfolio_result", {})
    return PortfolioSummaryResponse(
        final_portfolio_equity=pr.get("final_portfolio_equity", 0.0),
        rebalance_steps=pr.get("rebalance_steps", []),
        disabled_strategies=pr.get("disabled_strategies", []),
        equity_curve_length=len(pr.get("equity_curve", [])),
    )


@app.get("/portfolio/analytics", response_model=PortfolioAnalyticsResponse)
async def portfolio_analytics():
    """Return the full analytics report from the last pipeline run."""
    if _last_pipeline_result is None:
        raise HTTPException(
            status_code=404,
            detail="No pipeline result available. Run POST /research first."
        )
    analytics = _last_pipeline_result.get("analytics_report", {})
    # Remove non-serialisable rolling lists for this endpoint
    safe_analytics = {
        k: v for k, v in analytics.items()
        if not isinstance(v, list)
    }
    return PortfolioAnalyticsResponse(analytics=safe_analytics)


@app.websocket("/stream/equity")
async def stream_equity(websocket: WebSocket):
    """
    WebSocket endpoint that streams equity curve updates.

    Clients receive JSON messages of the form:
        {"type": "equity_update", "equity": float, "equity_curve": list}
    """
    await _ws_manager.connect(websocket)
    try:
        # Send a welcome message
        await _ws_manager.send_personal(websocket, {
            "type":    "connected",
            "message": "Equity stream connected",
            "clients": _ws_manager.connection_count,
        })

        # Keep connection alive; updates are pushed via broadcast()
        while True:
            # Receive any client messages (ping/pong or commands)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=30.0
                )
            except asyncio.TimeoutError:
                # Send heartbeat
                await _ws_manager.send_personal(websocket, {"type": "heartbeat"})
    except WebSocketDisconnect:
        _ws_manager.disconnect(websocket)
