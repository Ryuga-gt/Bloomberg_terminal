"""
api.schemas
===========

Pydantic request and response models for the FastAPI backend.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    """Request body for POST /research."""
    symbol: str = Field(..., description="Ticker symbol, e.g. 'AAPL'")
    start:  str = Field(..., description="Start date YYYY-MM-DD")
    end:    str = Field(..., description="End date YYYY-MM-DD")
    initial_capital:   float = Field(default=10_000, description="Total capital")
    population_size:   int   = Field(default=10,     description="Evolution population size")
    generations:       int   = Field(default=5,      description="Evolution generations")
    rebalance_interval: int  = Field(default=20,     description="Candles between rebalances")
    allocator_mode:    str   = Field(default="sharpe", description="Capital allocation mode")
    seed:              int   = Field(default=42,     description="Random seed")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str


class CandleSchema(BaseModel):
    timestamp: str
    open:      float
    high:      float
    low:       float
    close:     float
    volume:    float


class GenomeSchema(BaseModel):
    type:  str
    params: Dict[str, Any]


class StrategyResultSchema(BaseModel):
    strategy_name:   str
    composite_score: float
    rank:            int
    backtest:        Dict[str, float]
    robustness:      float


class AnalyticsSchema(BaseModel):
    total_return:          Optional[float]
    cagr:                  Optional[float]
    volatility:            Optional[float]
    sharpe:                Optional[float]
    sortino:               Optional[float]
    max_drawdown:          Optional[float]
    max_drawdown_duration: Optional[int]
    var_95_hist:           Optional[float]
    var_95_param:          Optional[float]


class ResearchResponse(BaseModel):
    symbol:          str
    candle_count:    int
    best_genome:     Optional[Dict[str, Any]]
    best_fitness:    Optional[float]
    ranking_results: List[Dict[str, Any]]
    equity_curve:    List[float]
    analytics:       Optional[Dict[str, Any]]
    error:           Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "candle_count": 756,
                "best_genome": {"type": "moving_average", "short": 5, "long": 20},
                "best_fitness": 0.42,
                "ranking_results": [
                    {
                        "strategy_name": "MA_5_20",
                        "backtest": {
                            "return_pct": 45.2,
                            "sharpe_ratio": 0.85,
                            "calmar_ratio": 2.1,
                            "max_drawdown_pct": -18.5
                        },
                        "composite_score": 1.23,
                        "rank": 1,
                        "robustness": 0.65
                    }
                ],
                "equity_curve": [10000.0, 10150.0, 10320.0, 10280.0],
                "analytics": {
                    "total_return": 0.452,
                    "sharpe": 0.85,
                    "max_drawdown": -0.185,
                    "volatility": 0.22
                },
                "error": None
            }
        }
    }


class PortfolioSummaryResponse(BaseModel):
    final_portfolio_equity: float
    rebalance_steps:        List[int]
    disabled_strategies:    List[str]
    equity_curve_length:    int


class PortfolioAnalyticsResponse(BaseModel):
    analytics: Dict[str, Any]
