---
title: LLM Safety Mechanisms Explorer
style: custom-styles.css
---

# LLM Safety Mechanisms Explorer

An interactive dashboard for exploring safety techniques implemented by major LLM providers.

---

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
import {createCoverageHeatmap} from "./components/coverage-heatmap.js";
```

```js
// --- Build Dataset ---
const data = buildDataset(evidence, techniques, categories, techniqueMap, models, providers, lifecycle);
const {categoryColors, providerColors} = generateColorSchemes(data.raw.categories, data.raw.providers, d3);
```

---

## Filters

```js
const filters = view(createFilterForm(data, d3));
```

```js
const filteredData = applyFilters(data, filters);
```

---

## Safety Technique Coverage by Provider

<div class="card">

```js
display(createCoverageHeatmap(data, filteredData, categoryColors, providerColors, d3));
```

</div>

---

## Provider–Technique Network

<div class="card">

```js
const chartData = buildUnifiedChartData(data, filteredData, categoryColors, providerColors, d3);
const layouts = createUnifiedChartLayouts(d3);
const validatedLayout = validateUnifiedChartLayout(chartData, layouts);
display(createUnifiedChart(chartData, unifiedChartConfig, layouts, validatedLayout, d3));
```

</div>

---

## Category Sunburst

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

<div class="card">

```js
const lifecycleChartData = buildLifecycleChartData(data);
display(createLifecycleChart(data, lifecycleChartData, lifecycleConfig, d3));
```

</div>

---

## Document Network

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

---

## Data Quality

```js
display(createDataQualityReport(data, providerColors));
```

---

## Data Table

```js
const tableData = filteredData.map((d) => ({
  Provider: d.provider,
  Technique: d.technique,
  Category: d.category,
  Rating: d.rating,
  "Severity Band": d.severityBand || "—",
  Model: d.model || "—"
}));

display(Inputs.table(tableData, {
  columns: ["Provider", "Technique", "Category", "Rating", "Severity Band", "Model"],
  sort: "Provider",
  rows: 20
}));
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

<details>
<summary>About this dashboard</summary>

This dashboard visualizes safety techniques implemented by major LLM providers (OpenAI, Anthropic, Google, Meta, Amazon, and others). The data is sourced from official documentation, research papers, and publicly available information.

**Charts:**
- **Safety Technique Coverage** — Heatmap showing which providers implement which techniques, colored by confidence level (High/Medium/Low).
- **Provider–Technique Network** — Interactive force-directed graph showing which providers implement which techniques. Drag nodes to customize layout, use toolbar to save/load positions.
- **Category Sunburst** — Hierarchical view of technique categories and their relative coverage.
- **Model Development Lifecycle** — Timeline view of when safety techniques are applied during model development phases.
- **Document Network** — Network graph showing relationships between source documents, providers, and models.

**Filters** narrow all charts simultaneously by provider, category, rating, or severity band.

Source: [GitHub Repository](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms)
</details>
