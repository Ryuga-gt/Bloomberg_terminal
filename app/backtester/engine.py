import math


class Backtester:
    def __init__(self, initial_cash: float) -> None:
        self.initial_cash = initial_cash

    def run(self, candles: list[dict], mode: str = "buy_and_hold",
            transaction_cost_pct: float = 0.0, slippage_pct: float = 0.0) -> dict:
        if len(candles) < 2:
            raise ValueError("buy_and_hold requires at least 2 candles")
        buy_price = candles[0]["close"] * (1 + slippage_pct / 100)
        sell_price = candles[-1]["close"] * (1 - slippage_pct / 100)
        cash_after_entry_cost = self.initial_cash * (1 - transaction_cost_pct / 100)
        shares = cash_after_entry_cost / buy_price
        equity_curve = [shares * c["close"] for c in candles]
        gross_exit = shares * sell_price
        final_equity = gross_exit * (1 - transaction_cost_pct / 100)
        return_pct = (final_equity - self.initial_cash) / self.initial_cash * 100
        peak = equity_curve[0]
        max_drawdown_pct = 0.0
        for v in equity_curve:
            if v > peak:
                peak = v
            dd = (v - peak) / peak * 100
            if dd < max_drawdown_pct:
                max_drawdown_pct = dd
        returns_series = [0.0] + [
            (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            for i in range(1, len(equity_curve))
        ]
        n = len(returns_series)
        mean_return = sum(returns_series) / n
        if n < 2:
            volatility_pct = 0.0
        else:
            variance = sum((x - mean_return) ** 2 for x in returns_series) / (n - 1)
            volatility_pct = math.sqrt(variance) * 100
        std_dev = volatility_pct / 100
        sharpe_ratio = mean_return / std_dev if std_dev != 0.0 else 0.0
        return {"final_equity": final_equity, "return_pct": return_pct, "equity_curve": equity_curve, "max_drawdown_pct": max_drawdown_pct, "returns_series": returns_series, "volatility_pct": volatility_pct, "sharpe_ratio": sharpe_ratio}
