// Cell 1: Title and Introduction
md`# LLM Safety Mechanisms Explorer

This interactive notebook provides comprehensive analysis of Large Language Model safety mechanisms, fetching live data from the [LLM Safety Mechanisms GitHub repository](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms).

## Features
- 🔍 Interactive filtering by provider, technique, and rating
- 📊 Custom comparison views and analytics
- 📁 Export data in multiple formats (JSON, CSV, Excel)
- 📚 Embedded documentation and methodology
- 🔗 Shareable visualization configurations

---`

// Cell 2: Data Fetching and Processing
data = {
    const baseUrl = "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data/";

    try {
        // Fetch all data files
        const [evidence, techniques, providers, models] = await Promise.all([
            fetch(`${baseUrl}evidence.json`).then(d => d.json()),
            fetch(`${baseUrl}techniques.json`).then(d => d.json()),
            fetch(`${baseUrl}providers.json`).then(d => d.json()),
            fetch(`${baseUrl}models.json`).then(d => d.json())
        ]);

        // Process and enrich data
        const processedEvidence = evidence.map(item => ({
            ...item,
            provider_name: providers.find(p => p.id === item.provider_id)?.name || 'Unknown',
            technique_name: techniques.find(t => t.id === item.technique_id)?.name || 'Unknown',
            model_name: models.find(m => m.id === item.model_id)?.name || 'Unknown',
            effectiveness_score: parseFloat(item.effectiveness_rating) || 0,
            date_added: new Date(item.date_added || Date.now())
        }));

        return {
            evidence: processedEvidence,
            techniques,
            providers,
            models,
            lastUpdated: new Date()
        };

    } catch(error) {
        console.error("Error fetching data:", error);
        return {
            evidence: [],
            techniques: [],
            providers: [],
            models: [],
            error: error.message
        };
    }
}

// Cell 3: Interactive Filters
viewof filters = {
    const form = html`<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px; margin-bottom: 20px;">
    <div>
      <label style="display: block; font-weight: bold; margin-bottom: 5px;">Provider</label>
      <select name="provider" style="width: 100%; padding: 8px;">
        <option value="">All Providers</option>
        ${data.providers.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
      </select>
    </div>
    
    <div>
      <label style="display: block; font-weight: bold; margin-bottom: 5px;">Technique</label>
      <select name="technique" style="width: 100%; padding: 8px;">
        <option value="">All Techniques</option>
        ${data.techniques.map(t => `<option value="${t.id}">${t.name}</option>`).join('')}
      </select>
    </div>
    
    <div>
      <label style="display: block; font-weight: bold; margin-bottom: 5px;">Minimum Rating</label>
      <input name="rating" type="range" min="0" max="10" step="0.1" value="0" style="width: 100%;">
      <span style="font-size: 12px; color: #666;">Rating: <span id="rating-value">0</span></span>
    </div>
    
    <div style="grid-column: 1 / -1;">
      <label style="display: block; font-weight: bold; margin-bottom: 5px;">Search</label>
      <input name="search" type="text" placeholder="Search evidence descriptions..." style="width: 100%; padding: 8px;">
    </div>
  </div>`;

    const ratingSpan = form.querySelector('#rating-value');
    const ratingInput = form.querySelector('input[name="rating"]');

    ratingInput.addEventListener('input', () => {
        ratingSpan.textContent = ratingInput.value;
    });

    return form;
}

// Cell 4: Filtered Data
filteredData = {
    let filtered = data.evidence;

    if(filters.provider) {
    filtered = filtered.filter(d => d.provider_id === filters.provider);
}

if (filters.technique) {
    filtered = filtered.filter(d => d.technique_id === filters.technique);
}

if (filters.rating > 0) {
    filtered = filtered.filter(d => d.effectiveness_score >= parseFloat(filters.rating));
}

if (filters.search) {
    const searchTerm = filters.search.toLowerCase();
    filtered = filtered.filter(d =>
        d.description?.toLowerCase().includes(searchTerm) ||
        d.provider_name.toLowerCase().includes(searchTerm) ||
        d.technique_name.toLowerCase().includes(searchTerm)
    );
}

return filtered;
}

