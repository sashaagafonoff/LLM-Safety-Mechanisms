import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path
import numpy as np

class DashboardGenerator:
    def __init__(self):
        self.load_data()
        self.output_dir = Path('docs')
        self.output_dir.mkdir(exist_ok=True)
    
    def load_data(self):
        """Load all data files"""
        with open('data/providers.json', 'r') as f:
            self.providers = {p['id']: p for p in json.load(f)}
        
        with open('data/techniques.json', 'r') as f:
            self.techniques = {t['id']: t for t in json.load(f)}
        
        with open('data/categories.json', 'r') as f:
            self.categories = {c['id']: c for c in json.load(f)}
        
        with open('data/evidence.json', 'r') as f:
            self.evidence = json.load(f)
        
        with open('data/risk_areas.json', 'r') as f:
            self.risk_areas = {r['id']: r for r in json.load(f)}
    
    def create_coverage_heatmap(self):
        """Create provider-technique coverage heatmap"""
        # Build matrix
        provider_ids = ['openai', 'anthropic', 'google', 'meta', 'amazon']
        technique_ids = sorted(set(e['techniqueId'] for e in self.evidence))
        
        # Create rating matrix
        matrix = []
        technique_names = []
        
        for tech_id in technique_ids:
            if tech_id not in self.techniques:
                continue
                
            technique_names.append(self.techniques[tech_id]['name'])
            row = []
            
            for prov_id in provider_ids:
                evidence = [e for e in self.evidence 
                          if e['providerId'] == prov_id and e['techniqueId'] == tech_id]
                
                if evidence:
                    rating = evidence[0]['rating']
                    if rating == 'high':
                        row.append(3)
                    elif rating == 'medium':
                        row.append(2)
                    elif rating == 'low':
                        row.append(1)
                    else:
                        row.append(0.5)
                else:
                    row.append(0)
            
            matrix.append(row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=[self.providers[p]['name'] for p in provider_ids],
            y=technique_names,
            colorscale=[
                [0, '#f0f0f0'],      # No implementation
                [0.17, '#ffd700'],   # Other (0.5)
                [0.33, '#ff6b6b'],   # Low (1)
                [0.67, '#ffd93d'],   # Medium (2)
                [1.0, '#4ecdc4']     # High (3)
            ],
            text=[[self._get_rating_text(val) for val in row] for row in matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="Provider: %{x}<br>Technique: %{y}<br>Rating: %{text}<extra></extra>"
        ))
        
        fig.update_layout(
            title="LLM Safety Mechanism Coverage by Provider",
            xaxis_title="Provider",
            yaxis_title="Safety Technique",
            height=800,
            width=1000,
            yaxis=dict(tickmode='linear'),
            xaxis=dict(side='top')
        )
        
        return fig
    
    def _get_rating_text(self, value):
        """Convert numeric rating to text"""
        if value == 0:
            return "—"
        elif value == 0.5:
            return "?"
        elif value == 1:
            return "Low"
        elif value == 2:
            return "Med"
        elif value == 3:
            return "High"
        return str(value)
    
    def create_timeline_chart(self):
        """Create implementation timeline"""
        # Prepare timeline data
        timeline_data = []
        
        for e in self.evidence:
            if e.get('implementationDate'):
                timeline_data.append({
                    'Date': e['implementationDate'],
                    'Provider': self.providers[e['providerId']]['name'],
                    'Technique': self.techniques[e['techniqueId']]['name'],
                    'Rating': e['rating'].title()
                })
        
        if not timeline_data:
            return None
        
        df = pd.DataFrame(timeline_data)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Create timeline
        fig = px.scatter(df, x='Date', y='Provider', color='Rating',
                        hover_data=['Technique'],
                        title='Safety Implementation Timeline',
                        color_discrete_map={
                            'High': '#4ecdc4',
                            'Medium': '#ffd93d', 
                            'Low': '#ff6b6b'
                        })
        
        fig.update_traces(marker=dict(size=12))
        fig.update_layout(
            height=400,
            xaxis_title="Implementation Date",
            yaxis_title="Provider"
        )
        
        return fig
    
    def create_rating_distribution(self):
        """Create rating distribution chart"""
        # Count ratings by provider
        rating_counts = {}
        
        for provider_id in self.providers:
            counts = {'high': 0, 'medium': 0, 'low': 0, 'other': 0}
            
            for e in self.evidence:
                if e['providerId'] == provider_id:
                    rating = e['rating']
                    if rating in counts:
                        counts[rating] += 1
                    else:
                        counts['other'] += 1
            
            if sum(counts.values()) > 0:
                rating_counts[self.providers[provider_id]['name']] = counts
        
        # Create stacked bar chart
        providers = list(rating_counts.keys())
        high_counts = [rating_counts[p]['high'] for p in providers]
        medium_counts = [rating_counts[p]['medium'] for p in providers]
        low_counts = [rating_counts[p]['low'] for p in providers]
        
        fig = go.Figure(data=[
            go.Bar(name='High', x=providers, y=high_counts, marker_color='#4ecdc4'),
            go.Bar(name='Medium', x=providers, y=medium_counts, marker_color='#ffd93d'),
            go.Bar(name='Low', x=providers, y=low_counts, marker_color='#ff6b6b')
        ])
        
        fig.update_layout(
            barmode='stack',
            title='Implementation Rating Distribution by Provider',
            xaxis_title='Provider',
            yaxis_title='Number of Techniques',
            height=400
        )
        
        return fig
    
    def create_evidence_quality_chart(self):
        """Create evidence quality distribution"""
        quality_map = {'P': 'Primary', 'B': 'Benchmarked', 'C': 'Claimed', 'V': 'Volunteered', 'U': 'Unverified'}
        
        quality_counts = {}
        for e in self.evidence:
            band = e.get('severityBand', 'U')
            quality = quality_map.get(band, 'Unknown')
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(quality_counts.keys()),
            values=list(quality_counts.values()),
            hole=.3,
            marker_colors=['#4ecdc4', '#6c5ce7', '#ffd93d', '#ff6b6b', '#dfe6e9']
        )])
        
        fig.update_layout(
            title='Evidence Quality Distribution',
            height=400
        )
        
        return fig
    
    def create_risk_coverage_chart(self):
        """Create risk area coverage chart"""
        risk_coverage = {risk_id: 0 for risk_id in self.risk_areas}
        
        for e in self.evidence:
            tech = self.techniques.get(e['techniqueId'])
            if tech:
                for risk_id in tech.get('riskAreaIds', []):
                    risk_coverage[risk_id] += 1
        
        # Create bar chart
        risk_names = [self.risk_areas[r]['name'] for r in sorted(risk_coverage.keys())]
        counts = [risk_coverage[r] for r in sorted(risk_coverage.keys())]
        
        fig = go.Figure(data=[go.Bar(
            x=counts,
            y=risk_names,
            orientation='h',
            marker_color='#4ecdc4'
        )])
        
        fig.update_layout(
            title='Evidence Coverage by Risk Area',
            xaxis_title='Number of Evidence Records',
            yaxis_title='Risk Area',
            height=400
        )
        
        return fig
    
    def generate_html_dashboard(self):
        """Generate complete HTML dashboard"""
        # Create all charts
        coverage_heatmap = self.create_coverage_heatmap()
        timeline = self.create_timeline_chart()
        rating_dist = self.create_rating_distribution()
        evidence_quality = self.create_evidence_quality_chart()
        risk_coverage = self.create_risk_coverage_chart()
        
        # Convert to HTML
        charts_html = []
        
        if coverage_heatmap:
            charts_html.append(coverage_heatmap.to_html(include_plotlyjs=False, div_id="coverage-heatmap"))
        
        if timeline:
            charts_html.append(timeline.to_html(include_plotlyjs=False, div_id="timeline"))
        
        charts_html.append(f'''
        <div class="row">
            <div class="col-md-6">
                {rating_dist.to_html(include_plotlyjs=False, div_id="rating-dist")}
            </div>
            <div class="col-md-6">
                {evidence_quality.to_html(include_plotlyjs=False, div_id="evidence-quality")}
            </div>
        </div>
        ''')
        
        charts_html.append(risk_coverage.to_html(include_plotlyjs=False, div_id="risk-coverage"))
        
        # Generate stats
        total_evidence = len(self.evidence)
        total_providers = len(self.providers)
        total_techniques = len(self.techniques)
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Create HTML
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Safety Mechanisms Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #f8f9fa;
        }}
        .dashboard-header {{
            background-color: #fff;
            padding: 2rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card {{
            background-color: #fff;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #4ecdc4;
        }}
        .chart-container {{
            background-color: #fff;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .footer {{
            margin-top: 3rem;
            padding: 2rem 0;
            background-color: #343a40;
            color: #fff;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container">
            <h1>🛡️ LLM Safety Mechanisms Dashboard</h1>
            <p class="lead">Tracking safety implementations across major LLM providers</p>
            <p class="text-muted">Last updated: {last_updated}</p>
        </div>
    </div>
    
    <div class="container">
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{total_providers}</div>
                    <div>Providers</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{total_techniques}</div>
                    <div>Techniques</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{total_evidence}</div>
                    <div>Evidence Records</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{len([e for e in self.evidence if e.get("severityBand") == "P"])}</div>
                    <div>Primary Sources</div>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Coverage Heatmap</h2>
            <p>Safety technique implementation across providers. Darker colors indicate higher implementation maturity.</p>
            {charts_html[0] if charts_html else ''}
        </div>
        
        {f'<div class="chart-container"><h2>Implementation Timeline</h2>{charts_html[1]}</div>' if len(charts_html) > 1 and timeline else ''}
        
        <div class="chart-container">
            <h2>Rating Distribution & Evidence Quality</h2>
            {charts_html[2] if len(charts_html) > 2 else charts_html[1] if len(charts_html) > 1 else ''}
        </div>
        
        <div class="chart-container">
            <h2>Risk Area Coverage</h2>
            <p>Number of evidence records addressing each risk area.</p>
            {charts_html[-1]}
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h3>About This Dashboard</h3>
                        <p>This dashboard visualizes data from the LLM Safety Mechanisms dataset, which tracks safety implementations across major language model providers.</p>
                        <p><strong>Data Quality:</strong></p>
                        <ul>
                            <li><strong>Primary (P):</strong> Evidence from official system cards or research papers</li>
                            <li><strong>Benchmarked (B):</strong> Includes quantitative metrics</li>
                            <li><strong>Claimed (C):</strong> Provider claims without detailed evidence</li>
                            <li><strong>Volunteered (V):</strong> Community-contributed evidence</li>
                            <li><strong>Unverified (U):</strong> Pending verification</li>
                        </ul>
                        <p>
                            <a href="https://github.com/sashaagafonoff/LLM-Safety-Mechanisms" class="btn btn-primary">View on GitHub</a>
                            <a href="SUMMARY.md" class="btn btn-secondary">View Text Summary</a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="footer">
        <div class="container">
            <p>LLM Safety Mechanisms Dataset | <a href="https://github.com/sashaagafonoff/LLM-Safety-Mechanisms" style="color: #4ecdc4;">Contribute on GitHub</a></p>
        </div>
    </footer>
</body>
</html>'''
        
        # Save dashboard
        dashboard_path = self.output_dir / 'index.html'
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"✅ Dashboard generated: {dashboard_path}")
        
        # Also copy the markdown summary
        import shutil
        if Path('SUMMARY.md').exists():
            shutil.copy('SUMMARY.md', self.output_dir / 'SUMMARY.md')

def main():
    generator = DashboardGenerator()
    generator.generate_html_dashboard()

if __name__ == "__main__":
    main()