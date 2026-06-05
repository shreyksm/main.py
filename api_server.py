"""
Flask API for BTC Options Strategy Engine
Provides REST endpoints with visual data for 30+ strategies
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from btc_options_engine import (
    BTCOptionsTradingEngine, 
    OrderBookData, 
    FootprintData,
    MarketRegime
)
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# Initialize engine
engine = BTCOptionsTradingEngine()

# Store latest analysis
latest_analysis = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'BTC Options Strategy Engine'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    """
    Main analysis endpoint
    Accepts orderbook and footprint data, returns ranked strategies
    """
    global latest_analysis
    
    data = request.get_json()
    
    # Extract parameters
    current_price = data.get('price', 95000.0)
    days_to_expiry = data.get('days_to_expiry', 2)
    
    # Parse orderbook
    bids = [(float(p), float(s)) for p, s in data.get('bids', [])]
    asks = [(float(p), float(s)) for p, s in data.get('asks', [])]
    
    # Parse footprint
    price_levels = [float(p) for p in data.get('price_levels', [])]
    delta_volume = [float(d) for d in data.get('delta_volume', [])]
    imbalance_ratio = [float(i) for i in data.get('imbalance_ratio', [])]
    poc = float(data.get('poc', current_price))
    va_high = float(data.get('value_area_high', current_price * 1.01))
    va_low = float(data.get('value_area_low', current_price * 0.99))
    
    # Create data objects
    orderbook = OrderBookData(bids=bids, asks=asks, whale_walls=[])
    footprint = FootprintData(
        price_levels=price_levels,
        delta_volume=delta_volume,
        imbalance_ratio=imbalance_ratio,
        poc=poc,
        value_area_high=va_high,
        value_area_low=va_low
    )
    
    # Run analysis
    result = engine.analyze_and_select_strategy(
        current_price=current_price,
        orderbook=orderbook,
        footprint=footprint,
        days_to_expiry=days_to_expiry
    )
    
    latest_analysis = result
    
    return jsonify(result)

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get latest trading signals with top 5 strategies"""
    if not latest_analysis:
        # Generate demo data if no analysis yet
        return jsonify(generate_demo_analysis())
    
    return jsonify({
        'timestamp': latest_analysis['timestamp'],
        'market_regime': latest_analysis['market_regime'],
        'current_price': latest_analysis['current_btc_price'],
        'top_5_strategies': latest_analysis['ranked_strategies'][:5],
        'top_recommendation': latest_analysis['top_recommendation']
    })

@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """Get visual heatmap data for strategy scores"""
    if not latest_analysis:
        demo = generate_demo_analysis()
        return jsonify(demo['visual_data']['heatmap'])
    
    return jsonify(latest_analysis['visual_data']['heatmap'])

@app.route('/api/strategy/<int:rank>', methods=['GET'])
def get_strategy_by_rank(rank):
    """Get detailed info for strategy at specific rank"""
    if not latest_analysis:
        generate_demo_analysis()
    
    if rank < 1 or rank > len(latest_analysis['ranked_strategies']):
        return jsonify({'error': 'Invalid rank'}), 400
    
    strategy = latest_analysis['ranked_strategies'][rank - 1]
    return jsonify({
        'rank': rank,
        'strategy': strategy,
        'market_context': {
            'regime': latest_analysis['market_regime'],
            'price': latest_analysis['current_btc_price'],
            'whale_levels': latest_analysis['orderflow_summary']['whale_walls_count']
        }
    })

@app.route('/api/orderbook-heatmap', methods=['GET'])
def get_orderbook_heatmap():
    """Get orderbook liquidity heatmap data"""
    if not latest_analysis:
        demo = generate_demo_analysis()
        return jsonify(demo['orderflow_summary']['orderbook_imbalance'])
    
    return jsonify(latest_analysis['orderflow_summary']['orderbook_imbalance'])

@app.route('/api/whale-alerts', methods=['GET'])
def get_whale_alerts():
    """Get detected whale walls"""
    if not latest_analysis:
        demo = generate_demo_analysis()
        return jsonify({
            'whale_count': demo['orderflow_summary']['whale_walls_count'],
            'top_whale': demo['orderflow_summary']['top_whale_level']
        })
    
    return jsonify({
        'whale_count': latest_analysis['orderflow_summary']['whale_walls_count'],
        'top_whale': latest_analysis['orderflow_summary']['top_whale_level']
    })

