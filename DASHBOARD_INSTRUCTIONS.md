# BTC Options Strategy Engine - Visual Dashboard

A complete HTML dashboard that connects to the API and displays real-time strategy rankings with visual heatmaps.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BTC Options Strategy Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status-bar {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 15px;
        }
        
        .status-item {
            background: rgba(255, 255, 255, 0.15);
            padding: 10px 20px;
            border-radius: 10px;
            min-width: 200px;
        }
        
        .status-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .status-value {
            font-size: 1.3em;
            font-weight: bold;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        
        .card h2 {
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 10px;
        }
        
        .strategy-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .strategy-table th,
        .strategy-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .strategy-table th {
            background: rgba(255, 255, 255, 0.15);
            font-weight: 600;
        }
        
        .strategy-table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .rank-badge {
            display: inline-block;
            width: 30px;
            height: 30px;
            line-height: 30px;
            text-align: center;
            border-radius: 50%;
            font-weight: bold;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .score-bar {
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #00f260 0%, #0575e6 100%);
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .confidence-high { color: #00f260; }
        .confidence-medium { color: #f5af19; }
        .confidence-low { color: #f5576c; }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
            margin: 20px auto;
            display: block;
        }
        
        .refresh-btn:hover {
            transform: scale(1.05);
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading-text {
            animation: pulse 1.5s infinite;
        }
        
        .regime-indicator {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.9em;
        }
        
        .regime-bullish { background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%); }
        .regime-bearish { background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); }
        .regime-range { background: linear-gradient(135deg, #f5af19 0%, #f12711 100%); }
        .regime-volatility { background: linear-gradient(135deg, #8e2de2 0%, #4a00e0 100%); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 BTC Options Strategy Engine</h1>
            <p>Real-time strategy selection from 30+ options using Order Flow Analysis</p>
            
            <div class="status-bar">
                <div class="status-item">
                    <div class="status-label">Current BTC Price</div>
                    <div class="status-value" id="btc-price">$--</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Market Regime</div>
                    <div class="status-value"><span class="regime-indicator regime-range" id="market-regime">--</span></div>
                </div>
                <div class="status-item">
                    <div class="status-label">Top Strategy Confidence</div>
                    <div class="status-value" id="top-confidence">--%</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Last Update</div>
                    <div class="status-value" id="last-update">--:--:--</div>
                </div>
            </div>
        </header>
        
        <div class="main-grid">
            <div class="card">
                <h2>📊 Top 5 Strategies</h2>
                <table class="strategy-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Strategy</th>
                            <th>Score</th>
                            <th>Prob%</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody id="strategy-table-body">
                        <tr><td colspan="5" class="loading loading-text">Loading strategies...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div class="card">
                <h2>🔥 Strategy Heatmap</h2>
                <div class="chart-container">
                    <canvas id="heatmap-chart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="card">
                <h2>📈 Expected Value Comparison</h2>
                <div class="chart-container">
                    <canvas id="ev-chart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h2>🎯 Top Recommendation Details</h2>
                <div id="top-recommendation">
                    <p class="loading loading-text">Analyzing market...</p>
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="fetchData()">🔄 Refresh Data</button>
    </div>
    
    <script>
        let heatmapChart = null;
        let evChart = null;
        
        // Color palette for charts
        const colors = [
            'rgba(255, 99, 132, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 206, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)',
            'rgba(199, 199, 199, 0.8)',
            'rgba(83, 102, 255, 0.8)',
            'rgba(255, 99, 255, 0.8)',
            'rgba(99, 255, 132, 0.8)'
        ];
        
        async function fetchData() {
            try {
                // Try to fetch from API, fallback to demo endpoint
                let response;
                try {
                    response = await fetch('http://localhost:5000/api/demo', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'}
                    });
                } catch (e) {
                    // If API not running, use mock data
                    updateWithMockData();
                    return;
                }
                
                const data = await response.json();
                updateDashboard(data);
                
            } catch (error) {
                console.error('Error fetching data:', error);
                document.getElementById('strategy-table-body').innerHTML = 
                    '<tr><td colspan="5" style="color: #ff6b6b;">Error loading data. Make sure API server is running.</td></tr>';
            }
        }
        
        function updateDashboard(data) {
            // Update status bar
            document.getElementById('btc-price').textContent = 
                `$${data.current_btc_price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            
            const regime = data.market_regime;
            const regimeEl = document.getElementById('market-regime');
            regimeEl.textContent = regime.replace(/_/g, ' ').toUpperCase();
            regimeEl.className = 'regime-indicator ' + getRegimeClass(regime);
            
            document.getElementById('top-confidence').textContent = 
                `${(data.top_recommendation.confidence_score * 100).toFixed(1)}%`;
            
            document.getElementById('last-update').textContent = 
                new Date().toLocaleTimeString();
            
            // Update strategy table
            updateStrategyTable(data.ranked_strategies.slice(0, 5));
            
            // Update charts
            updateHeatmapChart(data.visual_data.heatmap);
            updateEVChart(data.ranked_strategies.slice(0, 10));
            
            // Update top recommendation details
            updateTopRecommendation(data.top_recommendation);
        }
        
        function updateStrategyTable(strategies) {
            const tbody = document.getElementById('strategy-table-body');
            tbody.innerHTML = '';
            
            strategies.forEach((strat, index) => {
                const confidenceClass = strat.confidence_score >= 0.7 ? 'confidence-high' :
                                       strat.confidence_score >= 0.5 ? 'confidence-medium' : 'confidence-low';
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><span class="rank-badge">${index + 1}</span></td>
                    <td><strong>${strat.strategy_name}</strong></td>
                    <td>
                        <div>${strat.total_score.toFixed(1)}</div>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${strat.total_score}%"></div>
                        </div>
                    </td>
                    <td class="${confidenceClass}">${(strat.probability_of_profit * 100).toFixed(1)}%</td>
                    <td>${strat.strategy_type.replace(/_/g, ' ')}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function updateHeatmapChart(heatmapData) {
            const ctx = document.getElementById('heatmap-chart').getContext('2d');
            
            if (heatmapChart) {
                heatmapChart.destroy();
            }
            
            heatmapChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: heatmapData.labels,
                    datasets: [{
                        label: 'Strategy Score',
                        data: heatmapData.scores,
                        backgroundColor: colors.slice(0, heatmapData.labels.length),
                        borderColor: colors.map(c => c.replace('0.8', '1')).slice(0, heatmapData.labels.length),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: '#fff' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#fff', maxRotation: 45, minRotation: 45 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
        
        function updateEVChart(strategies) {
            const ctx = document.getElementById('ev-chart').getContext('2d');
            
            if (evChart) {
                evChart.destroy();
            }
            
            evChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: strategies.map(s => s.strategy_name.substring(0, 15) + (s.strategy_name.length > 15 ? '...' : '')),
                    datasets: [{
                        label: 'Expected Value',
                        data: strategies.map(s => s.expected_value),
                        backgroundColor: strategies.map(s => s.expected_value > 0 ? 'rgba(0, 242, 96, 0.8)' : 'rgba(245, 87, 108, 0.8)'),
                        borderColor: strategies.map(s => s.expected_value > 0 ? 'rgba(0, 242, 96, 1)' : 'rgba(245, 87, 108, 1)'),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: '#fff' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#fff', maxRotation: 45, minRotation: 45 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
        
        function updateTopRecommendation(strategy) {
            const container = document.getElementById('top-recommendation');
            container.innerHTML = `
                <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-bottom: 15px;">
                    <h3 style="margin-bottom: 10px; color: #00f260;">${strategy.strategy_name}</h3>
                    <p><strong>Type:</strong> ${strategy.strategy_type.replace(/_/g, ' ')}</p>
                    <p><strong>Risk/Reward:</strong> ${strategy.risk_profile}</p>
                    <p><strong>Volatility View:</strong> ${strategy.volatility_view}</p>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">Probability of Profit</div>
                        <div style="font-size: 1.8em; font-weight: bold; color: #00f260;">
                            ${(strategy.probability_of_profit * 100).toFixed(1)}%
                        </div>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">Expected Value</div>
                        <div style="font-size: 1.8em; font-weight: bold; color: #54a0ff;">
                            ${strategy.expected_value.toFixed(2)}
                        </div>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                    <h4 style="margin-bottom: 10px;">Reasoning:</h4>
                    <p style="line-height: 1.6;">${strategy.reasoning}</p>
                </div>
            `;
        }
        
        function getRegimeClass(regime) {
            if (regime.includes('bullish') || regime.includes('momentum_up')) return 'regime-bullish';
            if (regime.includes('bearish') || regime.includes('momentum_down')) return 'regime-bearish';
            if (regime.includes('volatility') || regime.includes('expansion')) return 'regime-volatility';
            return 'regime-range';
        }
        
        function updateWithMockData() {
            // Mock data for when API is not available
            const mockData = {
                current_btc_price: 95000 + Math.random() * 2000 - 1000,
                market_regime: ['bullish_breakout', 'bearish_breakdown', 'range_low_vol'][Math.floor(Math.random() * 3)],
                top_recommendation: {
                    strategy_name: 'Long Straddle',
                    strategy_type: 'volatility_long',
                    risk_profile: 'limited risk / unlimited reward',
                    volatility_view: 'expansion',
                    probability_of_profit: 0.70,
                    expected_value: 1.80,
                    confidence_score: 0.70,
                    reasoning: 'High delta imbalance detected in footprint. Volatility expansion expected based on order flow analysis.'
                },
                ranked_strategies: [
                    {strategy_name: 'Long Straddle', total_score: 85, probability_of_profit: 0.70, expected_value: 1.80, confidence_score: 0.85, strategy_type: 'volatility_long', risk_profile: 'limited/unlimited'},
                    {strategy_name: 'Bull Call Spread', total_score: 78, probability_of_profit: 0.65, expected_value: 1.45, confidence_score: 0.78, strategy_type: 'bullish', risk_profile: 'limited/limited'},
                    {strategy_name: 'Long Call', total_score: 72, probability_of_profit: 0.60, expected_value: 1.60, confidence_score: 0.72, strategy_type: 'bullish', risk_profile: 'limited/unlimited'},
                    {strategy_name: 'Iron Condor', total_score: 65, probability_of_profit: 0.75, expected_value: 0.95, confidence_score: 0.65, strategy_type: 'volatility_short', risk_profile: 'limited/limited'},
                    {strategy_name: 'Calendar Spread', total_score: 60, probability_of_profit: 0.68, expected_value: 0.88, confidence_score: 0.60, strategy_type: 'neutral_time', risk_profile: 'limited/limited'}
                ],
                visual_data: {
                    heatmap: {
                        labels: ['Long Straddle', 'Bull Call Spread', 'Long Call', 'Iron Condor', 'Calendar'],
                        scores: [85, 78, 72, 65, 60]
                    }
                }
            };
            
            updateDashboard(mockData);
        }
        
        // Initial load
        fetchData();
        
        // Auto-refresh every 10 seconds
        setInterval(fetchData, 10000);
    </script>
</body>
</html>
```

Save this as `dashboard.html` and open it in your browser. It will automatically connect to the API server at `http://localhost:5000` or display mock data if the server isn't running.

## Features:
- **Live Strategy Rankings** - Shows top 5 strategies with scores
- **Visual Heatmap** - Bar chart of strategy scores
- **Expected Value Chart** - Compares profitability across strategies  
- **Top Recommendation Details** - Full breakdown of best strategy
- **Auto-refresh** - Updates every 10 seconds
- **Responsive Design** - Works on desktop and mobile
- **Beautiful UI** - Modern glassmorphism design with gradients
