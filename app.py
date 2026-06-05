from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Tuple, Optional
import json
from scipy.stats import norm

app = Flask(__name__)

class BTCOptionsStrategy:
    """
    Automatic BTC Out-of-Money Options Trading Strategy
    Analyzes expiry, liquidity, and heatmap data for 2-3 day options
    """
    
    def __init__(self):
        self.btc_price = None
        self.options_chain = None
        self.liquidity_data = None
        self.heatmap_data = None
        self.supported_exchanges = ['deribit', 'binance', 'bybit', 'okx']
        
    def fetch_btc_price(self) -> float:
        """Fetch current BTC spot price"""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
                timeout=10
            )
            data = response.json()
            self.btc_price = data['bitcoin']['usd']
            return self.btc_price
        except Exception as e:
            print(f"Error fetching BTC price: {e}")
            return None
    
    def get_next_expiry_dates(self, days_ahead: int = 2) -> List[datetime]:
        """Get next expiry dates for options (typically Friday for weekly options)"""
        today = datetime.now()
        expiry_dates = []
        
        # Find next 2-3 expiry dates
        for i in range(1, 30):
            future_date = today + timedelta(days=i)
            # Weekly options typically expire on Friday
            if future_date.weekday() == 4:  # Friday
                expiry_dates.append(future_date)
                if len(expiry_dates) >= 3:
                    break
        
        return expiry_dates[:days_ahead]
    
    def calculate_otm_strikes(self, strike_distance: float = 0.05) -> Dict[str, List[float]]:
        """
        Calculate Out-of-The-Money strike prices
        strike_distance: percentage away from current price (default 5%)
        """
        if not self.btc_price:
            self.fetch_btc_price()
        
        if not self.btc_price:
            return {'calls': [], 'puts': []}
        
        # Common strike intervals for BTC options
        strike_interval = self._get_strike_interval(self.btc_price)
        
        # OTM Calls: strikes above current price
        otm_calls = []
        strike = self.btc_price + strike_interval
        while strike <= self.btc_price * (1 + strike_distance * 2):
            otm_calls.append(round(strike / strike_interval) * strike_interval)
            strike += strike_interval
        
        # OTM Puts: strikes below current price
        otm_puts = []
        strike = self.btc_price - strike_interval
        while strike >= self.btc_price * (1 - strike_distance * 2):
            otm_puts.append(round(strike / strike_interval) * strike_interval)
            strike -= strike_interval
        
        return {'calls': otm_calls, 'puts': otm_puts}
    
    def _get_strike_interval(self, price: float) -> float:
        """Determine appropriate strike interval based on BTC price"""
        if price < 10000:
            return 100
        elif price < 30000:
            return 250
        elif price < 50000:
            return 500
        elif price < 70000:
            return 1000
        else:
            return 2000
    
    def analyze_liquidity(self, exchange: str = 'deribit') -> Dict:
        """
        Analyze options liquidity metrics
        Returns volume, open interest, and bid-ask spreads
        """
        # Mock liquidity analysis - in production, connect to exchange API
        liquidity_metrics = {
            'exchange': exchange,
            'timestamp': datetime.now().isoformat(),
            'total_volume_24h': 0,
            'total_open_interest': 0,
            'avg_bid_ask_spread': 0,
            'liquidity_score': 0,
            'top_liquid_strikes': []
        }
        
        try:
            # Example: Deribit API for options data
            if exchange == 'deribit':
                response = requests.get(
                    'https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option&expired=false',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    instruments = data.get('result', [])
                    
                    # Process liquidity data
                    volumes = []
                    open_interests = []
                    
                    for instrument in instruments:
                        instrument_name = instrument.get('instrument_name', '')
                        # Filter for 2-3 day expiries
                        if self._is_near_term_expiry(instrument_name):
                            volumes.append(instrument.get('volume', 0))
                            open_interests.append(instrument.get('open_interest', 0))
                    
                    if volumes:
                        liquidity_metrics['total_volume_24h'] = sum(volumes)
                        liquidity_metrics['total_open_interest'] = sum(open_interests)
                        liquidity_metrics['avg_bid_ask_spread'] = np.mean([
                            instrument.get('bid_iv', 0) - instrument.get('mark_iv', 0)
                            for instrument in instruments
                        ]) if instruments else 0
                        
                        # Calculate liquidity score (0-100)
                        volume_score = min(100, liquidity_metrics['total_volume_24h'] / 1000)
                        oi_score = min(100, liquidity_metrics['total_open_interest'] / 5000)
                        liquidity_metrics['liquidity_score'] = (volume_score + oi_score) / 2
                        
        except Exception as e:
            print(f"Error analyzing liquidity: {e}")
        
        return liquidity_metrics
    
    def _is_near_term_expiry(self, instrument_name: str) -> bool:
        """Check if option expires in 2-3 days"""
        try:
            # Deribit format: BTC-DDMMMYY-STRIKE-C/P
            parts = instrument_name.split('-')
            if len(parts) >= 2:
                date_str = parts[1]
                expiry_date = datetime.strptime(date_str, '%d%b%y')
                days_to_expiry = (expiry_date - datetime.now()).days
                return 1 <= days_to_expiry <= 3
        except:
            pass
        return False
    
    def generate_heatmap(self, strikes: List[float], expiry: datetime) -> Dict:
        """
        Generate probability heatmap for BTC price movements
        Uses implied volatility to calculate probability distribution
        """
        if not self.btc_price:
            self.fetch_btc_price()
        
        # Typical BTC implied volatility (can be fetched from options data)
        iv = 0.65  # 65% annualized volatility
        
        # Time to expiry in years
        tte = (expiry - datetime.now()).total_seconds() / (365 * 24 * 3600)
        
        # Calculate standard deviation for log-normal distribution
        std_dev = self.btc_price * iv * np.sqrt(tte)
        
        heatmap_data = {
            'current_price': self.btc_price,
            'expiry_date': expiry.isoformat(),
            'days_to_expiry': (expiry - datetime.now()).days,
            'implied_volatility': iv,
            'probability_distribution': [],
            'support_levels': [],
            'resistance_levels': [],
            'max_pain': 0
        }
        
        # Generate probability for each strike
        probabilities = []
        for strike in strikes:
            # Calculate probability of finishing ITM using Black-Scholes approximation
            d1 = (np.log(self.btc_price / strike) + (iv**2 / 2) * tte) / (iv * np.sqrt(tte))
            d2 = d1 - iv * np.sqrt(tte)
            
            # Probability of call finishing ITM
            prob_call_itm = self._norm_cdf(d2)
            # Probability of put finishing ITM
            prob_put_itm = self._norm_cdf(-d2)
            
            probabilities.append({
                'strike': strike,
                'prob_call_itm': prob_call_itm,
                'prob_put_itm': prob_put_itm,
                'expected_value': self.btc_price * prob_call_itm - strike * prob_put_itm
            })
        
        heatmap_data['probability_distribution'] = probabilities
        
        # Identify support and resistance levels
        sorted_probs = sorted(probabilities, key=lambda x: x['prob_call_itm'], reverse=True)
        heatmap_data['resistance_levels'] = [p['strike'] for p in sorted_probs[:3]]
        heatmap_data['support_levels'] = [p['strike'] for p in sorted_probs[-3:]]
        
        # Calculate max pain (strike with maximum open interest pain)
        if probabilities:
            heatmap_data['max_pain'] = np.median([p['strike'] for p in probabilities])
        
        return heatmap_data
    
    def _norm_cdf(self, x: float) -> float:
        """Standard normal cumulative distribution function"""
        return norm.cdf(x)
    
    def generate_trading_signals(self) -> Dict:
        """
        Generate trading signals based on all analyzed data
        Returns recommended OTM options for 2-3 day trades
        """
        if not self.btc_price:
            self.fetch_btc_price()
        
        expiry_dates = self.get_next_expiry_dates(2)
        otm_strikes = self.calculate_otm_strikes(0.03)  # 3% OTM
        liquidity = self.analyze_liquidity()
        
        signals = {
            'timestamp': datetime.now().isoformat(),
            'btc_current_price': self.btc_price,
            'market_sentiment': 'neutral',
            'recommended_trades': [],
            'risk_metrics': {
                'max_loss_per_trade': 0,
                'position_sizing': 0,
                'stop_loss_levels': []
            },
            'confidence_score': 0
        }
        
        # Analyze each expiry date
        for expiry in expiry_dates:
            heatmap = self.generate_heatmap(otm_strikes['calls'] + otm_strikes['puts'], expiry)
            
            # Generate trade recommendations
            for strike in otm_strikes['calls'][:3]:  # Top 3 OTM calls
                prob_data = next((p for p in heatmap['probability_distribution'] 
                                if abs(p['strike'] - strike) < 100), None)
                if prob_data:
                    signals['recommended_trades'].append({
                        'type': 'BUY_OTM_CALL',
                        'strike': strike,
                        'expiry': expiry.strftime('%Y-%m-%d'),
                        'days_to_expiry': (expiry - datetime.now()).days,
                        'probability_profit': 1 - prob_data['prob_call_itm'],
                        'risk_reward_ratio': 3.0,
                        'entry_zone': f"${strike - 500:.0f} - ${strike + 500:.0f}",
                        'target_exit': f"${strike * 1.5:.0f}",
                        'stop_loss': f"${strike * 0.3:.0f}"
                    })
            
            for strike in otm_strikes['puts'][:3]:  # Top 3 OTM puts
                prob_data = next((p for p in heatmap['probability_distribution'] 
                                if abs(p['strike'] - strike) < 100), None)
                if prob_data:
                    signals['recommended_trades'].append({
                        'type': 'BUY_OTM_PUT',
                        'strike': strike,
                        'expiry': expiry.strftime('%Y-%m-%d'),
                        'days_to_expiry': (expiry - datetime.now()).days,
                        'probability_profit': 1 - prob_data['prob_put_itm'],
                        'risk_reward_ratio': 3.0,
                        'entry_zone': f"${strike - 500:.0f} - ${strike + 500:.0f}",
                        'target_exit': f"${strike * 1.5:.0f}",
                        'stop_loss': f"${strike * 0.3:.0f}"
                    })
        
        # Calculate overall confidence score
        if signals['recommended_trades']:
            avg_prob = np.mean([t['probability_profit'] for t in signals['recommended_trades']])
            signals['confidence_score'] = min(100, avg_prob * 100 + liquidity['liquidity_score'] * 0.3)
        
        # Risk management
        if self.btc_price:
            signals['risk_metrics']['max_loss_per_trade'] = self.btc_price * 0.02  # 2% of portfolio
            signals['risk_metrics']['position_sizing'] = self.btc_price * 0.01  # 1% per trade
            signals['risk_metrics']['stop_loss_levels'] = [
                self.btc_price * 0.95,  # 5% below
                self.btc_price * 1.05   # 5% above
            ]
        
        return signals
    
    def get_full_analysis(self) -> Dict:
        """Comprehensive analysis combining all metrics"""
        return {
            'market_overview': {
                'btc_price': self.fetch_btc_price(),
                'timestamp': datetime.now().isoformat(),
                'market_status': 'active'
            },
            'expiry_analysis': {
                'next_expiries': [d.strftime('%Y-%m-%d') for d in self.get_next_expiry_dates(3)],
                'days_to_next_expiry': (self.get_next_expiry_dates(1)[0] - datetime.now()).days
            },
            'liquidity_analysis': self.analyze_liquidity(),
            'heatmap_data': self.generate_heatmap(
                self.calculate_otm_strikes()['calls'] + self.calculate_otm_strikes()['puts'],
                self.get_next_expiry_dates(1)[0]
            ),
            'trading_signals': self.generate_trading_signals(),
            'strategy_summary': {
                'approach': 'OTM Options Selling/Buying',
                'timeframe': '2-3 days',
                'risk_level': 'High',
                'recommended_capital_allocation': '5-10% of portfolio',
                'key_metrics': ['Implied Volatility', 'Open Interest', 'Volume', 'Gamma Exposure']
            }
        }


# Initialize strategy engine
strategy_engine = BTCOptionsStrategy()


@app.route('/api/analysis', methods=['GET'])
def get_full_analysis():
    """Endpoint to get complete BTC options analysis"""
    try:
        analysis = strategy_engine.get_full_analysis()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals', methods=['GET'])
def get_trading_signals():
    """Endpoint to get trading signals only"""
    try:
        signals = strategy_engine.generate_trading_signals()
        return jsonify(signals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """Endpoint to get probability heatmap data"""
    try:
        expiry_dates = strategy_engine.get_next_expiry_dates(1)
        otm_strikes = strategy_engine.calculate_otm_strikes()
        all_strikes = otm_strikes['calls'] + otm_strikes['puts']
        heatmap = strategy_engine.generate_heatmap(all_strikes, expiry_dates[0])
        return jsonify(heatmap)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/liquidity', methods=['GET'])
def get_liquidity():
    """Endpoint to get liquidity analysis"""
    try:
        exchange = request.args.get('exchange', 'deribit')
        liquidity = strategy_engine.analyze_liquidity(exchange)
        return jsonify(liquidity)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/expiry', methods=['GET'])
def get_expiry_dates():
    """Endpoint to get next expiry dates"""
    try:
        days = int(request.args.get('days', 2))
        expiries = strategy_engine.get_next_expiry_dates(days)
        return jsonify({
            'expiry_dates': [e.strftime('%Y-%m-%d') for e in expiries],
            'current_date': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for external integrations"""
    data = request.json
    print("Received webhook data:", data)
    
    # Process webhook and trigger analysis if needed
    if data.get('trigger_analysis'):
        analysis = strategy_engine.get_full_analysis()
        return jsonify({
            "message": "Webhook received and analysis triggered",
            "data": data,
            "analysis": analysis
        })
    
    return jsonify({"message": "Webhook received", "data": data})


if __name__ == '__main__':
    # Run initial analysis
    print("Initializing BTC Options Strategy Engine...")
    initial_analysis = strategy_engine.get_full_analysis()
    print(json.dumps(initial_analysis, indent=2))
    
    app.run(host='0.0.0.0', port=10000)