@app.route('/api/regime', methods=['GET'])
def get_market_regime():
    """Get current detected market regime"""
    if not latest_analysis:
        demo = generate_demo_analysis()
        return jsonify({'regime': demo['market_regime']})
    
    return jsonify({
        'regime': latest_analysis['market_regime'],
        'confidence': latest_analysis['top_recommendation']['confidence_score'],
        'reasoning': latest_analysis['top_recommendation']['reasoning']
    })

@app.route('/api/visual-dashboard', methods=['GET'])
def get_visual_dashboard():
    """Complete visual dashboard data"""
    if not latest_analysis:
        return jsonify(generate_demo_analysis()['visual_data']['chart_data'])
    
    return jsonify(latest_analysis['visual_data']['chart_data'])

@app.route('/api/demo', methods=['POST'])
def run_demo():
    """Run demo analysis with simulated data"""
    demo_result = generate_demo_analysis()
    global latest_analysis
    latest_analysis = demo_result
    return jsonify(demo_result)

def generate_demo_analysis():
    """Generate realistic demo data for testing"""
    
    # Simulate different market scenarios
    scenarios = [
        {'name': 'bullish_momentum', 'imbalance': 2.5, 'delta_bias': 'positive'},
        {'name': 'bearish_breakdown', 'imbalance': 0.4, 'delta_bias': 'negative'},
        {'name': 'range_consolidation', 'imbalance': 1.1, 'delta_bias': 'mixed'},
    ]
    
    scenario = random.choice(scenarios)
    base_price = 95000 + random.uniform(-2000, 2000)
    
    # Generate mock orderbook based on scenario
    if scenario['imbalance'] > 1.5:
        bids = [(base_price - 50*i, random.uniform(10, 30)) for i in range(1, 6)]
        asks = [(base_price + 50*i, random.uniform(3, 8)) for i in range(1, 6)]
    elif scenario['imbalance'] < 0.7:
        bids = [(base_price - 50*i, random.uniform(3, 8)) for i in range(1, 6)]
        asks = [(base_price + 50*i, random.uniform(10, 30)) for i in range(1, 6)]
    else:
        bids = [(base_price - 50*i, random.uniform(8, 15)) for i in range(1, 6)]
        asks = [(base_price + 50*i, random.uniform(8, 15)) for i in range(1, 6)]
    
    # Generate mock footprint
    price_levels = [base_price - 150 + 50*i for i in range(7)]
    if scenario['delta_bias'] == 'positive':
        delta_volume = [random.uniform(-50, 100) for _ in range(7)]
        delta_volume[3] = random.uniform(200, 400)  # Strong buy at POC
    elif scenario['delta_bias'] == 'negative':
        delta_volume = [random.uniform(-100, 50) for _ in range(7)]
        delta_volume[3] = random.uniform(-400, -200)  # Strong sell at POC
    else:
        delta_volume = [random.uniform(-150, 150) for _ in range(7)]
    
    orderbook = OrderBookData(bids=bids, asks=asks, whale_walls=[])
    footprint = FootprintData(
        price_levels=price_levels,
        delta_volume=delta_volume,
        imbalance_ratio=[random.uniform(0.5, 2.0) for _ in range(7)],
        poc=base_price,
        value_area_high=base_price * 1.015,
        value_area_low=base_price * 0.985
    )
    
    result = engine.analyze_and_select_strategy(
        current_price=base_price,
        orderbook=orderbook,
        footprint=footprint,
        days_to_expiry=2
    )
    
    return result

if __name__ == '__main__':
    print("🚀 Starting BTC Options Strategy API Server...")
    print("📊 Endpoints available:")
    print("   GET  /api/health - Health check")
    print("   POST /api/analyze - Full analysis with orderbook/footprint data")
    print("   GET  /api/signals - Top 5 strategy signals")
    print("   GET  /api/heatmap - Visual heatmap data")
    print("   GET  /api/strategy/<rank> - Specific strategy details")
    print("   GET  /api/orderbook-heatmap - Orderbook imbalance")
    print("   GET  /api/whale-alerts - Whale wall detections")
    print("   GET  /api/regime - Market regime detection")
    print("   GET  /api/visual-dashboard - Complete dashboard data")
    print("   POST /api/demo - Run demo analysis")
    print("\n🌐 Server running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
