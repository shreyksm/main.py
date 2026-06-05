import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import norm
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

class InstitutionalDataAggregator:
    """
    Simulates aggregation of Level 3 data across Binance, Deribit, CME, Bybit, OKX.
    In production, this connects to WebSocket feeds for all exchanges.
    """
    def __init__(self):
        self.exchanges = ['Binance', 'Deribit', 'CME', 'Bybit', 'OKX']
        self.current_price = 64000  # Base price
        
    def fetch_aggregated_order_flow(self) -> Dict:
        """
        Returns aggregated institutional flow metrics:
        - Net Delta (Aggressive Buy/Sell)
        - Whale Wall Density (Liquidity > $1M)
        - CME Premium/Discount
        - Cross-Exchange Imbalance
        """
        # Simulating institutional data patterns
        # In real life: Sum of (Price * Size * Direction) from all exchange L3 feeds
        np.random.seed(int(datetime.now().timestamp()) % 100)
        
        flow_data = {
            'net_delta_volume': np.random.normal(5000, 2000), # Positive = Aggressive Buying
            'whale_walls_support': [63200, 62800, 61500],    # Aggregated liquidity walls
            'whale_walls_resistance': [64800, 65500, 67000],
            'cme_premium_bps': np.random.normal(15, 5),      # Basis points
            'exchange_imbalance_score': np.random.uniform(-0.8, 0.8), # -1 (Sell pressure) to 1 (Buy pressure)
            'dark_pool_proxy_volume': np.random.exponential(2000), # Off-book volume proxy
            'vix_term_structure': 'contango' if np.random.random() > 0.4 else 'backwardation'
        }
        return flow_data

    def detect_institutional_regime(self, flow: Dict) -> str:
        """
        Determines market regime based on combined institutional signals.
        """
        score = 0
        if flow['net_delta_volume'] > 3000: score += 2
        elif flow['net_delta_volume'] < -3000: score -= 2
        
        if flow['cme_premium_bps'] > 10: score += 1
        elif flow['cme_premium_bps'] < -10: score -= 1
        
        if flow['exchange_imbalance_score'] > 0.5: score += 2
        elif flow['exchange_imbalance_score'] < -0.5: score -= 2
        
        if flow['dark_pool_proxy_volume'] > 3000: score += 1 # Big players accumulating
        
        if score >= 4: return "STRONG_BULL"
        if score >= 2: return "MODERATE_BULL"
        if score <= -4: return "STRONG_BEAR"
        if score <= -2: return "MODERATE_BEAR"
        return "NEUTRAL_CHOP"

