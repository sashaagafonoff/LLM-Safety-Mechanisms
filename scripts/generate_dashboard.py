import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path
import numpy as np
from collections import defaultdict

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
            evidence_data = json.load(f)
            self.sources = evidence_data.get('sources', [])

        with open('data/model_technique_map.json', 'r') as f:
            self.technique_map = json.load(f)

        with open('data/risk_areas.json', 'r') as f:
            self.risk_areas = {r['id']: r for r in json.load(f)}

        # Build provider-technique matrix from technique_map
        self.build_technique_matrix()

    def build_technique_matrix(self):
        """Build provider-technique detection matrix"""
        self.provider_techniques = defaultdict(lambda: defaultdict(list))
        self.technique_sources = defaultdict(list)

        for source_key, detected_techniques in self.technique_map.items():
            # Find provider for this source
            provider = None
            for source in self.sources:
                if source.get('url') == source_key or source.get('id') == source_key:
                    provider = source.get('provider')
                    break

            if not provider:
                continue

            # Track techniques per provider
            for tech in detected_techniques:
                tech_id = tech.get('techniqueId')
                confidence = tech.get('confidence', 'Unknown')
                if tech_id:
                    self.provider_techniques[provider][tech_id].append(confidence)
                    self.technique_sources[tech_id].append({
                        'provider': provider,
                        'source': source_key,
                        'confidence': confidence
                    })

    def create_coverage_heatmap(self):
        """Create provider-technique coverage heatmap"""
        # Build matrix
        provider_ids = ['openai', 'anthropic', 'google', 'meta', 'amazon']
        detected_techniques = set()
        for tech_id in self.technique_sources.keys():
            if tech_id in self.techniques:
                detected_techniques.add(tech_id)

        technique_ids = sorted(detected_techniques)

        # Create rating matrix
        matrix = []
        technique_names = []

        for tech_id in technique_ids:
            if tech_id not in self.techniques:
                continue

            technique_names.append(self.techniques[tech_id]['name'])
            row = []

            for prov_id in provider_ids:
                confidences = self.provider_techniques[prov_id].get(tech_id, [])

                if confidences:
                    # Use highest confidence
                    if 'High' in confidences:
                        row.append(3)
                    elif 'Medium' in confidences:
                        row.append(2)
                    else:
                        row.append(1)
                else:
                    row.append(0)

            matrix.append(row)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=[self.providers[p]['name'] for p in provider_ids if p in self.providers],
            y=technique_names,
            colorscale=[
                [0, '#f0f0f0'],      # No detection
                [0.33, '#ff6b6b'],   # Low (1)
                [0.67, '#ffd93d'],   # Medium (2)
                [1.0, '#4ecdc4']     # High (3)
            ],
            text=[[self._get_rating_text(val) for val in row] for row in matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="Provider: %{x}<br>Technique: %{y}<br>Confidence: %{text}<extra></extra>"
        ))

        fig.update_layout(
            title="LLM Safety Mechanism Detection by Provider",
            xaxis_title="Provider",
            yaxis_title="Safety Technique",
            height=max(800, len(technique_names) * 20),
            width=1000,
            yaxis=dict(tickmode='linear'),
            xaxis=dict(side='top')
        )

        return fig

    def _get_rating_text(self, value):
        """Convert numeric rating to text"""
        if value == 0:
            return "—"
        elif value == 1:
            return "Low"
        elif value == 2:
            return "Med"
        elif value == 3:
            return "High"
        return str(value)

    def create_timeline_chart(self):
        """Create source addition timeline"""
        # Prepare timeline data
        timeline_data = []

        for source in self.sources:
            if source.get('date_added'):
                timeline_data.append({
                    'Date': source['date_added'],
                    'Provider': self.providers.get(source.get('provider'), {}).get('name', source.get('provider', 'Unknown')),
                    'Title': source.get('title', 'Unknown')[:40],
                    'Type': source.get('type', 'Unknown')
                })

        if not timeline_data:
            return None

        df = pd.DataFrame(timeline_data)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')

        # Create timeline
        fig = px.scatter(df, x='Date', y='Provider', color='Type',
                        hover_data=['Title'],
                        title='Source Document Timeline',
                        height=400)

        fig.update_traces(marker=dict(size=12))
        fig.update_layout(
            xaxis_title="Date Added",
            yaxis_title="Provider"
        )

        return fig

    def create_confidence_distribution(self):
        """Create detection confidence distribution chart"""
        # Count confidences by provider
        confidence_counts = {}

        for provider_id in self.providers:
            counts = {'High': 0, 'Medium': 0, 'Low': 0}

            for tech_id, confidences in self.provider_techniques[provider_id].items():
                for conf in confidences:
                    if conf in counts:
                        counts[conf] += 1

            if sum(counts.values()) > 0:
                confidence_counts[self.providers[provider_id]['name']] = counts

        # Create stacked bar chart
        providers = list(confidence_counts.keys())
        high_counts = [confidence_counts[p]['High'] for p in providers]
        medium_counts = [confidence_counts[p]['Medium'] for p in providers]
        low_counts = [confidence_counts[p]['Low'] for p in providers]

        fig = go.Figure(data=[
            go.Bar(name='High', x=providers, y=high_counts, marker_color='#4ecdc4'),
            go.Bar(name='Medium', x=providers, y=medium_counts, marker_color='#ffd93d'),
            go.Bar(name='Low', x=providers, y=low_counts, marker_color='#ff6b6b')
        ])

        fig.update_layout(
            barmode='stack',
            title='Detection Confidence Distribution by Provider',
            xaxis_title='Provider',
            yaxis_title='Number of Detections',
            height=400
        )

        return fig

    def create_source_type_chart(self):
        """Create source type distribution"""
        type_counts = defaultdict(int)
        for source in self.sources:
            source_type = source.get('type', 'Unknown')
            type_counts[source_type] += 1

        fig = go.Figure(data=[go.Pie(
            labels=list(type_counts.keys()),
            values=list(type_counts.values()),
            hole=.3,
            marker_colors=['#4ecdc4', '#6c5ce7', '#ffd93d', '#ff6b6b', '#a29bfe', '#fd79a8', '#fdcb6e']
        )])

        fig.update_layout(
            title='Source Document Types',
            height=400
        )

        return fig

    def create_risk_coverage_chart(self):
        """Create risk area coverage chart"""
        risk_coverage = {risk_id: 0 for risk_id in self.risk_areas}

        for tech_id in self.technique_sources.keys():
            tech = self.techniques.get(tech_id)
            if tech:
                for risk_id in tech.get('riskAreaIds', []):
                    risk_coverage[risk_id] += len(self.technique_sources[tech_id])

        # Create bar chart
        risk_data = [(self.risk_areas[r]['name'], risk_coverage[r])
                     for r in sorted(risk_coverage.keys())]
        risk_names = [r[0] for r in risk_data]
        counts = [r[1] for r in risk_data]

        fig = go.Figure(data=[go.Bar(
            x=counts,
            y=risk_names,
            orientation='h',
            marker_color='#4ecdc4'
        )])

        fig.update_layout(
            title='Detection Coverage by Risk Area',
            xaxis_title='Number of Detections',
            yaxis_title='Risk Area',
            height=400
        )

        return fig

    def generate_html_dashboard(self):
        """Generate complete HTML dashboard"""
        # Create all charts
        coverage_heatmap = self.create_coverage_heatmap()
        timeline = self.create_timeline_chart()
        confidence_dist = self.create_confidence_distribution()
        source_types = self.create_source_type_chart()
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
                {confidence_dist.to_html(include_plotlyjs=False, div_id="confidence-dist")}
            </div>
            <div class="col-md-6">
                {source_types.to_html(include_plotlyjs=False, div_id="source-types")}
            </div>
        </div>
        ''')

        charts_html.append(risk_coverage.to_html(include_plotlyjs=False, div_id="risk-coverage"))

        # Generate stats
        total_sources = len(self.sources)
        total_providers = len(self.providers)
        total_techniques = len(self.techniques)
        techniques_detected = len(self.technique_sources)
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
            <p class="lead">Tracking safety implementations across major LLM providers via NLU analysis</p>
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
                    <div>Total Techniques</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{techniques_detected}</div>
                    <div>Detected</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{total_sources}</div>
                    <div>Source Documents</div>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h2>Coverage Heatmap</h2>
            <p>Safety technique detection across providers via NLU analysis. Colors indicate detection confidence.</p>
            {charts_html[0] if charts_html else ''}
        </div>

        {f'<div class="chart-container"><h2>Source Document Timeline</h2>{charts_html[1]}</div>' if len(charts_html) > 1 and timeline else ''}

        <div class="chart-container">
            <h2>Detection Confidence & Source Types</h2>
            {charts_html[2] if len(charts_html) > 2 else charts_html[1] if len(charts_html) > 1 else ''}
        </div>

        <div class="chart-container">
            <h2>Risk Area Coverage</h2>
            <p>Number of technique detections addressing each risk area.</p>
            {charts_html[-1]}
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h3>About This Dashboard</h3>
                        <p>This dashboard visualizes data from the LLM Safety Mechanisms dataset, which uses NLU analysis to detect safety technique implementations across {total_sources} source documents from major language model providers.</p>
                        <p><strong>Detection Confidence:</strong></p>
                        <ul>
                            <li><strong>High:</strong> Strong evidence with implementation-specific language</li>
                            <li><strong>Medium:</strong> Moderate evidence of technique usage</li>
                            <li><strong>Low:</strong> Weak or indirect mentions</li>
                        </ul>
                        <p><strong>Methodology:</strong> Uses a two-stage NLU pipeline with semantic retrieval (all-mpnet-base-v2) and entailment verification (cross-encoder/nli-deberta-v3-small), enhanced with quality filters to avoid false positives.</p>
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
