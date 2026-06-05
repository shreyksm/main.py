# BTC Options Trading Strategy API

## Overview
Automatic BTC Out-of-Money (OTM) Options Trading Strategy for 2-3 day expiry trading. This system analyzes expiry dates, liquidity metrics, and probability heatmaps to generate trading signals.

## Features

### Core Capabilities
- **Real-time BTC Price Fetching**: Gets current BTC spot price from CoinGecko API
- **Expiry Date Analysis**: Identifies next 2-3 weekly option expiry dates (Fridays)
- **OTM Strike Calculation**: Automatically calculates out-of-the-money strike prices (3% OTM by default)
- **Liquidity Analysis**: Analyzes volume, open interest, and bid-ask spreads from Deribit
- **Probability Heatmap**: Generates Black-Scholes based probability distributions for price movements
- **Trading Signals**: Produces actionable trade recommendations with entry zones, targets, and stop-losses
- **Risk Management**: Includes position sizing, max loss per trade, and stop-loss levels

### API Endpoints

#### 1. Full Analysis
```bash
GET /api/analysis
```
Returns comprehensive analysis including market overview, expiry dates, liquidity, heatmap, and trading signals.

#### 2. Trading Signals
```bash
GET /api/signals
```
Returns only trading signal recommendations with:
- Trade type (BUY_OTM_CALL / BUY_OTM_PUT)
- Strike price and expiry date
- Probability of profit
- Risk/reward ratio
- Entry zone, target exit, and stop-loss levels
- Confidence score

#### 3. Probability Heatmap
```bash
GET /api/heatmap
```
Returns probability distribution data including:
- Current BTC price
- Implied volatility (65% default)
- Days to expiry
- Support and resistance levels
- Max pain calculation
- Probability distribution for each strike

#### 4. Liquidity Analysis
```bash
GET /api/liquidity?exchange=deribit
```
Returns liquidity metrics:
- 24h volume
- Open interest
- Average bid-ask spread
- Liquidity score (0-100)
- Top liquid strikes

Supported exchanges: deribit, binance, bybit, okx

#### 5. Expiry Dates
```bash
GET /api/expiry?days=2
```
Returns next option expiry dates (default: 2 days ahead).

#### 6. Webhook Integration
```bash
POST /webhook
Content-Type: application/json
{
  "trigger_analysis": true,
  "source": "your_system"
}
```
Triggers full analysis and returns results. Useful for automated trading systems.

## Strategy Details

### OTM Strike Selection
- **Calls**: Strikes 3-10% above current BTC price
- **Puts**: Strikes 3-10% below current BTC price
- Strike intervals automatically adjust based on BTC price level:
  - < $10k: $100 intervals
  - $10k-$30k: $250 intervals
  - $30k-$50k: $500 intervals
  - $50k-$70k: $1000 intervals
  - > $70k: $2000 intervals

### Probability Calculations
Uses Black-Scholes model with:
- Default implied volatility: 65% (annualized)
- Time to expiry in years
- Log-normal price distribution
- Cumulative normal distribution for ITM probabilities

### Risk Management
- **Position Sizing**: 1% of portfolio per trade
- **Max Loss**: 2% of portfolio per trade
- **Stop Loss Levels**: 5% above/below current price
- **Risk/Reward Ratio**: 3.0 (target)

### Trading Signal Components
Each signal includes:
- Trade type and direction
- Strike price and expiry
- Days to expiry
- Probability of profit
- Entry zone ($500 range around strike)
- Target exit (1.5x strike)
- Stop-loss (0.3x strike)

## Installation

### Requirements
- Python 3.8+
- Flask
- Pandas
- NumPy
- SciPy
- Requests

### Install Dependencies
```bash
pip install flask gunicorn pandas numpy requests scipy
```

### Run the Server
```bash
python app.py
```
Server runs on `http://0.0.0.0:10000`

### Production Deployment (Render/gunicorn)
```bash
gunicorn --bind 0.0.0.0:10000 app:app
```

## Example Usage

### Get Trading Signals
```bash
curl http://localhost:10000/api/signals
```

Response example:
```json
{
  "btc_current_price": 59685,
  "confidence_score": 62.23,
  "recommended_trades": [
    {
      "type": "BUY_OTM_CALL",
      "strike": 61000,
      "expiry": "2026-06-12",
      "days_to_expiry": 6,
      "probability_profit": 0.613,
      "risk_reward_ratio": 3.0,
      "entry_zone": "$60500 - $61500",
      "target_exit": "$91500",
      "stop_loss": "$18300"
    }
  ]
}
```

### Get Heatmap Data
```bash
curl http://localhost:10000/api/heatmap
```

### Trigger Analysis via Webhook
```bash
curl -X POST http://localhost:10000/webhook \
  -H "Content-Type: application/json" \
  -d '{"trigger_analysis": true}'
```

## Configuration

### Customization Points
1. **Implied Volatility**: Modify `iv = 0.65` in `generate_heatmap()` method
2. **OTM Distance**: Change `strike_distance = 0.03` in `generate_trading_signals()`
3. **Expiry Filter**: Adjust `days_ahead` parameter in `get_next_expiry_dates()`
4. **Risk Parameters**: Edit values in `generate_trading_signals()` risk_metrics section

### Exchange Integration
Currently configured for Deribit API. To add more exchanges:
1. Add exchange to `supported_exchanges` list
2. Implement exchange-specific API calls in `analyze_liquidity()`
3. Parse instrument names according to exchange format

## Important Notes

### Disclaimer
- This is a **high-risk** trading strategy
- Recommended capital allocation: 5-10% of portfolio
- Past performance does not guarantee future results
- Always do your own research before trading

### Limitations
- Liquidity data may be limited if Deribit API is unavailable
- Implied volatility is set to default 65% (can be fetched from options chain)
- Does not execute trades automatically (signal generation only)
- Requires manual integration with brokerage/exchange for execution

### Production Considerations
1. Add API key authentication for endpoints
2. Implement rate limiting
3. Add logging and monitoring
4. Set up alerts for significant market moves
5. Integrate real options chain data for accurate IV
6. Add backtesting capabilities
7. Implement position tracking and P&L monitoring

## Architecture

```
BTCOptionsStrategy Class
├── fetch_btc_price() - Get current BTC price
├── get_next_expiry_dates() - Find upcoming expiries
├── calculate_otm_strikes() - Generate OTM strike prices
├── analyze_liquidity() - Fetch volume/OI data
├── generate_heatmap() - Create probability distribution
├── generate_trading_signals() - Produce trade recommendations
└── get_full_analysis() - Comprehensive analysis

Flask API Routes
├── GET /api/analysis
├── GET /api/signals
├── GET /api/heatmap
├── GET /api/liquidity
├── GET /api/expiry
└── POST /webhook
```

## License
MIT License - Use at your own risk
