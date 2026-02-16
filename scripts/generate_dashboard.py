import json
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
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

        with open('data/models.json', 'r') as f:
            models_data = json.load(f)
            if isinstance(models_data, dict) and 'models' in models_data:
                self.models_list = models_data['models']
            elif isinstance(models_data, list):
                self.models_list = models_data
            else:
                self.models_list = []

        # Build provider-technique matrix from technique_map
        self.build_technique_matrix()

    def build_technique_matrix(self):
        """Build provider-technique detection matrix"""
        self.provider_techniques = defaultdict(lambda: defaultdict(list))
        self.technique_sources = defaultdict(list)
        self.source_by_id = {s['id']: s for s in self.sources if 'id' in s}

        for doc_id, detected_techniques in self.technique_map.items():
            source = self.source_by_id.get(doc_id)
            if not source:
                continue
            provider = source.get('provider')
            if not provider:
                continue

            for tech in detected_techniques:
                if not tech.get('active', True):
                    continue
                tech_id = tech.get('techniqueId')
                confidence = tech.get('confidence', 'Unknown')
                if tech_id:
                    self.provider_techniques[provider][tech_id].append(confidence)
                    self.technique_sources[tech_id].append({
                        'provider': provider,
                        'source': doc_id,
                        'confidence': confidence
                    })

    def _get_provider_order(self):
        """Get providers ordered by source count desc, then alphabetical."""
        providers_with_sources = set()
        for s in self.sources:
            p = s.get('provider')
            if p and p in self.providers:
                providers_with_sources.add(p)

        return sorted(
            providers_with_sources,
            key=lambda p: (-len([s for s in self.sources
                                if s.get('provider') == p]),
                           self.providers.get(p, {}).get('name', p)),
        )

    def create_coverage_heatmap(self):
        """Create provider-technique coverage heatmap"""
        provider_order = self._get_provider_order()

        # Sort techniques by category then name, exclude aspirational
        sorted_techniques = sorted(
            [t for t in self.techniques.values()
             if t.get('status') != 'aspirational'],
            key=lambda t: (
                self.categories.get(t['categoryId'], {}).get('name', ''),
                t['name']
            )
        )

        # Build matrix
        matrix = []
        technique_names = []
        category_labels = []

        for tech in sorted_techniques:
            tech_id = tech['id']
            technique_names.append(tech['name'])
            cat = self.categories.get(tech['categoryId'], {})
            category_labels.append(cat.get('name', ''))
            row = []

            for prov_id in provider_order:
                confidences = self.provider_techniques[prov_id].get(
                    tech_id, [])
                if confidences:
                    if 'High' in confidences:
                        row.append(3)
                    elif 'Medium' in confidences:
                        row.append(2)
                    else:
                        row.append(1)
                else:
                    row.append(0)

            matrix.append(row)

        provider_names = [self.providers[p]['name'] for p in provider_order]

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=provider_names,
            y=technique_names,
            colorscale=[
                [0, '#f0f0f0'],      # No detection
                [0.33, '#ff6b6b'],   # Low (1)
                [0.67, '#ffd93d'],   # Medium (2)
                [1.0, '#4ecdc4']     # High (3)
            ],
            text=[[self._get_rating_text(val) for val in row]
                  for row in matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate=("Provider: %{x}<br>Technique: %{y}<br>"
                          "Confidence: %{text}<extra></extra>"),
            showscale=False
        ))

        fig.update_layout(
            title="Safety Technique Coverage by Provider",
            xaxis_title="",
            yaxis_title="",
            height=max(900, len(technique_names) * 22),
            width=max(1000, len(provider_names) * 80 + 350),
            yaxis=dict(tickmode='linear', autorange='reversed'),
            xaxis=dict(side='top', tickangle=-45),
            margin=dict(l=300, t=120, r=30, b=30)
        )

        return fig

    def _get_rating_text(self, value):
        """Convert numeric rating to text"""
        if value == 0:
            return "\u2014"
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
                    risk_coverage[risk_id] += len(
                        self.technique_sources[tech_id])

        # Create bar chart sorted by count
        risk_data = sorted(
            [(self.risk_areas[r]['name'], risk_coverage[r])
             for r in risk_coverage.keys()],
            key=lambda x: x[1]
        )
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
            yaxis_title='',
            height=max(350, len(risk_names) * 30),
            margin=dict(l=250)
        )

        return fig

    def create_category_chart(self):
        """Create technique count by category chart"""
        cat_counts = defaultdict(int)
        cat_detected = defaultdict(int)

        for tech in self.techniques.values():
            if tech.get('status') == 'aspirational':
                continue
            cat_id = tech['categoryId']
            cat_counts[cat_id] += 1
            if tech['id'] in self.technique_sources:
                cat_detected[cat_id] += 1

        cat_names = []
        totals = []
        detected = []

        for cat_id in sorted(cat_counts.keys(),
                            key=lambda c: self.categories.get(
                                c, {}).get('name', '')):
            cat_names.append(self.categories[cat_id]['name'])
            totals.append(cat_counts[cat_id])
            detected.append(cat_detected[cat_id])

        fig = go.Figure(data=[
            go.Bar(name='Detected', x=cat_names, y=detected,
                   marker_color='#4ecdc4'),
            go.Bar(name='Total', x=cat_names, y=totals,
                   marker_color='#e0e0e0'),
        ])

        fig.update_layout(
            title='Techniques by Category',
            barmode='overlay',
            height=350,
            xaxis_tickangle=-20,
            margin=dict(b=100)
        )

        return fig

    def generate_html_dashboard(self):
        """Generate complete HTML dashboard"""
        # Create charts
        coverage_heatmap = self.create_coverage_heatmap()
        risk_coverage = self.create_risk_coverage_chart()
        category_chart = self.create_category_chart()

        # Generate stats
        providers_with_sources = set(
            s.get('provider') for s in self.sources if s.get('provider'))
        total_sources = len(self.sources)
        total_providers = len(providers_with_sources)
        active_techniques = len([t for t in self.techniques.values()
                                if t.get('status') != 'aspirational'])
        active_detected = len([
            t_id for t_id in self.technique_sources
            if t_id in self.techniques
            and self.techniques[t_id].get('status') != 'aspirational'
        ])
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
        .stat-label {{
            color: #666;
            font-size: 0.95rem;
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
            <h1>LLM Safety Mechanisms Dashboard</h1>
            <p class="lead">Tracking safety implementations across major LLM providers</p>
            <p class="text-muted">Last updated: {last_updated}</p>
        </div>
    </div>

    <div class="container">
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{total_providers}</div>
                    <div class="stat-label">Providers</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{active_techniques}</div>
                    <div class="stat-label">Active Techniques</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{active_detected}/{active_techniques}</div>
                    <div class="stat-label">Techniques Detected</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{total_sources}</div>
                    <div class="stat-label">Source Documents</div>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h2>Safety Technique Coverage by Provider</h2>
            <p>Which safety techniques have been detected in each provider's documentation. Colours indicate detection confidence.</p>
            {coverage_heatmap.to_html(include_plotlyjs=False, div_id="coverage-heatmap")}
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <h2>Techniques by Category</h2>
                    {category_chart.to_html(include_plotlyjs=False, div_id="category-chart")}
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <h2>Risk Area Coverage</h2>
                    {risk_coverage.to_html(include_plotlyjs=False, div_id="risk-coverage")}
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h3>About This Dashboard</h3>
                        <p>This dashboard tracks safety mechanism implementations across {total_providers} LLM providers by analysing {total_sources} source documents (system cards, technical reports, model cards, and documentation).</p>

                        <p><strong>Methodology:</strong> Safety techniques are detected using a multi-stage pipeline:</p>
                        <ol>
                            <li><strong>Semantic Retrieval:</strong> Identifies candidate text passages using sentence embeddings (all-mpnet-base-v2)</li>
                            <li><strong>Entailment Verification:</strong> Validates technique presence using cross-encoder verification (nli-deberta-v3-small)</li>
                            <li><strong>LLM Review:</strong> Claude reviews findings in context, confirming matches and flagging gaps</li>
                            <li><strong>Quality Filtering:</strong> Removes glossary definitions, "future work" mentions, and other false positives</li>
                        </ol>

                        <p><strong>Confidence Levels:</strong> High = strong implementation evidence with specific technical language; Medium = clear mentions; Low = indirect or weak references.</p>

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

        print(f"Dashboard generated: {dashboard_path}")
        print(f"  Providers: {total_providers}")
        print(f"  Techniques: {active_detected}/{active_techniques}")
        print(f"  Sources: {total_sources}")

        # SUMMARY.md is written directly to docs/ by generate_report.py


def main():
    generator = DashboardGenerator()
    generator.generate_html_dashboard()


if __name__ == "__main__":
    main()
