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
        # Create charts
        coverage_heatmap = self.create_coverage_heatmap()
        risk_coverage = self.create_risk_coverage_chart()

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
            <h2>Safety Technique Coverage by Provider</h2>
            <p>This heatmap shows which safety techniques have been detected in each provider's documentation. Colors indicate detection confidence based on NLU analysis.</p>
            {coverage_heatmap.to_html(include_plotlyjs=False, div_id="coverage-heatmap")}
        </div>

        <div class="chart-container">
            <h2>Risk Area Coverage</h2>
            <p>Number of safety technique detections addressing each risk area across all providers.</p>
            {risk_coverage.to_html(include_plotlyjs=False, div_id="risk-coverage")}
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h3>About This Dashboard</h3>
                        <p>This dashboard tracks safety mechanism implementations across {total_providers} major LLM providers by analyzing {total_sources} source documents (system cards, technical reports, model cards, and documentation).</p>

                        <p><strong>What This Shows:</strong></p>
                        <ul>
                            <li><strong>Coverage Heatmap:</strong> Which providers implement which safety techniques based on their public documentation</li>
                            <li><strong>Risk Area Coverage:</strong> How well different categories of AI risk are addressed across the industry</li>
                        </ul>

                        <p><strong>Methodology:</strong> Safety techniques are detected using a two-stage NLU pipeline:</p>
                        <ol>
                            <li><strong>Semantic Retrieval:</strong> Identifies candidate text passages using sentence embeddings (all-mpnet-base-v2)</li>
                            <li><strong>Entailment Verification:</strong> Validates technique presence using cross-encoder verification (nli-deberta-v3-small)</li>
                            <li><strong>Quality Filtering:</strong> Removes glossary definitions, "future work" mentions, and other false positives</li>
                        </ol>

                        <p><strong>Confidence Levels:</strong> High confidence indicates strong implementation evidence with specific technical language; Medium indicates clear mentions; Low indicates indirect or weak references.</p>

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
