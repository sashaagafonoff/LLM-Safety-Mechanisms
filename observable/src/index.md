---
title: LLM Safety Mechanisms Explorer
style: custom-styles.css
toc: false
---

# LLM Safety Mechanisms Explorer

This project supports holistic analysis of Large Language Model safety mechanisms, using data from my [LLM Safety Mechanisms GitHub repository](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms). Please raise any issues/suggestions via [GitHub](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms/issues).

```js
// --- Data Loading (from GitHub) ---
const ghBase = "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data";
const fetchJson = (name) => fetch(`${ghBase}/${name}`).then((r) => r.json());

const [evidence, techniques, categories, techniqueMap, models, providers, lifecycle] =
  await Promise.all([
    fetchJson("evidence.json"),
    fetchJson("techniques.json"),
    fetchJson("categories.json"),
    fetchJson("model_technique_map.json"),
    fetchJson("models.json"),
    fetchJson("providers.json"),
    fetchJson("model_lifecycle.json")
  ]);
```

```js
// --- Component Imports ---
import {buildDataset, applyFilters} from "./components/data-pipeline.js";
import {generateColorSchemes} from "./components/color-schemes.js";
import {createFilterForm} from "./components/filters.js";
import {unifiedChartConfig, buildUnifiedChartData, createUnifiedChartLayouts, validateUnifiedChartLayout} from "./components/unified-chart-data.js";
import {createUnifiedChart} from "./components/unified-chart.js";
import {createSunburstChart} from "./components/sunburst-chart.js";
import {lifecycleConfig, buildLifecycleChartData} from "./components/lifecycle-data.js";
import {createLifecycleChart} from "./components/lifecycle-chart.js";
import {networkConfig, buildNetworkGraph, positionGraph, computeAutoLayout, validateNetworkLayout} from "./components/network-data.js";
import {createNetworkViz} from "./components/network-viz.js";
import {createDataQualityReport} from "./components/data-quality.js";
```

```js
// --- Build Dataset ---
const data = buildDataset(evidence, techniques, categories, techniqueMap, models, providers, lifecycle);
const {categoryColors, providerColors} = generateColorSchemes(data.raw.categories, data.raw.providers, d3);
```

```js
// --- Filter + Filtered Data (reactive) ---
const filteredData = applyFilters(data, filters);
```

## Why do we need it?

Understanding which safety mechanisms are implemented across large language models currently requires piecing together information from scattered documentation, each using different terminology and varying levels of detail. This work provides a structured, queryable view of safety technique coverage across major frontier models — as a coverage profile that assists researchers, practitioners, and policymakers to make informed risk assessments.

---

## Provider-Technique Relationships

This is designed to support coverage analysis. Use the filter below this graph to reduce the dataset for improved clarity. You can apply force layout on selected subsets of nodes.

<div class="card">

```js
const chartData = buildUnifiedChartData(data, filteredData, categoryColors, providerColors, d3);
const layouts = createUnifiedChartLayouts(d3);
const validatedLayout = validateUnifiedChartLayout(chartData, layouts);
display(createUnifiedChart(chartData, unifiedChartConfig, layouts, validatedLayout, d3));
```

</div>

---

## Dataset Filter

Constrain the collection using the following tools.

```js
const filters = view(createFilterForm(data, d3));
```

---

## Safety Mechanisms by Category

This chart provides a visual overview of the safety mechanisms documented in this project. The Categories and individual techniques have been defined as a common taxonomy across the set of providers over months of iteration and analysis. This has been a data-driven approach, collapsing members where there was high overlap. I've also removed life cycle stage as higher order categories, and these are now represented intersectionally with techniques in a different section of the dataset.

<div class="card">

```js
display(createSunburstChart(data, filteredData, categoryColors, d3));
```

</div>

---

## Summary Statistics

```js
const providerStats = {};
filteredData.forEach((d) => {
  if (!providerStats[d.provider]) {
    providerStats[d.provider] = {provider: d.provider, techniques: new Set(), high: 0, medium: 0, low: 0};
  }
  providerStats[d.provider].techniques.add(d.techniqueId);
  if (d.rating === "high") providerStats[d.provider].high++;
  else if (d.rating === "medium") providerStats[d.provider].medium++;
  else providerStats[d.provider].low++;
});

const summaryRows = Object.values(providerStats).map((s) => ({
  Provider: s.provider,
  "Techniques": s.techniques.size,
  "High": s.high,
  "Medium": s.medium,
  "Low": s.low,
  "Total Evidence": s.high + s.medium + s.low
})).sort((a, b) => b["Total Evidence"] - a["Total Evidence"]);
```

```js
display(Inputs.table(summaryRows, {
  columns: ["Provider", "Techniques", "High", "Medium", "Low", "Total Evidence"],
  header: {
    Provider: "Provider",
    Techniques: "# Techniques",
    High: "High",
    Medium: "Medium",
    Low: "Low",
    "Total Evidence": "Total Evidence"
  }
}));
```

---

## Model Development Lifecycle

