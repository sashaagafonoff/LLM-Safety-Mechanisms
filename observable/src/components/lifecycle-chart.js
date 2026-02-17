// Lifecycle chart: model development lifecycle visualization
// Ported from Observable notebook cell: lifecycleChart

export function createLifecycleChart(data, chartData, cfg, d3) {
  let selectedProvider = null;

  const container = d3.create("div").style("position", "relative");

  // --- Provider filter bar ---
  const filterBar = container
    .append("div")
    .style("margin-bottom", "12px")
    .style("display", "flex")
    .style("align-items", "center")
    .style("gap", "12px")
    .style("font-family", "'Segoe UI', system-ui, sans-serif");

  filterBar.append("label")
    .style("font-size", "13px").style("font-weight", "600").style("color", "#444")
    .text("Filter by provider:");

  const providerSelect = filterBar
    .append("select")
    .style("font-size", "13px").style("padding", "4px 8px")
    .style("border", "1px solid #ccc").style("border-radius", "4px").style("background", "#fff")
    .on("change", function () {
      selectedProvider = this.value || null;
      updateProviderHighlight();
    });

  providerSelect.append("option").attr("value", "").text("All providers");
  chartData.allProviders.forEach((p) => {
    providerSelect.append("option").attr("value", p).text(p);
  });

  const providerStatus = filterBar.append("span")
    .style("font-size", "12px").style("color", "#888");

  // --- SVG ---
  const svg = container
    .append("svg")
    .attr("width", cfg.width).attr("height", cfg.height)
    .attr("viewBox", `0 0 ${cfg.width} ${cfg.height}`)
    .style("font-family", "'Segoe UI', system-ui, sans-serif")
    .style("background", "#fafafa")
    .style("border-radius", "8px")
    .style("border", "1px solid #e0e0e0");

  // --- Defs ---
  const defs = svg.append("defs");

  const shadowFilter = defs.append("filter")
    .attr("id", "lc-shadow").attr("x", "-10%").attr("y", "-10%")
    .attr("width", "120%").attr("height", "130%");
  shadowFilter.append("feDropShadow")
    .attr("dx", 0).attr("dy", 1).attr("stdDeviation", 1.5)
    .attr("flood-color", "#000").attr("flood-opacity", 0.08);

  defs.append("marker")
    .attr("id", "lc-arrowhead").attr("viewBox", "0 0 10 7")
    .attr("refX", 10).attr("refY", 3.5)
    .attr("markerWidth", 10).attr("markerHeight", 7).attr("orient", "auto")
    .append("polygon").attr("points", "0 0, 10 3.5, 0 7").attr("fill", "#aaa");

  // ── LAYER 1: BEZIER CONNECTORS ──
  const connectorGroup = svg.append("g").attr("class", "lc-connectors");

  chartData.connectors.forEach((conn) => {
    const x1 = conn.govPos.cx;
    const y1 = conn.govPos.y + conn.govPos.height;
    const x2 = conn.tempPos.cx;
    const y2 = conn.tempPos.y;

    const midY = (y1 + y2) / 2;
    const cp1x = x1, cp1y = y1 + (midY - y1) * 0.6;
    const cp2x = x2, cp2y = y2 - (y2 - midY) * 0.6;

    connectorGroup.append("path")
      .attr("class", `lc-connector lc-connector-${conn.techId}`)
      .attr("d", `M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`)
      .attr("fill", "none").attr("stroke", cfg.connector.color)
      .attr("stroke-width", cfg.connector.strokeWidth)
      .attr("stroke-dasharray", cfg.connector.dashArray)
      .attr("opacity", cfg.connector.opacity);

    connectorGroup.append("circle")
      .attr("class", `lc-connector lc-connector-${conn.techId}`)
      .attr("cx", x1).attr("cy", y1).attr("r", 3)
      .attr("fill", cfg.connector.color).attr("opacity", cfg.connector.opacity);

    connectorGroup.append("circle")
      .attr("class", `lc-connector lc-connector-${conn.techId}`)
      .attr("cx", x2).attr("cy", y2).attr("r", 3)
      .attr("fill", cfg.connector.color).attr("opacity", cfg.connector.opacity);
  });

  // ── LAYER 2: GOVERNANCE BAND ──
  const govGroup = svg.append("g").attr("class", "lc-governance");

  govGroup.append("rect")
    .attr("x", cfg.margin.left).attr("y", cfg.governance.top)
    .attr("width", cfg.width - cfg.margin.left - cfg.margin.right)
    .attr("height", cfg.governance.height).attr("rx", 6)
    .attr("fill", "#ECEFF1").attr("stroke", "#90A4AE")
    .attr("stroke-width", 1).attr("stroke-dasharray", "6,3").attr("opacity", 0.5);

  govGroup.append("text")
    .attr("x", cfg.margin.left + 12)
    .attr("y", cfg.governance.top + cfg.governance.labelOffsetY)
    .attr("font-size", "12px").attr("font-weight", "600").attr("fill", "#546E7A")
    .text("Governance & Compliance");

  govGroup.append("text")
    .attr("x", cfg.width - cfg.margin.right - 12)
    .attr("y", cfg.governance.top + cfg.governance.labelOffsetY)
    .attr("text-anchor", "end").attr("font-size", "10px").attr("fill", "#90A4AE")
    .text("organisational oversight across all phases \u2192");

  chartData.governanceTechniques.forEach((tech) => {
    const pos = chartData.govPositions.get(tech.id);
    if (pos) renderTechNode(govGroup, tech, pos, false);
  });

  // ── LAYER 3: TIMELINE ARROW ──
  const timelineY = cfg.phases.areaTop - 18;

  svg.append("line")
    .attr("x1", cfg.margin.left).attr("y1", timelineY)
    .attr("x2", cfg.width - cfg.margin.right - 2).attr("y2", timelineY)
    .attr("stroke", "#bbb").attr("stroke-width", 1.5)
    .attr("marker-end", "url(#lc-arrowhead)");

  svg.append("text")
    .attr("x", cfg.margin.left).attr("y", timelineY - 6)
    .attr("font-size", "10px").attr("fill", "#999")
    .text("MODEL DEVELOPMENT LIFECYCLE");

  // ── LAYER 4: TEMPORAL PHASE COLUMNS ──
  const phaseGroup = svg.append("g").attr("class", "lc-phases");

  chartData.columns.forEach((col) => {
    const cg = phaseGroup.append("g");

    cg.append("rect")
      .attr("x", col.x).attr("y", cfg.phases.areaTop)
      .attr("width", col.width)
      .attr("height", cfg.phases.areaBottom - cfg.phases.areaTop)
      .attr("rx", 6)
      .attr("fill", cfg.phaseColors[col.phaseId] || "#f5f5f5")
      .attr("stroke", cfg.phaseBorderColors[col.phaseId] || "#ddd")
      .attr("stroke-width", 1).attr("opacity", 0.5);

    cg.append("rect")
      .attr("x", col.x).attr("y", cfg.phases.areaTop)
      .attr("width", col.width).attr("height", cfg.phases.headerHeight)
      .attr("rx", 6)
      .attr("fill", cfg.phaseBorderColors[col.phaseId] || "#999")
      .attr("opacity", 0.85);

    cg.append("text")
      .attr("x", col.centerX)
      .attr("y", cfg.phases.areaTop + cfg.phases.headerHeight / 2 + 1)
      .attr("text-anchor", "middle").attr("dominant-baseline", "middle")
      .attr("font-size", "12px").attr("font-weight", "600").attr("fill", "#fff")
      .text(col.phaseName);

    cg.append("text")
      .attr("x", col.x + col.width - 8)
      .attr("y", cfg.phases.areaTop + cfg.phases.headerHeight + 12)
      .attr("text-anchor", "end").attr("font-size", "10px").attr("fill", "#999")
      .text(`${col.techniques.length}`);
  });

  // ── LAYER 5: TECHNIQUE NODES (temporal columns) ──
  const nodesGroup = svg.append("g").attr("class", "lc-nodes");

  chartData.columns.forEach((col) => {
    (col.techniques || []).forEach((tech) => {
      const posKey = tech._isEcho ? `${tech.id}__temporal` : tech.id;
      const pos = chartData.nodePositions.get(posKey);
      if (pos) renderTechNode(nodesGroup, tech, pos, !!tech._isEcho);
    });
  });

  // ── LAYER 6: SPANNING NODES ──
  chartData.spanningPositions.forEach((span) => {
    const sg = nodesGroup.append("g")
      .attr("class", "lc-tech-node")
      .attr("data-tech-id", span.tech.id)
      .attr("transform", `translate(${span.x}, ${span.y})`)
      .style("cursor", "pointer");

    sg.append("rect")
      .attr("width", span.width).attr("height", span.height)
      .attr("rx", cfg.node.radius)
      .attr("fill", "#fff").attr("stroke", span.tech.categoryColor)
      .attr("stroke-width", 1.5).attr("filter", "url(#lc-shadow)");

    sg.append("rect")
      .attr("width", 4).attr("height", span.height).attr("rx", 2)
      .attr("fill", span.tech.categoryColor).attr("opacity", 0.85);

    sg.append("text")
      .attr("x", span.width / 2).attr("y", span.height / 2 + 1)
      .attr("text-anchor", "middle").attr("dominant-baseline", "middle")
      .attr("font-size", `${cfg.node.fontSize}px`).attr("fill", "#333").attr("font-weight", "500")
      .text(span.tech.name);

    const fromCol = chartData.columnLookup.get(span.fromPhase);
    const toCol = chartData.columnLookup.get(span.toPhase);
    if (fromCol && toCol) {
      sg.append("text")
        .attr("x", fromCol.centerX - span.x).attr("y", span.height + 12)
        .attr("text-anchor", "middle").attr("font-size", "9px").attr("fill", "#aaa")
        .text(`\u25C2 ${fromCol.phaseName}`);
      sg.append("text")
        .attr("x", toCol.centerX - span.x).attr("y", span.height + 12)
        .attr("text-anchor", "middle").attr("font-size", "9px").attr("fill", "#aaa")
        .text(`${toCol.phaseName} \u25B8`);
    }

    attachTooltip(sg, span.tech, span);
  });

  // ── LAYER 7: HARM & CONTENT CLASSIFICATION BAND ──
  const harmGroup = svg.append("g").attr("class", "lc-harm");

  harmGroup.append("rect")
    .attr("x", cfg.margin.left).attr("y", cfg.harm.top)
    .attr("width", cfg.width - cfg.margin.left - cfg.margin.right)
    .attr("height", cfg.harm.height).attr("rx", 6)
    .attr("fill", "#FFF3E0").attr("stroke", "#FF9800")
    .attr("stroke-width", 1).attr("stroke-dasharray", "6,3").attr("opacity", 0.4);

  harmGroup.append("text")
    .attr("x", cfg.margin.left + 12)
    .attr("y", cfg.harm.top + cfg.harm.labelOffsetY)
    .attr("font-size", "12px").attr("font-weight", "600").attr("fill", "#E65100")
    .text("Harm & Content Classification");

  harmGroup.append("text")
    .attr("x", cfg.width - cfg.margin.right - 12)
    .attr("y", cfg.harm.top + cfg.harm.labelOffsetY)
    .attr("text-anchor", "end").attr("font-size", "10px").attr("fill", "#FF9800")
    .text("cross-stage classifiers applied at data curation & runtime \u2192");

  chartData.harmTechniques.forEach((tech) => {
    const pos = chartData.harmPositions.get(tech.id);
    if (pos) renderTechNode(harmGroup, tech, pos, false);
  });

  // ── TOOLTIP ──
  const tooltip = container.append("div")
    .style("position", "absolute").style("display", "none")
    .style("background", "#fff").style("border", "1px solid #ddd")
    .style("border-radius", "6px").style("padding", "10px 14px")
    .style("font-size", "12px").style("max-width", "320px")
    .style("box-shadow", "0 2px 8px rgba(0,0,0,0.12)")
    .style("pointer-events", "none").style("z-index", "10")
    .style("font-family", "'Segoe UI', system-ui, sans-serif");

  // ── NODE RENDERER ──
  function renderTechNode(parent, tech, pos, isEcho) {
    const ng = parent.append("g")
      .attr("class", "lc-tech-node")
      .attr("data-tech-id", tech.id)
      .attr("transform", `translate(${pos.x}, ${pos.y})`)
      .style("cursor", "pointer");

    ng.append("rect")
      .attr("width", pos.width).attr("height", pos.height)
      .attr("rx", cfg.node.radius)
      .attr("fill", isEcho ? "#fafafa" : "#fff")
      .attr("stroke", isEcho ? "#bbb" : tech.categoryColor)
      .attr("stroke-width", isEcho ? 1 : 1.5)
      .attr("filter", isEcho ? "none" : "url(#lc-shadow)");

    ng.append("rect")
      .attr("width", 4).attr("height", pos.height).attr("rx", 2)
      .attr("fill", isEcho ? "#ccc" : tech.categoryColor)
      .attr("opacity", isEcho ? 0.4 : 0.85);

    const maxChars = Math.floor((pos.width - 20) / 6.5);
    const label = tech.name.length > maxChars ? tech.name.slice(0, maxChars - 1) + "\u2026" : tech.name;

    ng.append("text")
      .attr("x", cfg.node.padding.x + 4)
      .attr("y", pos.height / 2 + 1)
      .attr("dominant-baseline", "middle")
      .attr("font-size", `${cfg.node.fontSize}px`)
      .attr("fill", isEcho ? "#aaa" : "#333")
      .attr("font-weight", isEcho ? "normal" : "500")
      .attr("font-style", isEcho ? "italic" : "normal")
      .text(label);

    attachTooltip(ng, tech, pos);
  }

  // ── TOOLTIP + CONNECTOR HIGHLIGHT ──
  function attachTooltip(g, tech, pos) {
    g.on("mouseenter", function () {
      svg.selectAll(`.lc-connector-${tech.id}`)
        .attr("opacity", 1).attr("stroke-width", 2.5);

      const phases = (tech.lifecycleStages || [])
        .map((s) => {
          const def = (data.lifecycle || []).find((p) => p.id === s);
          return def?.name || s;
        })
        .join("  \u2192  ");

      const providerList = tech.providerNames.length > 0
        ? tech.providerNames.join(", ")
        : "<em>No provider evidence yet</em>";

      tooltip.style("display", "block").html(
        `<div style="font-weight:600; margin-bottom:4px;">${tech.name}</div>` +
        `<div style="color:#666; margin-bottom:6px;">${tech.description || ""}</div>` +
        `<div style="font-size:11px; color:${tech.categoryColor}; margin-bottom:4px;">\u25A0 ${tech.categoryName}</div>` +
        `<div style="font-size:11px; color:#888; margin-bottom:4px;">Phases: ${phases}</div>` +
        `<div style="font-size:11px; color:#666;">Providers: ${providerList}</div>`
      );

      const tooltipX = pos.x + pos.width + 328 > cfg.width ? pos.x - 330 : pos.x + pos.width + 8;
      tooltip.style("left", tooltipX + "px").style("top", pos.y + "px");
    });

    g.on("mouseleave", function () {
      svg.selectAll(`.lc-connector-${tech.id}`)
        .attr("opacity", cfg.connector.opacity)
        .attr("stroke-width", cfg.connector.strokeWidth);
      tooltip.style("display", "none");
    });
  }

  // ── CATEGORY LEGEND ──
  const uniqueCats = [
    ...new Map(
      chartData.allTechniques.map((t) => {
        const cat = data.categories?.find((c) => c.id === t.categoryId) || {};
        return [t.categoryId, { id: t.categoryId, name: cat.name || t.categoryId, color: cat.color || "#999" }];
      })
    ).values()
  ].sort((a, b) => a.name.localeCompare(b.name));

  const legend = container.append("div")
    .style("display", "flex").style("gap", "16px").style("margin-top", "10px")
    .style("flex-wrap", "wrap").style("font-family", "'Segoe UI', system-ui, sans-serif");

  legend.append("span")
    .style("font-size", "11px").style("font-weight", "600").style("color", "#666")
    .style("align-self", "center").text("Categories:");

  uniqueCats.forEach((cat) => {
    const item = legend.append("span")
      .style("display", "inline-flex").style("align-items", "center")
      .style("gap", "5px").style("font-size", "11px").style("color", "#555");

    item.append("span")
      .style("width", "10px").style("height", "10px").style("border-radius", "2px")
      .style("background", cat.color).style("display", "inline-block");

    item.append("span").text(cat.name);
  });

  // ── PROVIDER FILTER ──
  function updateProviderHighlight() {
    if (!selectedProvider) {
      svg.selectAll(".lc-tech-node").attr("opacity", 1);
      svg.selectAll(".lc-connector").attr("opacity", cfg.connector.opacity);
      providerStatus.text("");
      return;
    }

    const providerTechNames = new Set();
    (data.flatPairs || []).forEach((fp) => {
      if (fp.provider === selectedProvider) providerTechNames.add(fp.technique);
    });

    const providerTechIds = new Set();
    (data.raw?.techniques || data.techniques || []).forEach((t) => {
      if (providerTechNames.has(t.name)) providerTechIds.add(t.id);
    });

    svg.selectAll(".lc-tech-node").each(function () {
      const techId = d3.select(this).attr("data-tech-id");
      d3.select(this).attr("opacity", providerTechIds.has(techId) ? 1 : 0.15);
    });

    svg.selectAll(".lc-connector").each(function () {
      const cls = d3.select(this).attr("class") || "";
      const match = [...providerTechIds].some((id) => cls.includes(`lc-connector-${id}`));
      d3.select(this).attr("opacity", match ? 0.8 : 0.08);
    });

    providerStatus.text(`${providerTechIds.size} of ${chartData.allTechniques.length} techniques evidenced`);
  }

  return container.node();
}