class OptionsStrategyEngine:
    def __init__(self, spot_price: float, days_to_expiry: int, iv: float):
        self.S = spot_price
        self.T = days_to_expiry / 365.0
        self.iv = iv
        self.r = 0.05 # Risk-free rate
        self.strategies = self._define_strategies()
        
    def _bs_price(self, K, option_type='call'):
        d1 = (np.log(self.S / K) + (self.r + 0.5 * self.iv**2) * self.T) / (self.iv * np.sqrt(self.T))
        d2 = d1 - self.iv * np.sqrt(self.T)
        
        if option_type == 'call':
            price = self.S * norm.cdf(d1) - K * np.exp(-self.r * self.T) * norm.cdf(d2)
        else:
            price = K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.S * norm.cdf(-d1)
        return price

    def _define_strategies(self) -> List[Dict]:
        """Defines 30+ distinct options strategies with logic."""
        atm = self.S
        otm_2p = self.S * 1.02
        otm_5p = self.S * 1.05
        itm_2p = self.S * 0.98
        itm_5p = self.S * 0.95
        
        strategies = [
            # Directional Bullish
            {"name": "Long Call", "type": "bullish", "legs": [("buy_call", atm)]},
            {"name": "Bull Call Spread", "type": "bullish", "legs": [("buy_call", atm), ("sell_call", otm_5p)]},
            {"name": "Synthetic Long", "type": "bullish", "legs": [("buy_call", atm), ("sell_put", atm)]},
            {"name": "Call Backspread", "type": "bullish_vol", "legs": [("sell_call", atm), ("buy_call", otm_2p, 2)]},
            {"name": "Risk Reversal (Bull)", "type": "bullish", "legs": [("sell_put", itm_2p), ("buy_call", otm_2p)]},
            
            # Directional Bearish
            {"name": "Long Put", "type": "bearish", "legs": [("buy_put", atm)]},
            {"name": "Bear Put Spread", "type": "bearish", "legs": [("buy_put", atm), ("sell_put", itm_5p)]},
            {"name": "Synthetic Short", "type": "bearish", "legs": [("sell_call", atm), ("buy_put", atm)]},
            {"name": "Put Backspread", "type": "bearish_vol", "legs": [("sell_put", atm), ("buy_put", itm_2p, 2)]},
            {"name": "Risk Reversal (Bear)", "type": "bearish", "legs": [("buy_put", itm_2p), ("sell_call", otm_2p)]},

            # Neutral / Income
            {"name": "Iron Condor", "type": "neutral", "legs": [("sell_put", itm_2p), ("buy_put", itm_5p), ("sell_call", otm_2p), ("buy_call", otm_5p)]},
            {"name": "Short Straddle", "type": "neutral_short_vol", "legs": [("sell_call", atm), ("sell_put", atm)]},
            {"name": "Short Strangle", "type": "neutral_short_vol", "legs": [("sell_call", otm_2p), ("sell_put", itm_2p)]},
            {"name": "Butterfly (Call)", "type": "neutral", "legs": [("buy_call", itm_2p), ("sell_call", atm, 2), ("buy_call", otm_2p)]},
            {"name": "Butterfly (Put)", "type": "neutral", "legs": [("buy_put", itm_2p), ("sell_put", atm, 2), ("buy_put", otm_2p)]},
            {"name": "Calendar Call", "type": "neutral_time", "legs": [("sell_call_short", atm), ("buy_call_long", atm)]}, # Simplified
            
            # Volatility Expansion (Breakout)
            {"name": "Long Straddle", "type": "vol_long", "legs": [("buy_call", atm), ("buy_put", atm)]},
            {"name": "Long Strangle", "type": "vol_long", "legs": [("buy_call", otm_2p), ("buy_put", itm_2p)]},
            {"name": "Guts", "type": "vol_long_deep", "legs": [("buy_call", itm_2p), ("buy_put", otm_2p)]},
            
            # Advanced / Skew Based
            {"name": "Ratio Call Spread", "type": "bullish_ratio", "legs": [("buy_call", atm), ("sell_call", otm_2p, 2)]},
            {"name": "Ratio Put Spread", "type": "bearish_ratio", "legs": [("buy_put", atm), ("sell_put", itm_2p, 2)]},
            {"name": "Jade Lizard", "type": "bullish_income", "legs": [("sell_put", itm_5p), ("sell_call", otm_2p), ("buy_call", otm_5p)]},
            {"name": "Reverse Iron Condor", "type": "vol_long_range", "legs": [("buy_put", itm_2p), ("sell_put", itm_5p), ("buy_call", otm_2p), ("sell_call", otm_5p)]},
            {"name": "Double Diagonal", "type": "neutral_time_vol", "legs": [("sell_call_short", otm_2p), ("buy_call_long", otm_5p), ("sell_put_short", itm_2p), ("buy_put_long", itm_5p)]},
            
            # Tail Risk / Black Swan
            {"name": "Tail Hedge Put", "type": "hedge", "legs": [("buy_put", itm_5p)]},
            {"name": "Seagull", "type": "bullish_hedge", "legs": [("buy_call", atm), ("sell_call", otm_5p), ("sell_put", itm_5p)]},
            {"name": "Collar", "type": "hedge", "legs": [("long_stock", atm), ("buy_put", itm_5p), ("sell_call", otm_5p)]},
            {"name": "Protective Put", "type": "hedge", "legs": [("long_stock", atm), ("buy_put", atm)]},
            
            # Exotic/Complex
            {"name": "Broken Wing Butterfly", "type": "biased_neutral", "legs": [("buy_put", itm_5p), ("sell_put", itm_2p, 2), ("buy_put", atm)]}, # Skewed
            {"name": "Christmas Tree", "type": "bearish_ratio", "legs": [("buy_put", atm), ("sell_put", itm_2p, 2), ("buy_put", itm_5p)]},
            {"name": "Condor Spread", "type": "neutral_wide", "legs": [("buy_put", itm_5p), ("sell_put", itm_2p), ("sell_call", otm_2p), ("buy_call", otm_5p)]},
            {"name": "Box Spread", "type": "arb", "legs": [("buy_call", itm_2p), ("sell_call", otm_2p), ("sell_put", itm_2p), ("buy_put", otm_2p)]},
            {"name": "Conversion", "type": "arb", "legs": [("long_stock", atm), ("buy_put", atm), ("sell_call", atm)]}
        ]
        return strategies

    def simulate_pnl(self, strategy: Dict, future_prices: np.ndarray) -> float:
        """Simulates PnL for a strategy given a range of future prices."""
        total_pnl = []
        
        for price in future_prices:
            strategy_pnl = 0
            cost = 0
            
            for leg in strategy['legs']:
                action = leg[0]
                strike = leg[1]
                qty = leg[2] if len(leg) > 2 else 1
                
                # Calculate intrinsic value at expiry (simplified for T+2)
                call_val = max(0, price - strike)
                put_val = max(0, strike - price)
                
                # Initial Cost (approximate)
                premium = self._bs_price(strike, 'call') if 'call' in action else self._bs_price(strike, 'put')
                
                if action == 'buy_call':
                    strategy_pnl += (call_val - premium) * qty
                elif action == 'sell_call':
                    strategy_pnl += (premium - call_val) * qty
                elif action == 'buy_put':
                    strategy_pnl += (put_val - premium) * qty
                elif action == 'sell_put':
                    strategy_pnl += (premium - put_val) * qty
                elif action == 'long_stock':
                    strategy_pnl += (price - self.S) * qty
            
            total_pnl.append(strategy_pnl)
            
        return np.mean(total_pnl), np.std(total_pnl), max(total_pnl), min(total_pnl)