Safety techniques mapped across the six phases of model development. Techniques appearing in multiple phases are connected with bridge lines. The governance band spans the full lifecycle to reflect its cross-cutting nature. Use the provider filter to compare coverage profiles.

<div class="card">

```js
const lifecycleChartData = buildLifecycleChartData(data);
display(createLifecycleChart(data, lifecycleChartData, lifecycleConfig, d3));
```

</div>

---

## Documentation Map

The following chart shows the relationship between documents in the collection to providers (via models). This is to provide a quick overview as to which documentation has been brought into the dataset for analysis and will also assist in coverage analysis as I identify gaps in information. Click and drag to move things around. You can export the layout and save it as you prefer. Tooltips on the document nodes provide the URIs for the original source document referenced.

<div class="card">

```js
const netGraph = buildNetworkGraph(data);
const netLayout = FileAttachment("./data/network-layout.json").json();
```

```js
const validatedNetLayout = validateNetworkLayout(netGraph, await netLayout);
const autoLayout = computeAutoLayout(netGraph, networkConfig, d3);
const positioned = positionGraph(netGraph, validatedNetLayout, networkConfig, d3);
display(createNetworkViz(positioned, validatedNetLayout, autoLayout, networkConfig, providerColors, d3));
```

</div>

```js
display(createDataQualityReport(data, providerColors));
```

---

## Export

```js
function downloadJSON() {
  const blob = new Blob([JSON.stringify(filteredData, null, 2)], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "filtered-safety-data.json";
  a.click();
  URL.revokeObjectURL(url);
}

function downloadCSV() {
  const headers = ["provider", "technique", "category", "rating", "severityBand", "model"];
  const rows = filteredData.map((d) =>
    headers.map((h) => JSON.stringify(d[h] || "")).join(",")
  );
  const csv = [headers.join(","), ...rows].join("\n");
  const blob = new Blob([csv], {type: "text/csv"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "filtered-safety-data.csv";
  a.click();
  URL.revokeObjectURL(url);
}
```

```js
display(html`<div style="display: flex; gap: 10px;">
  <button onclick=${downloadJSON}>Export Filtered JSON</button>
  <button onclick=${downloadCSV}>Export Filtered CSV</button>
</div>`);
```

---

## Current (& Planned) Activity

This project is under active development. Current priorities include:

- **Improving detection accuracy and improving human review workflows** — *[Underway]* Manual ground-truth labelling against source documentation is underway to empirically tune the semantic matching thresholds. The goal is reliable, automated linking of models to techniques with transparent confidence levels. I'm also running post-labelling analysis to optimise the technique and category taxonomy to minimise overlap (and concept confusability) by the automated linking workflow. I'm also making improvements to the human review user interface with a view to optimising the linking output review workflow — including capture of link origination sources (NLU/LLM/Human) — which will lead into simpler feedback mechanisms (including community-based contributions).
- **Reported Safety Incidents** — *[Planned]* Reported safety incidents linked to models, with a mechanism for public users to submit incidents as well as performing automated scans for them. Recent issues with Grok stand out as an excellent example, as do situations like ChatGPT encouraging risky/dangerous behaviours.

---

## Documentation

### Data Sources

This notebook fetches live data from the following GitHub repository endpoints:

- **Evidence:** `evidence.json` — Points at sources of documentation (and soon, third party analysis) for models. This is used by `/scripts/ingest_universal.py` to map techniques to models. Metadata for the document in evidence.json lists the provider and model versions to which it relates.
- **Techniques:** `techniques.json` — Catalog of safety techniques and methodologies. These are expanded with additional semantic content (descriptions, alternative equivalent terminology, etc) to support the automation step which correlates evidence (and related models) with techniques using NLU libraries.
- **Providers:** `providers.json` — LLM provider names.
- **Models:** `models.json` — Model versions.

### Methodology

- **Data Processing:** Documentation sources are converted to flat file using Python (BeautifulSoup), then matched against the semantic concepts captured in techniques.json using vectorization: it uses a Bi-Encoder model (all-mpnet-base-v2) to convert the descriptions of these techniques into mathematical vector embeddings.
- **Confidence:** This is calculated via a Cross-Encoder model (nli-deberta-v3-small) trained on Natural Language Inference (NLI). High Confidence: > 80% entailment score, Medium Confidence: > 50% entailment score.
- **Filtering:** Multi-dimensional filtering across providers, techniques, ratings, and free-text search.

### Usage Examples

#### Basic Filtering

1. Select a provider from the dropdown to focus on specific implementations
2. Choose a technique type to analyse particular safety approaches
3. Adjust the minimum rating slider to filter by confidence threshold
4. Use the search box for free-text filtering across descriptions

#### Advanced Analytics

**Provider Comparison:** Compare safety mechanism adoption across providers

#### Data Export

- **JSON Export:** Full structured data with all fields and metadata
- **CSV Export:** Tabular format suitable for spreadsheet analysis
- **Configuration Export:** Save current filter settings for reproducibility

---

**Repository:** [LLM Safety Mechanisms](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms) · **License:** MIT · **Maintainer:** Sasha Agafonoff
