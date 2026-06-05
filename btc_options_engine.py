"""
Advanced BTC Options Strategy Engine
Uses Order Flow, Whale Data, and Footprint to select from 30+ strategies
with visual profitability scoring.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math

# ========================
# DATA STRUCTURES
# ========================

class MarketRegime(Enum):
    BULLISH_BREAKOUT = "bullish_breakout"
    BEARISH_BREAKDOWN = "bearish_breakdown"
    RANGE_BOUND_HIGH_VOL = "range_high_vol"
    RANGE_BOUND_LOW_VOL = "range_low_vol"
    REVERSAL_TOP = "reversal_top"
    REVERSAL_BOTTOM = "reversal_bottom"
    MOMENTUM_CONTINUATION_UP = "momentum_up"
    MOMENTUM_CONTINUATION_DOWN = "momentum_down"

@dataclass
class OrderBookData:
    bids: List[Tuple[float, float]]  # (price, size)
    asks: List[Tuple[float, float]]  # (price, size)
    whale_walls: List[Dict]  # Detected whale levels
    
@dataclass
class FootprintData:
    price_levels: List[float]
    delta_volume: List[float]  # Buy vol - Sell vol at each level
    imbalance_ratio: List[float]
    poc: float  # Point of Control
    value_area_high: float
    value_area_low: float

@dataclass
class StrategySignal:
    strategy_name: str
    strategy_type: str
    direction: str
    entry_zone: Tuple[float, float]
    targets: List[float]
    stop_loss: float
    max_profit: float
    max_loss: float
    probability_of_profit: float
    expected_value: float
    confidence_score: float
    reasoning: str
    required_regime: MarketRegime
    legs: List[Dict]  # Option legs details

# ========================
# 30+ OPTIONS STRATEGIES DEFINITIONS
# ========================

class StrategyLibrary:
    """Defines 30+ options strategies with payoff characteristics"""
    
    @staticmethod
    def get_all_strategies() -> List[Dict]:
        return [
            # DIRECTIONAL BULLISH (1-8)
            {"name": "Long Call", "type": "bullish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "high"},
            {"name": "Bull Call Spread", "type": "bullish", "max_risk": "limited", "max_reward": "limited", "volatility_view": "neutral"},
            {"name": "Synthetic Long", "type": "bullish", "max_risk": "unlimited", "max_reward": "unlimited", "volatility_view": "neutral"},
            {"name": "Call Ratio Backspread", "type": "bullish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "very_high"},
            {"name": "Bull Put Spread", "type": "bullish", "max_risk": "limited", "max_reward": "limited", "volatility_view": "low"},
            {"name": "Covered Call", "type": "bullish_neutral", "max_risk": "large", "max_reward": "limited", "volatility_view": "low"},
            {"name": "Protective Collar", "type": "bullish_hedge", "max_risk": "limited", "max_reward": "limited", "volatility_view": "low"},
            {"name": "Diagonal Bull Call", "type": "bullish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "medium"},
            
            # DIRECTIONAL BEARISH (9-16)
            {"name": "Long Put", "type": "bearish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "high"},
            {"name": "Bear Put Spread", "type": "bearish", "max_risk": "limited", "max_reward": "limited", "volatility_view": "neutral"},
            {"name": "Synthetic Short", "type": "bearish", "max_risk": "unlimited", "max_reward": "unlimited", "volatility_view": "neutral"},
            {"name": "Put Ratio Backspread", "type": "bearish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "very_high"},
            {"name": "Bull Call Spread", "type": "bearish", "max_risk": "limited", "max_reward": "limited", "volatility_view": "low"},
            {"name": "Covered Put", "type": "bearish_neutral", "max_risk": "large", "max_reward": "limited", "volatility_view": "low"},
            {"name": "Reverse Collar", "type": "bearish_hedge", "max_risk": "limited", "max_reward": "limited", "volatility_view": "low"},
            {"name": "Diagonal Bear Put", "type": "bearish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "medium"},
            
            # VOLATILITY EXPANSION (17-22)
            {"name": "Long Straddle", "type": "volatility_long", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "expansion"},
            {"name": "Long Strangle", "type": "volatility_long", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "expansion"},
            {"name": "Strip", "type": "volatility_long_bearish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "expansion"},
            {"name": "Strap", "type": "volatility_long_bullish", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "expansion"},
            {"name": "Guts", "type": "volatility_long", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "extreme_expansion"},
            {"name": "Christmas Tree", "type": "volatility_directional", "max_risk": "limited", "max_reward": "unlimited", "volatility_view": "expansion"},
            
            # VOLATILITY CONTRACTION (23-27)
            {"name": "Short Straddle", "type": "volatility_short", "max_risk": "unlimited", "max_reward": "limited", "volatility_view": "contraction"},
            {"name": "Short Strangle", "type": "volatility_short", "max_risk": "unlimited", "max_reward": "limited", "volatility_view": "contraction"},
            {"name": "Iron Condor", "type": "volatility_short", "max_risk": "limited", "max_reward": "limited", "volatility_view": "contraction"},
            {"name": "Iron Butterfly", "type": "volatility_short", "max_risk": "limited", "max_reward": "limited", "volatility_view": "contraction"},
            {"name": "Jade Lizard", "type": "volatility_short_bullish", "max_risk": "limited", "max_reward": "limited", "volatility_view": "contraction"},
            
            # NEUTRAL/RANGE (28-30+)
            {"name": "Calendar Spread", "type": "neutral_time", "max_risk": "limited", "max_reward": "limited", "volatility_view": "term_structure"},
            {"name": "Double Calendar", "type": "neutral_time", "max_risk": "limited", "max_reward": "limited", "volatility_view": "term_structure"},
            {"name": "Ratio Spread", "type": "neutral_directional", "max_risk": "unlimited", "max_reward": "limited", "volatility_view": "skew"},
            {"name": "Broken Wing Butterfly", "type": "biased_neutral", "max_risk": "limited", "max_reward": "limited", "volatility_view": "skew"},
            {"name": "Condor Spread", "type": "neutral", "max_risk": "limited", "max_reward": "limited", "volatility_view": "low"},
        ]

# ========================
# ORDER FLOW ANALYZER
# ========================

class OrderFlowAnalyzer:
    """Analyzes whale orders, orderbook heatmap, and footprint"""
    
    def __init__(self):
        self.whale_threshold_usd = 500000  # $500k minimum for whale
        
    def detect_whale_walls(self, orderbook: OrderBookData, current_price: float) -> List[Dict]:
        """Identify significant liquidity walls"""
        whale_levels = []
        
        # Check bids
        for price, size in orderbook.bids:
            notional = price * size
            if notional >= self.whale_threshold_usd:
                distance_pct = ((current_price - price) / current_price) * 100
                whale_levels.append({
                    'type': 'support',
                    'price': price,
                    'size': size,
                    'notional_usd': notional,
                    'distance_pct': abs(distance_pct),
                    'strength': 'strong' if notional > 2000000 else 'moderate'
                })
        
        # Check asks
        for price, size in orderbook.asks:
            notional = price * size
            if notional >= self.whale_threshold_usd:
                distance_pct = ((price - current_price) / current_price) * 100
                whale_levels.append({
                    'type': 'resistance',
                    'price': price,
                    'size': size,
                    'notional_usd': notional,
                    'distance_pct': abs(distance_pct),
                    'strength': 'strong' if notional > 2000000 else 'moderate'
                })
        
        return sorted(whale_levels, key=lambda x: x['notional_usd'], reverse=True)
    
    def calculate_orderbook_imbalance(self, orderbook: OrderBookData, depth_levels: int = 10) -> Dict:
        """Calculate bid/ask imbalance ratio"""
        total_bid_vol = sum([size for _, size in orderbook.bids[:depth_levels]])
        total_ask_vol = sum([size for _, size in orderbook.asks[:depth_levels]])
        
        if total_ask_vol == 0:
            return {'ratio': float('inf'), 'direction': 'extreme_buy'}
        
        ratio = total_bid_vol / total_ask_vol
        
        if ratio > 2.0:
            direction = 'strong_buy_pressure'
        elif ratio > 1.3:
            direction = 'buy_pressure'
        elif ratio < 0.5:
            direction = 'strong_sell_pressure'
        elif ratio < 0.77:
            direction = 'sell_pressure'
        else:
            direction = 'balanced'
            
        return {
            'ratio': ratio,
            'bid_volume': total_bid_vol,
            'ask_volume': total_ask_vol,
            'direction': direction,
            'imbalance_pct': abs(ratio - 1) * 100
        }
    
    def analyze_footprint(self, footprint: FootprintData) -> Dict:
        """Analyze footprint for absorption, imbalances, and POC shifts"""
        signals = []
        
        # Find highest delta
        max_delta_idx = np.argmax(footprint.delta_volume)
        min_delta_idx = np.argmin(footprint.delta_volume)
        
        # Detect absorption (high volume but low price movement)
        for i in range(len(footprint.price_levels) - 1):
            vol = abs(footprint.delta_volume[i])
            price_change = abs(footprint.price_levels[i] - footprint.price_levels[i+1])
            
            if vol > np.mean(abs(np.array(footprint.delta_volume))) * 2 and price_change < 0.001:
                signals.append({
                    'type': 'absorption',
                    'price': footprint.price_levels[i],
                    'volume': vol,
                    'signal': 'reversal_likely'
                })
        
        # Identify POC (Point of Control)
        poc_signal = 'at_poc' if abs(footprint.poc - footprint.price_levels[len(footprint.price_levels)//2]) < 0.005 else 'away_from_poc'
        
        # Delta divergence
        if footprint.delta_volume[max_delta_idx] > 0 and footprint.price_levels[max_delta_idx] < footprint.poc:
            signals.append({
                'type': 'bullish_divergence',
                'strength': 'strong',
                'price': footprint.price_levels[max_delta_idx]
            })
        
        return {
            'poc': footprint.poc,
            'value_area': (footprint.value_area_low, footprint.value_area_high),
            'max_positive_delta': footprint.delta_volume[max_delta_idx],
            'max_negative_delta': footprint.delta_volume[min_delta_idx],
            'signals': signals,
            'poc_position': poc_signal
        }
    
    def determine_market_regime(self, orderbook: OrderBookData, footprint: FootprintData, 
                               current_price: float) -> MarketRegime:
        """Determine current market regime based on microstructure"""
        
        imbalance = self.calculate_orderbook_imbalance(orderbook)
        footprint_analysis = self.analyze_footprint(footprint)
        whale_walls = self.detect_whale_walls(orderbook, current_price)
        
        # Logic tree for regime detection
        if imbalance['direction'] in ['strong_buy_pressure', 'buy_pressure']:
            if len([w for w in whale_walls if w['type'] == 'resistance' and w['distance_pct'] < 2]) == 0:
                return MarketRegime.MOMENTUM_CONTINUATION_UP
            else:
                return MarketRegime.BULLISH_BREAKOUT
                
        elif imbalance['direction'] in ['strong_sell_pressure', 'sell_pressure']:
            if len([w for w in whale_walls if w['type'] == 'support' and w['distance_pct'] < 2]) == 0:
                return MarketRegime.MOMENTUM_CONTINUATION_DOWN
            else:
                return MarketRegime.BEARISH_BREAKDOWN
        
        # Check for reversal patterns
        absorption_signals = [s for s in footprint_analysis['signals'] if s['type'] == 'absorption']
        if absorption_signals:
            if footprint_analysis['max_positive_delta'] > abs(footprint_analysis['max_negative_delta']):
                return MarketRegime.REVERSAL_BOTTOM
            else:
                return MarketRegime.REVERSAL_TOP
        
        # Range bound detection
        if imbalance['direction'] == 'balanced':
            # Check volatility via value area width
            va_width_pct = ((footprint_analysis['value_area'][1] - footprint_analysis['value_area'][0]) / current_price) * 100
            if va_width_pct > 2.0:
                return MarketRegime.RANGE_BOUND_HIGH_VOL
            else:
                return MarketRegime.RANGE_BOUND_LOW_VOL
        
        # Default
        return MarketRegime.RANGE_BOUND_LOW_VOL

# ========================
# STRATEGY SCORING ENGINE
# ========================

class StrategyScorer:
    """Scores all 30+ strategies and ranks by profitability"""
    
    def __init__(self):
        self.strategy_lib = StrategyLibrary()
        
    def score_strategy(self, strategy: Dict, regime: MarketRegime, 
                      orderbook_data: Dict, footprint_data: Dict,
                      current_price: float, days_to_expiry: int) -> Dict:
        """Score a single strategy based on fit with current conditions"""
        
        base_score = 0.0
        reasoning = []
        
        # Regime match scoring (0-40 points)
        regime_matches = {
            MarketRegime.BULLISH_BREAKOUT: ['bullish', 'volatility_long_bullish'],
            MarketRegime.BEARISH_BREAKDOWN: ['bearish', 'volatility_long_bearish'],
            MarketRegime.RANGE_BOUND_HIGH_VOL: ['volatility_short', 'neutral'],
            MarketRegime.RANGE_BOUND_LOW_VOL: ['volatility_long', 'neutral_time'],
            MarketRegime.REVERSAL_TOP: ['bearish', 'volatility_long_bearish'],
            MarketRegime.REVERSAL_BOTTOM: ['bullish', 'volatility_long_bullish'],
            MarketRegime.MOMENTUM_CONTINUATION_UP: ['bullish', 'volatility_long_bullish'],
            MarketRegime.MOMENTUM_CONTINUATION_DOWN: ['bearish', 'volatility_long_bearish'],
        }
        
        matching_types = regime_matches.get(regime, [])
        if strategy['type'] in matching_types:
            base_score += 35
            reasoning.append(f"Perfect regime match for {regime.value}")
        elif any(x in strategy['type'] for x in matching_types):
            base_score += 20
            reasoning.append(f"Partial regime match")
        
        # Volatility view scoring (0-25 points)
        vol_match = False
        if 'expansion' in strategy['volatility_view'] or 'very_high' in strategy['volatility_view']:
            # Check if footprint shows expansion signals
            if footprint_data.get('max_positive_delta', 0) > 1000 or footprint_data.get('max_negative_delta', 0) < -1000:
                base_score += 25
                vol_match = True
                reasoning.append("Volatility expansion confirmed by footprint")
        elif 'contraction' in strategy['volatility_view'] or 'low' in strategy['volatility_view']:
            if orderbook_data.get('imbalance_pct', 0) < 30:
                base_score += 25
                vol_match = True
                reasoning.append("Low imbalance supports volatility contraction")
        
        if not vol_match:
            base_score += 10
            reasoning.append("Neutral volatility assumption")
        
        # Risk/Reward scoring (0-20 points)
        if strategy['max_risk'] == 'limited' and strategy['max_reward'] == 'unlimited':
            base_score += 20
            reasoning.append("Asymmetric risk/reward profile")
        elif strategy['max_risk'] == 'limited' and strategy['max_reward'] == 'limited':
            base_score += 15
            reasoning.append("Defined risk defined reward")
        else:
            base_score += 5
            reasoning.append("Higher risk profile")
        
        # Time decay consideration (0-15 points)
        if days_to_expiry <= 3:
            if 'time' in strategy['type'] or 'short' in strategy['type']:
                base_score += 15
                reasoning.append(f"Optimal for {days_to_expiry} DTE theta decay")
            elif 'long' in strategy['type'] and 'volatility' in strategy['type']:
                base_score += 5
                reasoning.append("Gamma risk high for long vol with low DTE")
        else:
            base_score += 10
            reasoning.append("Standard time horizon")
        
        # Calculate expected metrics (simplified)
        prob_profit = min(0.85, max(0.15, base_score / 100))
        max_profit_potential = 3.0 if strategy['max_reward'] == 'unlimited' else 1.5
        max_loss_risk = 1.0 if strategy['max_risk'] == 'limited' else 2.5
        
        expected_value = (prob_profit * max_profit_potential) - ((1 - prob_profit) * max_loss_risk)
        
        return {
            'strategy_name': strategy['name'],
            'strategy_type': strategy['type'],
            'total_score': min(100, base_score),
            'probability_of_profit': round(prob_profit, 3),
            'expected_value': round(expected_value, 3),
            'confidence_score': round(base_score / 100, 2),
            'reasoning': "; ".join(reasoning),
            'risk_profile': f"{strategy['max_risk']} risk / {strategy['max_reward']} reward",
            'volatility_view': strategy['volatility_view']
        }
    
    def rank_all_strategies(self, regime: MarketRegime, orderbook_data: Dict, 
                           footprint_data: Dict, current_price: float,
                           days_to_expiry: int = 2) -> List[Dict]:
        """Score and rank all 30+ strategies"""
        
        all_strategies = self.strategy_lib.get_all_strategies()
        scored_strategies = []
        
        for strategy in all_strategies:
            score_result = self.score_strategy(
                strategy, regime, orderbook_data, footprint_data,
                current_price, days_to_expiry
            )
            scored_strategies.append(score_result)
        
        # Sort by total score descending
        ranked = sorted(scored_strategies, key=lambda x: x['total_score'], reverse=True)
        
        return ranked

# ========================
# VISUALIZATION GENERATOR
# ========================

class VisualStrategySelector:
    """Generates visual representations of strategy rankings"""
    
    @staticmethod
    def generate_heatmap_data(ranked_strategies: List[Dict], top_n: int = 10) -> Dict:
        """Generate data for visual heatmap of top strategies"""
        
        heatmap_data = {
            'labels': [],
            'scores': [],
            'probabilities': [],
            'expected_values': [],
            'categories': [],
            'color_scale': []  # 0-100 for color intensity
        }
        
        for i, strat in enumerate(ranked_strategies[:top_n]):
            heatmap_data['labels'].append(strat['strategy_name'])
            heatmap_data['scores'].append(strat['total_score'])
            heatmap_data['probabilities'].append(strat['probability_of_profit'])
            heatmap_data['expected_values'].append(strat['expected_value'])
            heatmap_data['categories'].append(strat['strategy_type'])
            heatmap_data['color_scale'].append(strat['total_score'])
        
        return heatmap_data
    
    @staticmethod
    def generate_strategy_comparison_table(ranked_strategies: List[Dict], top_n: int = 5) -> str:
        """Generate ASCII table of top strategies"""
        
        lines = []
        lines.append("=" * 120)
        lines.append(f"{'RANK':<6}{'STRATEGY':<30}{'SCORE':<8}{'PROB%':<8}{'EV':<8}{'TYPE':<25}{'RISK/REWARD':<25}")
        lines.append("=" * 120)
        
        for i, strat in enumerate(ranked_strategies[:top_n], 1):
            lines.append(
                f"{i:<6}"
                f"{strat['strategy_name']:<30}"
                f"{strat['total_score']:<8.1f}"
                f"{strat['probability_of_profit']*100:<8.1f}"
                f"{strat['expected_value']:<8.2f}"
                f"{strat['strategy_type']:<25}"
                f"{strat['risk_profile']:<25}"
            )
        
        lines.append("=" * 120)
        return "\n".join(lines)
    
    @staticmethod
    def generate_recommendation_chart(ranked_strategies: List[Dict]) -> Dict:
        """Generate structured data for charting libraries"""
        
        top_strategy = ranked_strategies[0] if ranked_strategies else None
        
        return {
            'timestamp': datetime.now().isoformat(),
            'top_recommendation': top_strategy,
            'top_5': ranked_strategies[:5],
            'category_distribution': {
                'bullish': len([s for s in ranked_strategies[:10] if 'bullish' in s['strategy_type']]),
                'bearish': len([s for s in ranked_strategies[:10] if 'bearish' in s['strategy_type']]),
                'volatility_long': len([s for s in ranked_strategies[:10] if 'volatility_long' in s['strategy_type']]),
                'volatility_short': len([s for s in ranked_strategies[:10] if 'volatility_short' in s['strategy_type']]),
                'neutral': len([s for s in ranked_strategies[:10] if 'neutral' in s['strategy_type']])
            },
            'average_confidence': sum([s['confidence_score'] for s in ranked_strategies[:10]]) / 10,
            'market_regime_detected': 'calculated_from_flow'
        }

# ========================
# MAIN TRADING ENGINE
# ========================

class BTCOptionsTradingEngine:
    """Main engine combining all components"""
    
    def __init__(self):
        self.orderflow_analyzer = OrderFlowAnalyzer()
        self.strategy_scorer = StrategyScorer()
        self.visualizer = VisualStrategySelector()
        
    def analyze_and_select_strategy(self, 
                                   current_price: float,
                                   orderbook: OrderBookData,
                                   footprint: FootprintData,
                                   days_to_expiry: int = 2) -> Dict:
        """Complete analysis pipeline"""
        
        # Step 1: Analyze order flow
        whale_walls = self.orderflow_analyzer.detect_whale_walls(orderbook, current_price)
        imbalance = self.orderflow_analyzer.calculate_orderbook_imbalance(orderbook)
        footprint_analysis = self.orderflow_analyzer.analyze_footprint(footprint)
        
        # Step 2: Determine market regime
        regime = self.orderflow_analyzer.determine_market_regime(
            orderbook, footprint, current_price
        )
        
        # Step 3: Score all 30+ strategies
        ranked_strategies = self.strategy_scorer.rank_all_strategies(
            regime, imbalance, footprint_analysis, current_price, days_to_expiry
        )
        
        # Step 4: Generate visual data
        heatmap_data = self.visualizer.generate_heatmap_data(ranked_strategies)
        comparison_table = self.visualizer.generate_strategy_comparison_table(ranked_strategies)
        recommendation_chart = self.visualizer.generate_recommendation_chart(ranked_strategies)
        
        # Build complete response
        result = {
            'timestamp': datetime.now().isoformat(),
            'current_btc_price': current_price,
            'days_to_expiry': days_to_expiry,
            'market_regime': regime.value,
            'orderflow_summary': {
                'whale_walls_count': len(whale_walls),
                'top_whale_level': whale_walls[0] if whale_walls else None,
                'orderbook_imbalance': imbalance,
                'footprint_poc': footprint_analysis['poc'],
                'footprint_signals': footprint_analysis['signals']
            },
            'ranked_strategies': ranked_strategies,
            'top_recommendation': ranked_strategies[0] if ranked_strategies else None,
            'visual_data': {
                'heatmap': heatmap_data,
                'comparison_table': comparison_table,
                'chart_data': recommendation_chart
            },
            'execution_notes': [
                "Connect to exchange WebSocket for real-time orderbook",
                "Update footprint data every 100ms for live trading",
                "Recalculate regime every 5 seconds",
                "Execute top strategy when confidence > 0.75"
            ]
        }
        
        return result

# ========================
# EXAMPLE USAGE
# ========================

if __name__ == "__main__":
    # Initialize engine
    engine = BTCOptionsTradingEngine()
    
    # Mock current price
    current_price = 95000.0
    
    # Mock orderbook data (in production, fetch from exchange API)
    mock_orderbook = OrderBookData(
        bids=[(94950, 15.5), (94900, 8.2), (94850, 25.0), (94800, 12.3)],
        asks=[(95050, 18.2), (95100, 6.5), (95150, 22.8), (95200, 9.1)],
        whale_walls=[]
    )
    
    # Mock footprint data
    mock_footprint = FootprintData(
        price_levels=[94800, 94850, 94900, 94950, 95000, 95050, 95100, 95150],
        delta_volume=[-120, -80, 45, 230, 150, -90, -200, -150],
        imbalance_ratio=[0.6, 0.7, 1.2, 1.8, 1.4, 0.7, 0.5, 0.6],
        poc=94950,
        value_area_high=95100,
        value_area_low=94850
    )
    
    # Run analysis
    result = engine.analyze_and_select_strategy(
        current_price=current_price,
        orderbook=mock_orderbook,
        footprint=mock_footprint,
        days_to_expiry=2
    )
    
    # Output results
    print("\n" + "="*80)
    print("BTC OPTIONS STRATEGY ANALYSIS - ORDER FLOW BASED")
    print("="*80)
    print(f"Current Price: ${result['current_btc_price']:,.2f}")
    print(f"Market Regime: {result['market_regime']}")
    print(f"Days to Expiry: {result['days_to_expiry']}")
    print("\n" + result['visual_data']['comparison_table'])
    print("\n🎯 TOP RECOMMENDATION:")
    print(f"   Strategy: {result['top_recommendation']['strategy_name']}")
    print(f"   Confidence: {result['top_recommendation']['confidence_score']*100:.1f}%")
    print(f"   Probability of Profit: {result['top_recommendation']['probability_of_profit']*100:.1f}%")
    print(f"   Expected Value: {result['top_recommendation']['expected_value']:.2f}")
    print(f"   Reasoning: {result['top_recommendation']['reasoning']}")
    print("="*80 + "\n")
