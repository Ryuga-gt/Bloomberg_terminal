# BQuant Algo Terminal — Symbols & Strategies Reference

> **Comprehensive reference for supported stock symbols, markets, trading strategies, and timeframes.**

---

## Table of Contents

1. [Stock Symbols & Markets](#1-stock-symbols--markets)
   - [1.1 US Equities — Large Cap](#11-us-equities--large-cap)
   - [1.2 US Equities — Technology](#12-us-equities--technology)
   - [1.3 Exchange-Traded Funds (ETFs)](#13-exchange-traded-funds-etfs)
   - [1.4 Market Indices](#14-market-indices)
   - [1.5 Cryptocurrencies](#15-cryptocurrencies)
   - [1.6 Commodities & Futures](#16-commodities--futures)
   - [1.7 Forex Pairs](#17-forex-pairs)
2. [Trading Strategies](#2-trading-strategies)
   - [2.1 Trend Following Strategies](#21-trend-following-strategies)
   - [2.2 Mean Reversion Strategies](#22-mean-reversion-strategies)
   - [2.3 Momentum Strategies](#23-momentum-strategies)
   - [2.4 Volatility Strategies](#24-volatility-strategies)
   - [2.5 Statistical Arbitrage Strategies](#25-statistical-arbitrage-strategies)
   - [2.6 Machine Learning Strategies](#26-machine-learning-strategies)
   - [2.7 Hybrid & Multi-Factor Strategies](#27-hybrid--multi-factor-strategies)
3. [Supported Timeframes & Yahoo Finance Interval Codes](#3-supported-timeframes--yahoo-finance-interval-codes)
4. [Quick Reference Strategy Comparison Table](#4-quick-reference-strategy-comparison-table)

---

## 1. Stock Symbols & Markets

BQuant Algo Terminal supports data retrieval and backtesting across multiple asset classes and global markets via Yahoo Finance and Alpha Vantage data providers.

---

### 1.1 US Equities — Large Cap

| Symbol | Company | Sector |
|--------|---------|--------|
| `AAPL` | Apple Inc. | Technology |
| `MSFT` | Microsoft Corporation | Technology |
| `GOOGL` | Alphabet Inc. (Class A) | Communication Services |
| `GOOG` | Alphabet Inc. (Class C) | Communication Services |
| `AMZN` | Amazon.com Inc. | Consumer Discretionary |
| `NVDA` | NVIDIA Corporation | Technology |
| `META` | Meta Platforms Inc. | Communication Services |
| `TSLA` | Tesla Inc. | Consumer Discretionary |
| `BRK-B` | Berkshire Hathaway Inc. (Class B) | Financials |
| `JPM` | JPMorgan Chase & Co. | Financials |
| `JNJ` | Johnson & Johnson | Healthcare |
| `V` | Visa Inc. | Financials |
| `PG` | Procter & Gamble Co. | Consumer Staples |
| `UNH` | UnitedHealth Group Inc. | Healthcare |
| `HD` | The Home Depot Inc. | Consumer Discretionary |
| `MA` | Mastercard Inc. | Financials |
| `DIS` | The Walt Disney Company | Communication Services |
| `BAC` | Bank of America Corp. | Financials |
| `XOM` | Exxon Mobil Corporation | Energy |
| `CVX` | Chevron Corporation | Energy |
| `KO` | The Coca-Cola Company | Consumer Staples |
| `PEP` | PepsiCo Inc. | Consumer Staples |
| `ABBV` | AbbVie Inc. | Healthcare |
| `MRK` | Merck & Co. Inc. | Healthcare |
| `LLY` | Eli Lilly and Company | Healthcare |
| `TMO` | Thermo Fisher Scientific Inc. | Healthcare |
| `COST` | Costco Wholesale Corporation | Consumer Staples |
| `WMT` | Walmart Inc. | Consumer Staples |
| `MCD` | McDonald's Corporation | Consumer Discretionary |
| `NKE` | Nike Inc. | Consumer Discretionary |

---

### 1.2 US Equities — Technology

| Symbol | Company | Sub-Sector |
|--------|---------|------------|
| `AMD` | Advanced Micro Devices Inc. | Semiconductors |
| `INTC` | Intel Corporation | Semiconductors |
| `QCOM` | Qualcomm Inc. | Semiconductors |
| `AVGO` | Broadcom Inc. | Semiconductors |
| `TXN` | Texas Instruments Inc. | Semiconductors |
| `MU` | Micron Technology Inc. | Semiconductors |
| `AMAT` | Applied Materials Inc. | Semiconductor Equipment |
| `LRCX` | Lam Research Corporation | Semiconductor Equipment |
| `KLAC` | KLA Corporation | Semiconductor Equipment |
| `CRM` | Salesforce Inc. | Software |
| `ORCL` | Oracle Corporation | Software |
| `SAP` | SAP SE | Software |
| `ADBE` | Adobe Inc. | Software |
| `NOW` | ServiceNow Inc. | Software |
| `SNOW` | Snowflake Inc. | Cloud Computing |
| `DDOG` | Datadog Inc. | Cloud Computing |
| `NET` | Cloudflare Inc. | Cloud Computing |
| `ZS` | Zscaler Inc. | Cybersecurity |
| `CRWD` | CrowdStrike Holdings Inc. | Cybersecurity |
| `PANW` | Palo Alto Networks Inc. | Cybersecurity |
| `UBER` | Uber Technologies Inc. | Technology |
| `LYFT` | Lyft Inc. | Technology |
| `ABNB` | Airbnb Inc. | Technology |
| `SHOP` | Shopify Inc. | E-Commerce |
| `SQ` | Block Inc. | Fintech |
| `PYPL` | PayPal Holdings Inc. | Fintech |
| `COIN` | Coinbase Global Inc. | Fintech/Crypto |
| `HOOD` | Robinhood Markets Inc. | Fintech |
| `PLTR` | Palantir Technologies Inc. | Data Analytics |
| `AI` | C3.ai Inc. | Artificial Intelligence |

---

### 1.3 Exchange-Traded Funds (ETFs)

#### Broad Market ETFs

| Symbol | Name | Benchmark |
|--------|------|-----------|
| `SPY` | SPDR S&P 500 ETF Trust | S&P 500 |
| `IVV` | iShares Core S&P 500 ETF | S&P 500 |
| `VOO` | Vanguard S&P 500 ETF | S&P 500 |
| `QQQ` | Invesco QQQ Trust | NASDAQ-100 |
| `QQQM` | Invesco NASDAQ 100 ETF | NASDAQ-100 |
| `DIA` | SPDR Dow Jones Industrial Average ETF | DJIA |
| `IWM` | iShares Russell 2000 ETF | Russell 2000 |
| `VTI` | Vanguard Total Stock Market ETF | Total US Market |
| `ITOT` | iShares Core S&P Total US Stock Market ETF | Total US Market |
| `VT` | Vanguard Total World Stock ETF | Global Market |

#### Sector ETFs

| Symbol | Name | Sector |
|--------|------|--------|
| `XLK` | Technology Select Sector SPDR Fund | Technology |
| `XLF` | Financial Select Sector SPDR Fund | Financials |
| `XLV` | Health Care Select Sector SPDR Fund | Healthcare |
| `XLE` | Energy Select Sector SPDR Fund | Energy |
| `XLI` | Industrial Select Sector SPDR Fund | Industrials |
| `XLY` | Consumer Discretionary Select Sector SPDR Fund | Consumer Discretionary |
| `XLP` | Consumer Staples Select Sector SPDR Fund | Consumer Staples |
| `XLU` | Utilities Select Sector SPDR Fund | Utilities |
| `XLB` | Materials Select Sector SPDR Fund | Materials |
| `XLRE` | Real Estate Select Sector SPDR Fund | Real Estate |
| `XLC` | Communication Services Select Sector SPDR Fund | Communication Services |

#### Bond & Fixed Income ETFs

| Symbol | Name | Duration |
|--------|------|----------|
| `AGG` | iShares Core US Aggregate Bond ETF | Intermediate |
| `BND` | Vanguard Total Bond Market ETF | Intermediate |
| `TLT` | iShares 20+ Year Treasury Bond ETF | Long-Term |
| `IEF` | iShares 7-10 Year Treasury Bond ETF | Intermediate |
| `SHY` | iShares 1-3 Year Treasury Bond ETF | Short-Term |
| `LQD` | iShares iBoxx $ Investment Grade Corporate Bond ETF | Corporate |
| `HYG` | iShares iBoxx $ High Yield Corporate Bond ETF | High Yield |
| `JNK` | SPDR Bloomberg High Yield Bond ETF | High Yield |
| `TIP` | iShares TIPS Bond ETF | Inflation-Protected |
| `BNDX` | Vanguard Total International Bond ETF | International |

#### Volatility & Inverse ETFs

| Symbol | Name | Type |
|--------|------|------|
| `VXX` | iPath Series B S&P 500 VIX Short-Term Futures ETN | Volatility Long |
| `UVXY` | ProShares Ultra VIX Short-Term Futures ETF | Volatility 1.5x |
| `SVXY` | ProShares Short VIX Short-Term Futures ETF | Volatility Short |
| `SH` | ProShares Short S&P 500 | Inverse S&P 500 |
| `PSQ` | ProShares Short QQQ | Inverse NASDAQ-100 |
| `SQQQ` | ProShares UltraPro Short QQQ | 3x Inverse NASDAQ-100 |
| `SPXU` | ProShares UltraPro Short S&P 500 | 3x Inverse S&P 500 |
| `TQQQ` | ProShares UltraPro QQQ | 3x Leveraged NASDAQ-100 |
| `UPRO` | ProShares UltraPro S&P 500 | 3x Leveraged S&P 500 |
| `SSO` | ProShares Ultra S&P 500 | 2x Leveraged S&P 500 |

---

### 1.4 Market Indices

> **Note:** Indices are prefixed with `^` in Yahoo Finance. They are used for benchmarking and cannot be directly traded.

| Symbol | Index Name | Region |
|--------|-----------|--------|
| `^GSPC` | S&P 500 Index | United States |
| `^DJI` | Dow Jones Industrial Average | United States |
| `^IXIC` | NASDAQ Composite Index | United States |
| `^NDX` | NASDAQ-100 Index | United States |
| `^RUT` | Russell 2000 Index | United States |
| `^VIX` | CBOE Volatility Index | United States |
| `^FTSE` | FTSE 100 Index | United Kingdom |
| `^GDAXI` | DAX Performance Index | Germany |
| `^FCHI` | CAC 40 Index | France |
| `^N225` | Nikkei 225 Index | Japan |
| `^HSI` | Hang Seng Index | Hong Kong |
| `^AXJO` | S&P/ASX 200 Index | Australia |
| `^BSESN` | BSE SENSEX Index | India |
| `^NSEI` | NIFTY 50 Index | India |
| `^STOXX50E` | EURO STOXX 50 Index | Europe |
| `^TNX` | CBOE 10-Year Treasury Note Yield | United States |
| `^TYX` | CBOE 30-Year Treasury Bond Yield | United States |
| `^IRX` | CBOE 13-Week Treasury Bill Yield | United States |

---

### 1.5 Cryptocurrencies

> **Note:** Cryptocurrency pairs are suffixed with `-USD` for USD-denominated quotes in Yahoo Finance.

| Symbol | Name | Category |
|--------|------|----------|
| `BTC-USD` | Bitcoin | Layer 1 |
| `ETH-USD` | Ethereum | Layer 1 / Smart Contracts |
| `BNB-USD` | Binance Coin | Exchange Token |
| `SOL-USD` | Solana | Layer 1 |
| `XRP-USD` | XRP (Ripple) | Payments |
| `ADA-USD` | Cardano | Layer 1 |
| `AVAX-USD` | Avalanche | Layer 1 |
| `DOGE-USD` | Dogecoin | Meme Coin |
| `DOT-USD` | Polkadot | Layer 0 |
| `MATIC-USD` | Polygon | Layer 2 |
| `LINK-USD` | Chainlink | Oracle |
| `UNI-USD` | Uniswap | DeFi / DEX |
| `AAVE-USD` | Aave | DeFi / Lending |
| `LTC-USD` | Litecoin | Layer 1 |
| `BCH-USD` | Bitcoin Cash | Layer 1 |
| `ATOM-USD` | Cosmos | Interoperability |
| `NEAR-USD` | NEAR Protocol | Layer 1 |
| `FTM-USD` | Fantom | Layer 1 |
| `ALGO-USD` | Algorand | Layer 1 |
| `XLM-USD` | Stellar | Payments |

---

### 1.6 Commodities & Futures

> **Note:** Commodity ETFs and futures-tracking instruments are used for commodity exposure.

#### Precious Metals

| Symbol | Name | Type |
|--------|------|------|
| `GLD` | SPDR Gold Shares ETF | Gold ETF |
| `IAU` | iShares Gold Trust ETF | Gold ETF |
| `SLV` | iShares Silver Trust ETF | Silver ETF |
| `PPLT` | Aberdeen Standard Physical Platinum Shares ETF | Platinum ETF |
| `PALL` | Aberdeen Standard Physical Palladium Shares ETF | Palladium ETF |
| `GC=F` | Gold Futures (COMEX) | Futures |
| `SI=F` | Silver Futures (COMEX) | Futures |

#### Energy Commodities

| Symbol | Name | Type |
|--------|------|------|
| `USO` | United States Oil Fund ETF | Crude Oil ETF |
| `UNG` | United States Natural Gas Fund ETF | Natural Gas ETF |
| `BNO` | United States Brent Oil Fund ETF | Brent Oil ETF |
| `CL=F` | Crude Oil WTI Futures (NYMEX) | Futures |
| `BZ=F` | Brent Crude Oil Futures (ICE) | Futures |
| `NG=F` | Natural Gas Futures (NYMEX) | Futures |
| `RB=F` | RBOB Gasoline Futures (NYMEX) | Futures |

#### Agricultural Commodities

| Symbol | Name | Type |
|--------|------|------|
| `CORN` | Teucrium Corn Fund ETF | Corn ETF |
| `WEAT` | Teucrium Wheat Fund ETF | Wheat ETF |
| `SOYB` | Teucrium Soybean Fund ETF | Soybean ETF |
| `ZC=F` | Corn Futures (CBOT) | Futures |
| `ZW=F` | Wheat Futures (CBOT) | Futures |
| `ZS=F` | Soybean Futures (CBOT) | Futures |
| `KC=F` | Coffee Futures (ICE) | Futures |
| `CT=F` | Cotton Futures (ICE) | Futures |

---

### 1.7 Forex Pairs

> **Note:** Forex pairs are suffixed with `=X` in Yahoo Finance.

| Symbol | Pair | Description |
|--------|------|-------------|
| `EURUSD=X` | EUR/USD | Euro / US Dollar |
| `GBPUSD=X` | GBP/USD | British Pound / US Dollar |
| `USDJPY=X` | USD/JPY | US Dollar / Japanese Yen |
| `USDCHF=X` | USD/CHF | US Dollar / Swiss Franc |
| `AUDUSD=X` | AUD/USD | Australian Dollar / US Dollar |
| `USDCAD=X` | USD/CAD | US Dollar / Canadian Dollar |
| `NZDUSD=X` | NZD/USD | New Zealand Dollar / US Dollar |
| `EURGBP=X` | EUR/GBP | Euro / British Pound |
| `EURJPY=X` | EUR/JPY | Euro / Japanese Yen |
| `GBPJPY=X` | GBP/JPY | British Pound / Japanese Yen |
| `USDHKD=X` | USD/HKD | US Dollar / Hong Kong Dollar |
| `USDSGD=X` | USD/SGD | US Dollar / Singapore Dollar |
| `USDINR=X` | USD/INR | US Dollar / Indian Rupee |
| `USDCNY=X` | USD/CNY | US Dollar / Chinese Yuan |
| `USDBRL=X` | USD/BRL | US Dollar / Brazilian Real |
| `USDMXN=X` | USD/MXN | US Dollar / Mexican Peso |
| `USDZAR=X` | USD/ZAR | US Dollar / South African Rand |
| `USDTRY=X` | USD/TRY | US Dollar / Turkish Lira |

---

## 2. Trading Strategies

BQuant Algo Terminal supports 29 trading strategies across 7 categories. Each strategy is implemented as a modular component compatible with the backtesting engine and live execution gateway.

---

### 2.1 Trend Following Strategies

Trend following strategies identify and capitalize on sustained directional price movements.

---

#### Strategy 1: Simple Moving Average Crossover (SMA Crossover)

**Category:** Trend Following  
**Complexity:** Beginner  
**Typical Timeframe:** Daily, Weekly

**Description:**  
Generates buy signals when a short-period SMA crosses above a long-period SMA (golden cross), and sell signals when it crosses below (death cross).

**Parameters:**
- `short_window` (int): Short SMA period (default: 20)
- `long_window` (int): Long SMA period (default: 50)

**Signal Logic:**
- **Buy:** `SMA(short) > SMA(long)` (crossover from below)
- **Sell:** `SMA(short) < SMA(long)` (crossover from above)

**Strengths:** Simple, robust, widely tested  
**Weaknesses:** Lagging indicator, whipsaws in sideways markets

---

#### Strategy 2: Exponential Moving Average Crossover (EMA Crossover)

**Category:** Trend Following  
**Complexity:** Beginner  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Similar to SMA Crossover but uses exponential moving averages, which give more weight to recent prices and react faster to price changes.

**Parameters:**
- `short_window` (int): Short EMA period (default: 12)
- `long_window` (int): Long EMA period (default: 26)

**Signal Logic:**
- **Buy:** `EMA(short) > EMA(long)` (crossover from below)
- **Sell:** `EMA(short) < EMA(long)` (crossover from above)

**Strengths:** More responsive than SMA, reduces lag  
**Weaknesses:** More sensitive to noise, higher false signal rate

---

#### Strategy 3: Triple Moving Average System

**Category:** Trend Following  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily

**Description:**  
Uses three moving averages (fast, medium, slow) to confirm trend direction. Requires alignment of all three for signal generation.

**Parameters:**
- `fast_window` (int): Fast MA period (default: 5)
- `medium_window` (int): Medium MA period (default: 20)
- `slow_window` (int): Slow MA period (default: 50)

**Signal Logic:**
- **Buy:** `MA(fast) > MA(medium) > MA(slow)`
- **Sell:** `MA(fast) < MA(medium) < MA(slow)`

**Strengths:** Reduces false signals, stronger trend confirmation  
**Weaknesses:** More lag, misses early trend entries

---

#### Strategy 4: MACD Strategy

**Category:** Trend Following  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Uses the Moving Average Convergence Divergence (MACD) indicator. Generates signals based on MACD line crossing the signal line.

**Parameters:**
- `fast_period` (int): Fast EMA period (default: 12)
- `slow_period` (int): Slow EMA period (default: 26)
- `signal_period` (int): Signal line EMA period (default: 9)

**Signal Logic:**
- **Buy:** MACD line crosses above signal line
- **Sell:** MACD line crosses below signal line

**Strengths:** Captures momentum and trend, widely used  
**Weaknesses:** Lagging, poor in ranging markets

---

#### Strategy 5: Parabolic SAR Trend Strategy

**Category:** Trend Following  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily, 1-Hour

**Description:**  
Uses the Parabolic Stop and Reverse (SAR) indicator to identify trend direction and potential reversal points.

**Parameters:**
- `acceleration` (float): Acceleration factor (default: 0.02)
- `maximum` (float): Maximum acceleration (default: 0.2)

**Signal Logic:**
- **Buy:** Price crosses above Parabolic SAR
- **Sell:** Price crosses below Parabolic SAR

**Strengths:** Built-in trailing stop mechanism  
**Weaknesses:** Generates many signals in sideways markets

---

### 2.2 Mean Reversion Strategies

Mean reversion strategies assume prices will revert to their historical average after deviating significantly.

---

#### Strategy 6: Bollinger Bands Mean Reversion

**Category:** Mean Reversion  
**Complexity:** Beginner  
**Typical Timeframe:** Daily, 1-Hour

**Description:**  
Uses Bollinger Bands to identify overbought and oversold conditions. Buys when price touches the lower band and sells when it touches the upper band.

**Parameters:**
- `window` (int): Moving average period (default: 20)
- `num_std` (float): Number of standard deviations (default: 2.0)

**Signal Logic:**
- **Buy:** Price ≤ Lower Band (mean - 2σ)
- **Sell:** Price ≥ Upper Band (mean + 2σ)

**Strengths:** Intuitive, works well in ranging markets  
**Weaknesses:** Fails in strong trending markets

---

#### Strategy 7: RSI Mean Reversion

**Category:** Mean Reversion  
**Complexity:** Beginner  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Uses the Relative Strength Index (RSI) to identify overbought and oversold conditions.

**Parameters:**
- `rsi_period` (int): RSI calculation period (default: 14)
- `oversold_threshold` (int): Oversold level (default: 30)
- `overbought_threshold` (int): Overbought level (default: 70)

**Signal Logic:**
- **Buy:** RSI < oversold_threshold
- **Sell:** RSI > overbought_threshold

**Strengths:** Simple, effective for range-bound assets  
**Weaknesses:** RSI can remain extreme in trending markets

---

#### Strategy 8: Stochastic Oscillator Strategy

**Category:** Mean Reversion  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Uses the Stochastic Oscillator (%K and %D lines) to identify momentum reversals in overbought/oversold zones.

**Parameters:**
- `k_period` (int): %K period (default: 14)
- `d_period` (int): %D smoothing period (default: 3)
- `oversold` (int): Oversold threshold (default: 20)
- `overbought` (int): Overbought threshold (default: 80)

**Signal Logic:**
- **Buy:** %K crosses above %D in oversold zone
- **Sell:** %K crosses below %D in overbought zone

**Strengths:** Good for short-term reversals  
**Weaknesses:** Generates false signals in trending markets

---

#### Strategy 9: Z-Score Mean Reversion

**Category:** Mean Reversion  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily

**Description:**  
Calculates the Z-score of price relative to its rolling mean and standard deviation. Trades when price deviates significantly from the mean.

**Parameters:**
- `lookback` (int): Rolling window period (default: 20)
- `entry_z` (float): Z-score entry threshold (default: 2.0)
- `exit_z` (float): Z-score exit threshold (default: 0.5)

**Signal Logic:**
- **Buy:** Z-score < -entry_z (price significantly below mean)
- **Sell:** Z-score > entry_z (price significantly above mean)
- **Exit:** |Z-score| < exit_z (price near mean)

**Strengths:** Statistically grounded, adaptable  
**Weaknesses:** Assumes normal distribution of returns

---

#### Strategy 10: Keltner Channel Reversion

**Category:** Mean Reversion  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Uses Keltner Channels (based on ATR) to identify price extremes and potential reversions.

**Parameters:**
- `ema_period` (int): EMA period for channel center (default: 20)
- `atr_period` (int): ATR period (default: 10)
- `multiplier` (float): ATR multiplier for channel width (default: 2.0)

**Signal Logic:**
- **Buy:** Price closes below lower Keltner Channel
- **Sell:** Price closes above upper Keltner Channel

**Strengths:** Volatility-adjusted bands, more adaptive than Bollinger Bands  
**Weaknesses:** Complex parameter tuning required

---

### 2.3 Momentum Strategies

Momentum strategies capitalize on the tendency of assets with recent strong performance to continue outperforming.

---

#### Strategy 11: Price Momentum Strategy

**Category:** Momentum  
**Complexity:** Beginner  
**Typical Timeframe:** Weekly, Monthly

**Description:**  
Ranks assets by their past N-period returns and goes long on top performers, short on bottom performers.

**Parameters:**
- `lookback` (int): Return calculation period in days (default: 252)
- `skip_days` (int): Days to skip before lookback (default: 21)
- `top_n` (int): Number of top assets to hold (default: 5)

**Signal Logic:**
- **Buy:** Asset in top N by past returns
- **Sell:** Asset falls out of top N

**Strengths:** Well-documented anomaly, strong historical performance  
**Weaknesses:** Momentum crashes during market reversals

---

#### Strategy 12: Rate of Change (ROC) Strategy

**Category:** Momentum  
**Complexity:** Beginner  
**Typical Timeframe:** Daily, Weekly

**Description:**  
Uses the Rate of Change indicator to measure the percentage change in price over a specified period.

**Parameters:**
- `roc_period` (int): ROC calculation period (default: 10)
- `signal_threshold` (float): Minimum ROC for signal (default: 0.0)

**Signal Logic:**
- **Buy:** ROC > signal_threshold
- **Sell:** ROC < -signal_threshold

**Strengths:** Simple momentum measure, easy to implement  
**Weaknesses:** Sensitive to period selection

---

#### Strategy 13: Dual Momentum Strategy

**Category:** Momentum  
**Complexity:** Intermediate  
**Typical Timeframe:** Monthly

**Description:**  
Combines absolute momentum (trend filter) with relative momentum (cross-sectional ranking). Popularized by Gary Antonacci.

**Parameters:**
- `lookback` (int): Momentum lookback period in days (default: 252)
- `risk_free_symbol` (str): Risk-free asset symbol (default: 'SHY')

**Signal Logic:**
- **Buy:** Asset has positive absolute momentum AND ranks highest in relative momentum
- **Sell/Cash:** Asset has negative absolute momentum (move to risk-free asset)

**Strengths:** Reduces drawdowns, combines two momentum types  
**Weaknesses:** Monthly rebalancing may miss intra-month moves

---

#### Strategy 14: Williams %R Strategy

**Category:** Momentum  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Uses Williams %R oscillator to identify overbought/oversold conditions with momentum confirmation.

**Parameters:**
- `period` (int): Williams %R period (default: 14)
- `oversold` (int): Oversold threshold (default: -80)
- `overbought` (int): Overbought threshold (default: -20)

**Signal Logic:**
- **Buy:** Williams %R crosses above oversold threshold
- **Sell:** Williams %R crosses below overbought threshold

**Strengths:** Fast-reacting momentum indicator  
**Weaknesses:** Prone to false signals in trending markets

---

### 2.4 Volatility Strategies

Volatility strategies exploit changes in market volatility or use volatility measures to time entries and exits.

---

#### Strategy 15: ATR Breakout Strategy

**Category:** Volatility  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Uses Average True Range (ATR) to define dynamic breakout levels. Enters positions when price breaks out by a multiple of ATR.

**Parameters:**
- `atr_period` (int): ATR calculation period (default: 14)
- `atr_multiplier` (float): Breakout threshold multiplier (default: 2.0)
- `lookback` (int): Breakout reference period (default: 20)

**Signal Logic:**
- **Buy:** Price > High(lookback) + ATR × multiplier
- **Sell:** Price < Low(lookback) - ATR × multiplier

**Strengths:** Adapts to market volatility, good for breakout trading  
**Weaknesses:** Can generate late entries after large moves

---

#### Strategy 16: Volatility Breakout (VIX-Based)

**Category:** Volatility  
**Complexity:** Advanced  
**Typical Timeframe:** Daily

**Description:**  
Uses VIX levels and changes to time equity market entries. Buys equities when VIX spikes (fear peaks) and reduces exposure when VIX is low.

**Parameters:**
- `vix_spike_threshold` (float): VIX spike level for buy signal (default: 30.0)
- `vix_low_threshold` (float): VIX level for reducing exposure (default: 15.0)
- `vix_symbol` (str): VIX symbol (default: '^VIX')

**Signal Logic:**
- **Buy:** VIX > vix_spike_threshold (contrarian entry)
- **Reduce/Sell:** VIX < vix_low_threshold (complacency exit)

**Strengths:** Counter-cyclical, exploits fear-driven selloffs  
**Weaknesses:** Requires VIX data, timing is imprecise

---

#### Strategy 17: Donchian Channel Breakout

**Category:** Volatility / Trend Following  
**Complexity:** Beginner  
**Typical Timeframe:** Daily, Weekly

**Description:**  
Uses Donchian Channels (highest high and lowest low over N periods) to identify breakouts. Classic turtle trading approach.

**Parameters:**
- `entry_period` (int): Entry channel period (default: 20)
- `exit_period` (int): Exit channel period (default: 10)

**Signal Logic:**
- **Buy:** Price breaks above N-period high
- **Sell:** Price breaks below N-period low
- **Exit Long:** Price breaks below exit_period low
- **Exit Short:** Price breaks above exit_period high

**Strengths:** Trend-following classic, simple rules  
**Weaknesses:** Many false breakouts in choppy markets

---

#### Strategy 18: Squeeze Momentum Strategy

**Category:** Volatility  
**Complexity:** Advanced  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Identifies "squeeze" conditions where Bollinger Bands contract inside Keltner Channels, signaling a potential explosive move.

**Parameters:**
- `bb_period` (int): Bollinger Band period (default: 20)
- `bb_std` (float): Bollinger Band standard deviations (default: 2.0)
- `kc_period` (int): Keltner Channel period (default: 20)
- `kc_multiplier` (float): Keltner Channel ATR multiplier (default: 1.5)

**Signal Logic:**
- **Squeeze On:** BB inside KC (low volatility compression)
- **Buy:** Squeeze releases with positive momentum
- **Sell:** Squeeze releases with negative momentum

**Strengths:** Identifies high-probability explosive moves  
**Weaknesses:** Complex setup, requires multiple indicators

---

### 2.5 Statistical Arbitrage Strategies

Statistical arbitrage strategies exploit pricing inefficiencies between related assets using quantitative methods.

---

#### Strategy 19: Pairs Trading (Cointegration)

**Category:** Statistical Arbitrage  
**Complexity:** Advanced  
**Typical Timeframe:** Daily

**Description:**  
Identifies cointegrated asset pairs and trades the spread when it deviates from its historical mean. Classic market-neutral strategy.

**Parameters:**
- `symbol_1` (str): First asset symbol
- `symbol_2` (str): Second asset symbol
- `lookback` (int): Cointegration test window (default: 252)
- `entry_z` (float): Z-score entry threshold (default: 2.0)
- `exit_z` (float): Z-score exit threshold (default: 0.5)

**Signal Logic:**
- **Long Spread:** Z-score < -entry_z (spread below mean)
- **Short Spread:** Z-score > entry_z (spread above mean)
- **Exit:** |Z-score| < exit_z

**Strengths:** Market-neutral, low correlation to market  
**Weaknesses:** Cointegration can break down, requires two positions

---

#### Strategy 20: ETF Arbitrage Strategy

**Category:** Statistical Arbitrage  
**Complexity:** Advanced  
**Typical Timeframe:** Intraday, Daily

**Description:**  
Exploits temporary price discrepancies between an ETF and its underlying basket of securities or a related ETF.

**Parameters:**
- `etf_symbol` (str): Primary ETF symbol
- `benchmark_symbol` (str): Benchmark ETF or index symbol
- `spread_threshold` (float): Minimum spread for entry (default: 0.005)

**Signal Logic:**
- **Buy ETF:** ETF trades at discount to NAV/benchmark
- **Sell ETF:** ETF trades at premium to NAV/benchmark

**Strengths:** Low directional risk, exploits structural inefficiencies  
**Weaknesses:** Requires precise execution, thin margins

---

#### Strategy 21: Index Rebalancing Strategy

**Category:** Statistical Arbitrage  
**Complexity:** Advanced  
**Typical Timeframe:** Daily

**Description:**  
Anticipates and trades around known index rebalancing events (additions/deletions) to capture predictable price movements.

**Parameters:**
- `announcement_days_before` (int): Days before effective date to enter (default: 5)
- `exit_days_after` (int): Days after effective date to exit (default: 2)

**Signal Logic:**
- **Buy:** Anticipated index addition (price pressure expected)
- **Sell:** Anticipated index deletion (price pressure expected)

**Strengths:** Event-driven, predictable catalyst  
**Weaknesses:** Crowded trade, alpha has diminished over time

---

### 2.6 Machine Learning Strategies

Machine learning strategies use algorithmic models to identify patterns and generate trading signals.

---

#### Strategy 22: Random Forest Classifier Strategy

**Category:** Machine Learning  
**Complexity:** Advanced  
**Typical Timeframe:** Daily

**Description:**  
Trains a Random Forest classifier on technical indicators and price features to predict next-day price direction.

**Parameters:**
- `n_estimators` (int): Number of trees (default: 100)
- `max_depth` (int): Maximum tree depth (default: 5)
- `lookback` (int): Training window in days (default: 252)
- `retrain_frequency` (int): Days between retraining (default: 21)
- `features` (list): Feature set (default: ['rsi', 'macd', 'bb_position', 'volume_ratio'])

**Signal Logic:**
- **Buy:** Model predicts positive return with probability > 0.6
- **Sell:** Model predicts negative return with probability > 0.6

**Strengths:** Captures non-linear relationships, handles many features  
**Weaknesses:** Overfitting risk, requires regular retraining

---

#### Strategy 23: LSTM Price Prediction Strategy

**Category:** Machine Learning  
**Complexity:** Expert  
**Typical Timeframe:** Daily, 4-Hour

**Description:**  
Uses Long Short-Term Memory (LSTM) neural networks to predict future price movements based on sequential price and volume data.

**Parameters:**
- `sequence_length` (int): Input sequence length (default: 60)
- `hidden_units` (int): LSTM hidden units (default: 50)
- `epochs` (int): Training epochs (default: 100)
- `prediction_horizon` (int): Days ahead to predict (default: 1)

**Signal Logic:**
- **Buy:** Predicted price > current price × (1 + threshold)
- **Sell:** Predicted price < current price × (1 - threshold)

**Strengths:** Captures temporal dependencies, powerful for sequential data  
**Weaknesses:** Computationally expensive, requires large datasets

---

#### Strategy 24: Gradient Boosting Strategy

**Category:** Machine Learning  
**Complexity:** Advanced  
**Typical Timeframe:** Daily

**Description:**  
Uses XGBoost or LightGBM gradient boosting models to predict price direction from a rich feature set including technical, fundamental, and sentiment indicators.

**Parameters:**
- `n_estimators` (int): Number of boosting rounds (default: 200)
- `learning_rate` (float): Boosting learning rate (default: 0.05)
- `max_depth` (int): Maximum tree depth (default: 4)
- `feature_set` (str): Feature configuration ('technical', 'full')

**Signal Logic:**
- **Buy:** Predicted probability of up move > threshold
- **Sell:** Predicted probability of down move > threshold

**Strengths:** State-of-the-art tabular data performance, handles missing values  
**Weaknesses:** Requires feature engineering, hyperparameter tuning

---

#### Strategy 25: Reinforcement Learning Strategy

**Category:** Machine Learning  
**Complexity:** Expert  
**Typical Timeframe:** Daily, Intraday

**Description:**  
Uses a Deep Q-Network (DQN) or Proximal Policy Optimization (PPO) agent trained via reinforcement learning to make trading decisions.

**Parameters:**
- `algorithm` (str): RL algorithm ('DQN', 'PPO', 'A2C')
- `state_features` (list): State space features
- `reward_function` (str): Reward shaping ('sharpe', 'returns', 'sortino')
- `training_episodes` (int): Training episodes (default: 1000)

**Signal Logic:**
- **Buy/Sell/Hold:** Agent action based on learned policy

**Strengths:** Learns optimal policy directly, adapts to market regimes  
**Weaknesses:** Extremely complex, unstable training, requires extensive compute

---

### 2.7 Hybrid & Multi-Factor Strategies

Hybrid strategies combine multiple signal types or factor models for more robust signal generation.

---

#### Strategy 26: Multi-Factor Momentum + Value

**Category:** Hybrid  
**Complexity:** Advanced  
**Typical Timeframe:** Monthly, Weekly

**Description:**  
Combines momentum signals with value factors (P/E, P/B ratios) to select stocks that are both trending and fundamentally attractive.

**Parameters:**
- `momentum_lookback` (int): Momentum period in days (default: 252)
- `value_metric` (str): Value factor ('pe_ratio', 'pb_ratio', 'ev_ebitda')
- `momentum_weight` (float): Weight for momentum score (default: 0.5)
- `value_weight` (float): Weight for value score (default: 0.5)

**Signal Logic:**
- **Buy:** Combined score in top quartile of universe
- **Sell:** Combined score falls to bottom quartile

**Strengths:** Diversified factor exposure, reduces single-factor risk  
**Weaknesses:** Requires fundamental data, complex scoring

---

#### Strategy 27: Trend + Volatility Filter Strategy

**Category:** Hybrid  
**Complexity:** Intermediate  
**Typical Timeframe:** Daily

**Description:**  
Applies a volatility filter to a trend-following strategy. Only takes trend signals when volatility is within acceptable bounds.

**Parameters:**
- `trend_ma_period` (int): Trend MA period (default: 50)
- `atr_period` (int): ATR period for volatility filter (default: 14)
- `max_atr_pct` (float): Maximum ATR as % of price (default: 0.03)
- `min_atr_pct` (float): Minimum ATR as % of price (default: 0.005)

**Signal Logic:**
- **Buy:** Price > MA AND min_atr < ATR% < max_atr
- **Sell:** Price < MA OR ATR% > max_atr

**Strengths:** Avoids trading in extreme volatility, improves risk-adjusted returns  
**Weaknesses:** May miss valid signals during high-volatility trends

---

#### Strategy 28: Regime-Adaptive Strategy

**Category:** Hybrid  
**Complexity:** Expert  
**Typical Timeframe:** Daily

**Description:**  
Detects market regimes (trending, mean-reverting, high-volatility) using Hidden Markov Models or clustering, then applies the optimal sub-strategy for each regime.

**Parameters:**
- `regime_model` (str): Regime detection model ('hmm', 'kmeans', 'threshold')
- `n_regimes` (int): Number of market regimes (default: 3)
- `regime_features` (list): Features for regime detection

**Signal Logic:**
- **Trending Regime:** Apply trend-following strategy
- **Mean-Reverting Regime:** Apply mean reversion strategy
- **High-Volatility Regime:** Reduce position size or go to cash

**Strengths:** Adapts to changing market conditions  
**Weaknesses:** Regime detection is noisy, transition periods are difficult

---

#### Strategy 29: Ensemble Signal Strategy

**Category:** Hybrid  
**Complexity:** Advanced  
**Typical Timeframe:** Daily

**Description:**  
Aggregates signals from multiple strategies using voting or weighted averaging. Trades only when a majority of strategies agree.

**Parameters:**
- `strategies` (list): List of sub-strategies to ensemble
- `min_agreement` (float): Minimum fraction of strategies agreeing (default: 0.6)
- `weighting` (str): Signal weighting method ('equal', 'performance', 'sharpe')

**Signal Logic:**
- **Buy:** Fraction of strategies with buy signal ≥ min_agreement
- **Sell:** Fraction of strategies with sell signal ≥ min_agreement
- **Hold:** No consensus

**Strengths:** Reduces false signals, more robust than single strategies  
**Weaknesses:** Slower to react, may miss fast-moving opportunities

---

## 3. Supported Timeframes & Yahoo Finance Interval Codes

BQuant Algo Terminal uses Yahoo Finance interval codes for data retrieval. The following timeframes are supported:

| Timeframe | Yahoo Finance Code | Description | Max History | Best For |
|-----------|-------------------|-------------|-------------|----------|
| 1 Minute | `1m` | 1-minute OHLCV bars | 7 days | High-frequency, scalping |
| 2 Minutes | `2m` | 2-minute OHLCV bars | 60 days | Short-term intraday |
| 5 Minutes | `5m` | 5-minute OHLCV bars | 60 days | Intraday trading |
| 15 Minutes | `15m` | 15-minute OHLCV bars | 60 days | Intraday swing |
| 30 Minutes | `30m` | 30-minute OHLCV bars | 60 days | Intraday swing |
| 60 Minutes | `60m` | 60-minute OHLCV bars | 730 days | Intraday / short-term |
| 90 Minutes | `90m` | 90-minute OHLCV bars | 60 days | Intraday |
| 1 Hour | `1h` | Hourly OHLCV bars | 730 days | Short-term swing |
| 1 Day | `1d` | Daily OHLCV bars | Full history | Swing trading, position |
| 5 Days | `5d` | 5-day OHLCV bars | Full history | Weekly analysis |
| 1 Week | `1wk` | Weekly OHLCV bars | Full history | Position trading |
| 1 Month | `1mo` | Monthly OHLCV bars | Full history | Long-term investing |
| 3 Months | `3mo` | Quarterly OHLCV bars | Full history | Macro analysis |

### Timeframe Selection Guidelines

| Strategy Type | Recommended Timeframes | Notes |
|--------------|----------------------|-------|
| Scalping | `1m`, `2m`, `5m` | Requires low-latency execution |
| Day Trading | `5m`, `15m`, `30m`, `1h` | Close all positions before market close |
| Swing Trading | `1h`, `4h`, `1d` | Hold positions 2-10 days |
| Position Trading | `1d`, `1wk` | Hold positions weeks to months |
| Trend Following | `1d`, `1wk`, `1mo` | Longer timeframes reduce noise |
| Mean Reversion | `1h`, `1d` | Works best in range-bound conditions |
| Momentum | `1d`, `1wk`, `1mo` | Monthly rebalancing common |
| Statistical Arb | `1d`, `1h` | Requires sufficient data for statistics |
| Machine Learning | `1d` | Sufficient data for model training |

---

## 4. Quick Reference Strategy Comparison Table

| # | Strategy Name | Category | Complexity | Timeframe | Market Condition | Sharpe (Typical) |
|---|--------------|----------|------------|-----------|-----------------|-----------------|
| 1 | SMA Crossover | Trend Following | Beginner | Daily | Trending | 0.5–1.0 |
| 2 | EMA Crossover | Trend Following | Beginner | Daily/4H | Trending | 0.6–1.1 |
| 3 | Triple MA System | Trend Following | Intermediate | Daily | Strong Trend | 0.7–1.2 |
| 4 | MACD Strategy | Trend Following | Intermediate | Daily/4H | Trending | 0.6–1.0 |
| 5 | Parabolic SAR | Trend Following | Intermediate | Daily/1H | Trending | 0.5–0.9 |
| 6 | Bollinger Bands MR | Mean Reversion | Beginner | Daily/1H | Ranging | 0.6–1.1 |
| 7 | RSI Mean Reversion | Mean Reversion | Beginner | Daily/4H | Ranging | 0.5–1.0 |
| 8 | Stochastic Oscillator | Mean Reversion | Intermediate | Daily/4H | Ranging | 0.5–0.9 |
| 9 | Z-Score Reversion | Mean Reversion | Intermediate | Daily | Ranging | 0.7–1.2 |
| 10 | Keltner Channel | Mean Reversion | Intermediate | Daily/4H | Ranging | 0.6–1.1 |
| 11 | Price Momentum | Momentum | Beginner | Weekly/Monthly | Any | 0.8–1.3 |
| 12 | Rate of Change | Momentum | Beginner | Daily/Weekly | Trending | 0.5–0.9 |
| 13 | Dual Momentum | Momentum | Intermediate | Monthly | Any | 0.9–1.4 |
| 14 | Williams %R | Momentum | Intermediate | Daily/4H | Any | 0.5–0.9 |
| 15 | ATR Breakout | Volatility | Intermediate | Daily/4H | Breakout | 0.6–1.1 |
| 16 | VIX-Based Strategy | Volatility | Advanced | Daily | High Volatility | 0.8–1.5 |
| 17 | Donchian Breakout | Volatility/Trend | Beginner | Daily/Weekly | Trending | 0.6–1.0 |
| 18 | Squeeze Momentum | Volatility | Advanced | Daily/4H | Pre-Breakout | 0.8–1.4 |
| 19 | Pairs Trading | Stat Arb | Advanced | Daily | Market Neutral | 0.9–1.6 |
| 20 | ETF Arbitrage | Stat Arb | Advanced | Intraday/Daily | Any | 0.7–1.2 |
| 21 | Index Rebalancing | Stat Arb | Advanced | Daily | Event-Driven | 0.6–1.1 |
| 22 | Random Forest | Machine Learning | Advanced | Daily | Any | 0.8–1.4 |
| 23 | LSTM Prediction | Machine Learning | Expert | Daily/4H | Any | 0.7–1.3 |
| 24 | Gradient Boosting | Machine Learning | Advanced | Daily | Any | 0.9–1.5 |
| 25 | Reinforcement Learning | Machine Learning | Expert | Daily/Intraday | Any | 0.8–1.6 |
| 26 | Multi-Factor MV | Hybrid | Advanced | Monthly/Weekly | Any | 1.0–1.6 |
| 27 | Trend + Vol Filter | Hybrid | Intermediate | Daily | Trending | 0.8–1.3 |
| 28 | Regime-Adaptive | Hybrid | Expert | Daily | Any | 1.0–1.7 |
| 29 | Ensemble Signal | Hybrid | Advanced | Daily | Any | 0.9–1.5 |

---

## Notes & Disclaimers

> **⚠️ Important:** Past performance of any strategy does not guarantee future results. All Sharpe ratios listed are typical historical ranges and will vary significantly based on:
> - Asset class and specific symbol
> - Time period of backtesting
> - Parameter settings
> - Transaction costs and slippage
> - Market regime during the test period

> **📊 Data Quality:** Strategy performance is highly dependent on data quality. BQuant Algo Terminal uses Yahoo Finance as the primary data source with Alpha Vantage as a fallback. Always verify data integrity before live trading.

> **🔧 Parameter Optimization:** All default parameters are starting points. Use the built-in walk-forward optimization and robustness testing tools to find parameters appropriate for your specific use case.

---

*Last updated: 2026-02-28 | BQuant Algo Terminal Documentation*