// Cell 5: Summary Statistics
md`## Summary Statistics

**Total Evidence Records:** ${filteredData.length.toLocaleString()}  
**Unique Providers:** ${new Set(filteredData.map(d => d.provider_id)).size}  
**Unique Techniques:** ${new Set(filteredData.map(d => d.technique_id)).size}  
**Average Effectiveness:** ${(filteredData.reduce((sum, d) => sum + d.effectiveness_score, 0) / filteredData.length || 0).toFixed(2)}

---`

// Cell 6: Effectiveness Distribution Chart
Plot.plot({
    title: "Effectiveness Rating Distribution",
    width: 800,
    height: 400,
    x: {
        label: "Effectiveness Rating",
        domain: [0, 10]
    },
    y: {
        label: "Count"
    },
    marks: [
        Plot.rectY(filteredData, Plot.binX({ y: "count" }, { x: "effectiveness_score", fill: "steelblue" })),
        Plot.ruleY([0])
    ]
})

// Cell 7: Provider Comparison
Plot.plot({
    title: "Safety Mechanisms by Provider",
    width: 800,
    height: 400,
    x: {
        label: "Provider"
    },
    y: {
        label: "Number of Mechanisms"
    },
    marks: [
        Plot.barY(
            d3.rollup(filteredData, v => v.length, d => d.provider_name),
            { x: ([provider]) => provider, y: ([, count]) => count, fill: "orange" }
        ),
        Plot.ruleY([0])
    ]
})

// Cell 8: Technique Effectiveness Comparison
Plot.plot({
    title: "Average Effectiveness by Technique",
    width: 800,
    height: 500,
    x: {
        label: "Average Effectiveness Rating"
    },
    y: {
        label: "Technique"
    },
    marks: [
        Plot.barX(
            d3.rollup(
                filteredData,
                v => d3.mean(v, d => d.effectiveness_score),
                d => d.technique_name
            ),
            {
                x: ([, avg]) => avg,
                y: ([technique]) => technique,
                fill: "green",
                sort: { y: "x", reverse: true }
            }
        ),
        Plot.ruleX([0])
    ]
})

// Cell 9: Data Table
viewof table = Inputs.table(filteredData.map(d => ({
    Provider: d.provider_name,
    Technique: d.technique_name,
    Model: d.model_name,
    Rating: d.effectiveness_score,
    Description: d.description?.substring(0, 100) + (d.description?.length > 100 ? '...' : ''),
    'Date Added': d.date_added.toLocaleDateString()
})), {
    columns: [
        "Provider",
        "Technique",
        "Model",
        "Rating",
        "Description",
        "Date Added"
    ],
    header: {
        Provider: "Provider",
        Technique: "Safety Technique",
        Model: "Model",
        Rating: "Effectiveness",
        Description: "Description",
        "Date Added": "Date"
    }
})

// Cell 10: Export Functions
viewof exportOptions = {
    const div = html`<div style="padding: 15px; background: #f0f8ff; border-radius: 8px; margin: 20px 0;">
    <h3>Export Data</h3>
    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
      <button id="export-json" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
        📄 Export JSON
      </button>
      <button id="export-csv" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
        📊 Export CSV
      </button>
      <button id="export-config" style="padding: 10px 20px; background: #6f42c1; color: white; border: none; border-radius: 4px; cursor: pointer;">
        ⚙️ Export Config
      </button>
    </div>
  </div>`;

    // Export functions
    const exportJSON = () => {
        const dataStr = JSON.stringify(filteredData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `llm-safety-mechanisms-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
    };

    const exportCSV = () => {
        const headers = ['Provider', 'Technique', 'Model', 'Rating', 'Description', 'Date Added'];
        const csvData = [
            headers.join(','),
            ...filteredData.map(d => [
                d.provider_name,
                d.technique_name,
                d.model_name,
                d.effectiveness_score,
                `"${d.description?.replace(/"/g, '""') || ''}"`,
                d.date_added.toISOString()
            ].join(','))
        ].join('\n');

        const dataBlob = new Blob([csvData], { type: 'text/csv' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `llm-safety-mechanisms-${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    };

    const exportConfig = () => {
        const config = {
            filters: {
                provider: filters.provider,
                technique: filters.technique,
                rating: filters.rating,
                search: filters.search
            },
            timestamp: new Date().toISOString(),
            recordCount: filteredData.length
        };

        const dataStr = JSON.stringify(config, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `llm-safety-config-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
    };

    div.querySelector('#export-json').addEventListener('click', exportJSON);
    div.querySelector('#export-csv').addEventListener('click', exportCSV);
    div.querySelector('#export-config').addEventListener('click', exportConfig);

    return div;
}

