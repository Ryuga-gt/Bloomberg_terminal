class Backtester:
    def __init__(self, initial_cash: float) -> None:
        self.initial_cash = initial_cash

    def run(self, candles: list[dict], mode: str = "buy_and_hold") -> dict:
        if len(candles) < 2:
            raise ValueError("buy_and_hold requires at least 2 candles")
        buy_price = candles[0]["close"]
        sell_price = candles[-1]["close"]
        shares = self.initial_cash / buy_price
        final_equity = shares * sell_price
        return_pct = (final_equity - self.initial_cash) / self.initial_cash * 100
        return {"final_equity": final_equity, "return_pct": return_pct}
