#!/usr/bin/env python3
"""
Dashboard Server - Analytics Visualization
لوحة معلومات حية للإحصائيات والتحليلات

النسخة: 1.0.0
التقنية: FastAPI + Chart.js
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
import sys
from pathlib import Path

# إضافة modules للـ path
sys.path.append(str(Path(__file__).parent))

from modules import analytics

app = FastAPI(
    title="OTP Scanner - Dashboard",
    description="Real-time analytics and monitoring dashboard",
    version="1.0.0"
)

DB_PATH = "checked_urls.db"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API Endpoints (دوال بسيطة)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/stats/summary")
async def get_summary():
    """ملخص عام للإحصائيات"""
    try:
        return {
            "total_scans": analytics.get_total_scans(DB_PATH, days=7),
            "success_rate": round(analytics.get_success_rate(DB_PATH, days=7), 2),
            "avg_confidence": round(analytics.get_average_confidence(DB_PATH, days=7), 2)
        }
    except Exception as e:
        return {"error": str(e), "total_scans": 0, "success_rate": 0, "avg_confidence": 0}

@app.get("/api/stats/modes")
async def get_modes():
    """مقارنة الأوضاع (generator vs dorking)"""
    try:
        return analytics.get_mode_comparison(DB_PATH, days=7)
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/stats/methods")
async def get_methods():
    """مقارنة الطرق (httpx vs playwright)"""
    try:
        return analytics.get_method_comparison(DB_PATH, days=7)
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/stats/dorks/top")
async def get_top_dorks(limit: int = 10):
    """أفضل Dorks"""
    try:
        return analytics.get_top_dorks(DB_PATH, limit=limit)
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/stats/dorks/worst")
async def get_worst_dorks(limit: int = 5):
    """أسوأ Dorks"""
    try:
        return analytics.get_worst_dorks(DB_PATH, limit=limit)
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/stats/signatures")
async def get_signatures(limit: int = 10):
    """البصمات الأكثر اكتشافاً"""
    try:
        return analytics.get_top_signatures(DB_PATH, limit=limit, days=30)
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/stats/trend")
async def get_trend(days: int = 30):
    """الاتجاه اليومي"""
    try:
        return analytics.get_daily_trend(DB_PATH, days=days)
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/stats/api-usage")
async def get_api_usage():
    """استخدام API Keys"""
    try:
        return analytics.get_api_usage_summary(DB_PATH)
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/stats/insights")
async def get_insights():
    """توصيات ذكية"""
    try:
        return {"insights": analytics.generate_performance_insights(DB_PATH)}
    except Exception as e:
        return {"insights": [f"Error: {e}"]}

@app.get("/api/stats/report")
async def get_report(days: int = 7):
    """تقرير شامل"""
    try:
        return analytics.generate_summary_report(DB_PATH, days=days)
    except Exception as e:
        return {"error": str(e)}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الصفحة الرئيسية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OTP Scanner - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 48px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 10px 0;
        }
        
        .stat-change {
            font-size: 12px;
            color: #28a745;
        }
        
        .charts-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .chart-container {
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .insights-container {
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .insight-item {
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .refresh-info {
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-top: 20px;
            font-size: 12px;
        }
        
        canvas {
            max-height: 300px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🚀 OTP Scanner - Dashboard</h1>
            <p>Real-time Analytics & Monitoring | v3.1 (Phase 5)</p>
        </div>
        
        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Scans (7 days)</div>
                <div class="stat-value" id="total-scans">-</div>
                <div class="stat-change">Last updated: <span id="update-time">-</span></div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success Rate</div>
                <div class="stat-value" id="success-rate">-%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Confidence</div>
                <div class="stat-value" id="avg-conf">-%</div>
            </div>
        </div>
        
        <!-- Charts Row 1 -->
        <div class="charts-row">
            <div class="chart-container">
                <div class="chart-title">Generator vs Dorking</div>
                <canvas id="modesChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">HTTPX vs Playwright</div>
                <canvas id="methodsChart"></canvas>
            </div>
        </div>
        
        <!-- Charts Row 2 -->
        <div class="charts-row">
            <div class="chart-container">
                <div class="chart-title">Top Performing Dorks</div>
                <canvas id="dorksChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Top Signatures</div>
                <canvas id="signaturesChart"></canvas>
            </div>
        </div>
        
        <!-- Insights -->
        <div class="insights-container">
            <div class="chart-title">💡 AI-Powered Insights</div>
            <div id="insights-list"></div>
        </div>
        
        <div class="refresh-info">
            ⟳ Auto-refresh every 5 seconds
        </div>
    </div>
    
    <script>
        let charts = {};
        
        // تحديث الوقت
        function updateTime() {
            const now = new Date();
            document.getElementById('update-time').textContent = now.toLocaleTimeString('ar-EG');
        }
        
        // تحميل الإحصائيات العامة
        async function loadSummary() {
            try {
                const res = await fetch('/api/stats/summary');
                const data = await res.json();
                
                document.getElementById('total-scans').textContent = data.total_scans;
                document.getElementById('success-rate').textContent = data.success_rate.toFixed(1) + '%';
                document.getElementById('avg-conf').textContent = data.avg_confidence.toFixed(0) + '%';
                updateTime();
            } catch (e) {
                console.error('Error loading summary:', e);
            }
        }
        
        // رسم بياني للأوضاع
        async function loadModesChart() {
            try {
                const res = await fetch('/api/stats/modes');
                const data = await res.json();
                
                const ctx = document.getElementById('modesChart');
                
                if (charts.modes) charts.modes.destroy();
                
                charts.modes = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Generator', 'Dorking'],
                        datasets: [{
                            label: 'Success Rate (%)',
                            data: [data.generator.success_rate, data.dorking.success_rate],
                            backgroundColor: ['#667eea', '#764ba2']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            } catch (e) {
                console.error('Error loading modes chart:', e);
            }
        }
        
        // رسم بياني للطرق
        async function loadMethodsChart() {
            try {
                const res = await fetch('/api/stats/methods');
                const data = await res.json();
                
                const ctx = document.getElementById('methodsChart');
                
                if (charts.methods) charts.methods.destroy();
                
                charts.methods = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['HTTPX', 'Playwright'],
                        datasets: [{
                            data: [data.httpx?.avg_confidence || 0, data.playwright?.avg_confidence || 0],
                            backgroundColor: ['#28a745', '#ffc107']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true
                    }
                });
            } catch (e) {
                console.error('Error loading methods chart:', e);
            }
        }
        
        // رسم بياني للـ Dorks
        async function loadDorksChart() {
            try {
                const res = await fetch('/api/stats/dorks/top?limit=5');
                const data = await res.json();
                
                const ctx = document.getElementById('dorksChart');
                
                if (charts.dorks) charts.dorks.destroy();
                
                const labels = data.map(d => d.dork.substring(0, 30) + '...');
                const rates = data.map(d => d.success_rate);
                
                charts.dorks = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Success Rate (%)',
                            data: rates,
                            backgroundColor: '#667eea'
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: true
                    }
                });
            } catch (e) {
                console.error('Error loading dorks chart:', e);
            }
        }
        
        // رسم بياني للبصمات
        async function loadSignaturesChart() {
            try {
                const res = await fetch('/api/stats/signatures?limit=5');
                const data = await res.json();
                
                const ctx = document.getElementById('signaturesChart');
                
                if (charts.signatures) charts.signatures.destroy();
                
                const labels = data.map(d => d.signature);
                const counts = data.map(d => d.count);
                
                charts.signatures = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: counts,
                            backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true
                    }
                });
            } catch (e) {
                console.error('Error loading signatures chart:', e);
            }
        }
        
        // تحميل التوصيات
        async function loadInsights() {
            try {
                const res = await fetch('/api/stats/insights');
                const data = await res.json();
                
                const container = document.getElementById('insights-list');
                container.innerHTML = '';
                
                data.insights.forEach(insight => {
                    const div = document.createElement('div');
                    div.className = 'insight-item';
                    div.textContent = insight;
                    container.appendChild(div);
                });
            } catch (e) {
                console.error('Error loading insights:', e);
            }
        }
        
        // تحميل كل شيء
        async function loadAll() {
            await loadSummary();
            await loadModesChart();
            await loadMethodsChart();
            await loadDorksChart();
            await loadSignaturesChart();
            await loadInsights();
        }
        
        // تحميل أولي
        loadAll();
        
        // Auto-refresh كل 5 ثواني
        setInterval(loadAll, 5000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """لوحة المعلومات الرئيسية"""
    return HTML_TEMPLATE

@app.get("/health")
async def health():
    """فحص صحة السيرفر"""
    return {"status": "healthy", "version": "1.0.0"}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# التشغيل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import uvicorn
    
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Dashboard Server - Analytics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dashboard: http://127.0.0.1:8000
API Docs: http://127.0.0.1:8000/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