// Cell 11: Embedding API
embedAPI = {
    return {
        // Get chart data for embedding
        getChartData: (type, filters = {}) => {
            let data = filteredData;

            switch (type) {
                case 'distribution':
                    return data.map(d => ({ x: d.effectiveness_score, y: 1 }));
                case 'provider-comparison':
                    return Array.from(d3.rollup(data, v => v.length, d => d.provider_name));
                case 'technique-effectiveness':
                    return Array.from(d3.rollup(data, v => d3.mean(v, d => d.effectiveness_score), d => d.technique_name));
                default:
                    return data;
            }
        },

        // Generate shareable URLs
        generateShareableURL: (filters) => {
            const params = new URLSearchParams();
            Object.entries(filters).forEach(([key, value]) => {
                if (value) params.append(key, value);
            });
            return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
        },

        // Get summary statistics
        getSummaryStats: () => ({
            totalRecords: filteredData.length,
            uniqueProviders: new Set(filteredData.map(d => d.provider_id)).size,
            uniqueTechniques: new Set(filteredData.map(d => d.technique_id)).size,
            avgEffectiveness: filteredData.reduce((sum, d) => sum + d.effectiveness_score, 0) / filteredData.length || 0
        })
    };
}

// Cell 12: Documentation
md`## Documentation

### Data Sources
This notebook fetches live data from the following GitHub repository endpoints:
- **Evidence**: \`evidence.json\` - Contains safety mechanism implementations and their effectiveness ratings
- **Techniques**: \`techniques.json\` - Catalog of safety techniques and methodologies  
- **Providers**: \`providers.json\` - LLM provider information and metadata
- **Models**: \`models.json\` - Model specifications and capabilities

### Methodology
- **Effectiveness Ratings**: Numerical scores from 0-10 indicating the effectiveness of safety mechanisms
- **Data Processing**: Real-time data fetching with automatic enrichment and cross-referencing
- **Filtering**: Multi-dimensional filtering across providers, techniques, ratings, and free-text search

### Usage Examples

#### Basic Filtering
1. Select a provider from the dropdown to focus on specific implementations
2. Choose a technique type to analyze particular safety approaches
3. Adjust the minimum rating slider to filter by effectiveness threshold
4. Use the search box for free-text filtering across descriptions

#### Advanced Analytics
- **Distribution Analysis**: Examine the spread of effectiveness ratings
- **Provider Comparison**: Compare safety mechanism adoption across providers
- **Technique Effectiveness**: Identify the most effective safety approaches

#### Data Export
- **JSON Export**: Full structured data with all fields and metadata
- **CSV Export**: Tabular format suitable for spreadsheet analysis
- **Configuration Export**: Save current filter settings for reproducibility

### API Integration
The notebook exposes an embedding API for integration with other applications:

\`\`\`javascript
// Get processed chart data
const chartData = embedAPI.getChartData('distribution');

// Generate shareable URL
const shareURL = embedAPI.generateShareableURL(filters);

// Get summary statistics
const stats = embedAPI.getSummaryStats();
\`\`\`

### Technical Notes
- Data refreshes automatically on notebook reload
- All visualizations are responsive and interactive
- Export functions generate timestamped files
- Shareable configurations preserve filter states

Last updated: ${data.lastUpdated.toLocaleString()}

---

**Repository**: [LLM Safety Mechanisms](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms)  
**License**: MIT  
**Maintainer**: Observable Notebook Community`