class InstitutionalStrategySelector:
    def __init__(self):
        self.aggregator = InstitutionalDataAggregator()
        
    def analyze_and_select(self) -> Dict:
        # 1. Get Institutional Data
        flow = self.aggregator.fetch_aggregated_order_flow()
        regime = self.aggregator.detect_institutional_regime(flow)
        
        # 2. Setup Option Engine (2-3 Days Expiry)
        spot = self.aggregator.current_price
        engine = OptionsStrategyEngine(spot, days_to_expiry=2.5, iv=0.65) # High BTC IV
        
        # 3. Generate Price Scenarios based on Flow
        # If strong buy flow, skew scenarios upward
        drift = 0
        if regime == "STRONG_BULL": drift = 0.04
        elif regime == "MODERATE_BULL": drift = 0.02
        elif regime == "STRONG_BEAR": drift = -0.04
        elif regime == "MODERATE_BEAR": drift = -0.02
        
        # Monte Carlo Simulation of future prices
        scenarios = np.linspace(spot * (0.90 + drift), spot * (1.10 + drift), 50)
        
        # 4. Evaluate ALL 30 Strategies
        results = []
        for strat in engine.strategies:
            avg_pnl, risk, max_prof, max_loss = engine.simulate_pnl(strat, scenarios)
            
            # Filter by Regime Compatibility
            compatible = False
            if regime in ["STRONG_BULL", "MODERATE_BULL"] and strat['type'] in ['bullish', 'bullish_vol', 'vol_long']:
                compatible = True
            elif regime in ["STRONG_BEAR", "MODERATE_BEAR"] and strat['type'] in ['bearish', 'bearish_vol', 'vol_long']:
                compatible = True
            elif regime == "NEUTRAL_CHOP" and strat['type'] in ['neutral', 'neutral_short_vol', 'arb']:
                compatible = True
            # Always allow vol long if dark pool volume suggests explosion
            if flow['dark_pool_proxy_volume'] > 2500 and 'vol_long' in strat['type']:
                compatible = True
                
            # Risk Adjusted Score (Sharpe-like)
            score = (avg_pnl / risk) if risk > 0 else 0
            if not compatible: score *= 0.5 # Penalty for fighting the tape
            
            results.append({
                "strategy_name": strat['name'],
                "type": strat['type'],
                "expected_pnl": avg_pnl,
                "risk_std": risk,
                "max_profit": max_prof,
                "max_loss": max_loss,
                "score": score,
                "compatible": compatible,
                "legs": strat['legs']
            })
            
        # Sort by Score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "regime": regime,
            "flow_metrics": flow,
            "top_5_strategies": results[:5],
            "all_strategies_ranked": results
        }

# Run the analysis
if __name__ == "__main__":
    selector = InstitutionalStrategySelector()
    report = selector.analyze_and_select()
    
    print(f"--- INSTITUTIONAL BTC OPTIONS ANALYSIS ---")
    print(f"Regime Detected: {report['regime']}")
    print(f"CME Premium: {report['flow_metrics']['cme_premium_bps']:.2f} bps")
    print(f"Net Delta Flow: {report['flow_metrics']['net_delta_volume']:.0f}")
    print(f"Dark Pool Proxy: {report['flow_metrics']['dark_pool_proxy_volume']:.0f}")
    print("-" * 40)
    print("TOP 5 PROFITABLE STRATEGIES (Next 2-3 Days):")
    
    for i, strat in enumerate(report['top_5_strategies']):
        print(f"\n{i+1}. {strat['strategy_name']} (Score: {strat['score']:.2f})")
        print(f"   Type: {strat['type']}")
        print(f"   Exp. PnL: ${strat['expected_pnl']:.2f} | Risk: ${strat['risk_std']:.2f}")
        print(f"   Max Profit: ${strat['max_profit']:.2f} | Max Loss: ${strat['max_loss']:.2f}")
        print(f"   Legs: {strat['legs']}")
        
    # Visual representation text
    print("\n" + "="*40)
    print("VISUAL PROFITABILITY HEATMAP (Top 10)")
    print("="*40)
    top_10 = report['all_strategies_ranked'][:10]
    max_score = top_10[0]['score']
    
    for strat in top_10:
        bar_len = int((strat['score'] / max_score) * 40)
        bar = "█" * bar_len
        color_code = "🟢" if strat['score'] > 1.5 else "🟡" if strat['score'] > 0.5 else "🔴"
        print(f"{color_code} {strat['strategy_name']:<25} [{bar}] {strat['score']:.2f}")
