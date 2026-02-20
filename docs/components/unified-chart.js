// Unified chart: Provider-technique network visualization
// Ported from Observable notebook cell: unifiedChart

import {UNIFIED_LAYOUT_STORAGE_KEY} from "./unified-chart-data.js";

export function createUnifiedChart(chartData, config, layouts, validatedLayout, d3) {
  const { width, height } = config;

  let currentLayoutName = validatedLayout.layoutName;
  let currentAnchors = { ...validatedLayout.labelAnchors };

  chartData.nodes.forEach((node) => {
    const pos = validatedLayout.positions[node.id];
    if (pos) {
      node.x = pos.x;
      node.y = pos.y;
    }
  });

  const selectedNodes = new Set();
  let forceSimulation = null;
  let layoutModified = false;
  let persistentTooltip = null;
  let selectedLinkElement = null;
  let isDragging = false;

  const container = d3.create("div").style("position", "relative");

  // ── Toolbar ──
  const toolbar = container
    .append("div")
    .style("margin-bottom", "10px")
    .style("display", "flex")
    .style("gap", "8px")
    .style("flex-wrap", "wrap")
    .style("align-items", "center");

  const buttonStyle = `
    padding: 6px 12px; font-size: 12px; border: 1px solid #ccc;
    border-radius: 4px; background: #fff; color: #333; cursor: pointer;
    transition: background 0.15s;
  `;

  function addButton(parent, label, onClick) {
    return parent
      .append("button")
      .attr("style", buttonStyle)
      .text(label)
      .on("click", onClick)
      .on("mouseover", function () { d3.select(this).style("background", "#f0f0f0"); })
      .on("mouseout", function () { d3.select(this).style("background", "#fff"); });
  }

  const statusText = { saved: "\u2713 Using saved layout", default: "Using balanced layout" };

  const status = toolbar
    .append("span")
    .style("font-size", "11px")
    .style("color", validatedLayout.source === "default" ? "#666" : "#2e7d32")
    .style("margin-left", "12px")
    .style("min-width", "180px")
    .text(statusText[validatedLayout.source] || statusText.default);

  const selectionStatus = toolbar
    .append("span")
    .style("font-size", "11px")
    .style("color", "#666")
    .style("margin-left", "12px")
    .text("");

  function showStatus(message, color, duration = 2000) {
    status.text(message).style("color", color);
    if (duration > 0) {
      setTimeout(() => {
        if (layoutModified) {
          status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
        } else {
          status
            .text(statusText[validatedLayout.source] || statusText.default)
            .style("color", validatedLayout.source === "default" ? "#666" : "#2e7d32");
        }
      }, duration);
    }
  }

  function updateSelectionStatus() {
    selectionStatus.text(
      selectedNodes.size === 0 ? "" : `${selectedNodes.size} selected (Esc to clear)`
    );
  }

  // --- Toolbar buttons ---
  addButton(toolbar, "\uD83D\uDCBE Save Layout", function () {
    try {
      const positions = {};
      chartData.nodes.forEach((n) => { positions[n.id] = { x: n.x, y: n.y }; });
      const payload = { positions, labelAnchors: currentAnchors, layoutName: currentLayoutName };
      localStorage.setItem(UNIFIED_LAYOUT_STORAGE_KEY, JSON.stringify(payload));
      layoutModified = false;
      showStatus("\u2713 Layout saved!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("\u2717 Save failed: " + e.message, "#c9190b", 3000);
    }
  });

  addButton(toolbar, "\u229E Balanced", function () {
    stopForce();
    const result = layouts.balancedLayout(chartData);
    applyLayout(result.positions, result.labelAnchors, "balanced");
    showStatus("\u229E Balanced layout applied (unsaved)", "#7c5e10", 3000);
  });

  addButton(toolbar, "\u2630 Sequential", function () {
    stopForce();
    const result = layouts.sequentialLayout(chartData);
    applyLayout(result.positions, result.labelAnchors, "sequential");
    showStatus("\u2630 Sequential layout applied (unsaved)", "#7c5e10", 3000);
  });

  const forceBtn = addButton(toolbar, "\u26A1 Force", function () {
    if (forceSimulation) {
      stopForce();
      showStatus("Force stopped", "#666", 2000);
    } else {
      startForce();
      showStatus(
        "\u26A1 Force active on " +
          (selectedNodes.size > 0 ? selectedNodes.size + " selected" : "all") +
          " nodes",
        "#7c5e10",
        0
      );
    }
  });

  addButton(toolbar, "\uD83D\uDCE4 Export", function () {
    try {
      const positions = {};
      chartData.nodes.forEach((n) => { positions[n.id] = { x: n.x, y: n.y }; });
      const payload = { positions, labelAnchors: currentAnchors, layoutName: currentLayoutName };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "unified-chart-layout.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showStatus("\u2713 Layout exported!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("\u2717 Export failed: " + e.message, "#c9190b", 3000);
    }
  });

  const fileInput = toolbar
    .append("input")
    .attr("type", "file")
    .attr("accept", ".json")
    .style("display", "none")
    .on("change", function () {
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          if (!imported.positions) throw new Error("Invalid layout: missing positions");
          localStorage.setItem(UNIFIED_LAYOUT_STORAGE_KEY, JSON.stringify(imported));
          showStatus("\u2713 Imported! Reloading...", "#2e7d32", 1000);
          setTimeout(() => location.reload(), 1000);
        } catch (err) {
          showStatus("\u2717 Import failed: " + err.message, "#c9190b", 3000);
        }
      };
      reader.readAsText(file);
    });

  addButton(toolbar, "\uD83D\uDCE5 Import", () => fileInput.node().click());

  addButton(toolbar, "\u2298 Clear", () => {
    selectedNodes.clear();
    updateSelectionVisuals();
    updateSelectionStatus();
  });

  addButton(toolbar, "\u21BA Reset", function () {
    try {
      localStorage.removeItem(UNIFIED_LAYOUT_STORAGE_KEY);
      location.reload();
    } catch (e) {
      showStatus("\u2717 Reset failed: " + e.message, "#c9190b", 3000);
    }
  });

  if (validatedLayout.stats.stale > 0 || validatedLayout.stats.newNodes > 0) {
    const parts = [];
    if (validatedLayout.stats.stale > 0) parts.push(`${validatedLayout.stats.stale} stale removed`);
    if (validatedLayout.stats.newNodes > 0) parts.push(`${validatedLayout.stats.newNodes} new (default pos)`);
    toolbar
      .append("span")
      .style("font-size", "11px")
      .style("color", "#7c5e10")
      .style("margin-left", "8px")
      .style("padding", "4px 8px")
      .style("background", "#fff8e1")
      .style("border-radius", "4px")
      .style("border", "1px solid #ffe082")
      .html(`\u27F3 Layout sync: ${parts.join(", ")}`);
  }

  // ── SVG + ZOOM ──
  const svg = container
    .append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("width", width)
    .attr("height", height)
    .style("background", "#fafafa")
    .style("font", "12px sans-serif")
    .style("user-select", "none");

  svg.append("style").text(`
    .node-label { fill: #333; font-size: 12px; pointer-events: none; user-select: none; }
    .category-label { fill: white; font-size: 14px; font-weight: bold; pointer-events: none; user-select: none; }
    .label-bg { fill: white; fill-opacity: 0.6; rx: 3; ry: 3; }
    .dragging { cursor: grabbing !important; }
    .selected circle, .selected rect, .selected path { filter: drop-shadow(0 0 3px #0066cc); }
    .marquee-hover circle, .marquee-hover rect, .marquee-hover path { filter: drop-shadow(0 0 2px #0066cc); opacity: 0.8; }
  `);

  const g = svg.append("g").attr("class", "main-container");

  const bgRect = g
    .append("rect")
    .attr("class", "marquee-bg")
    .attr("width", width * 4)
    .attr("height", height * 4)
    .attr("x", -width * 2)
    .attr("y", -height * 2)
    .attr("fill", "transparent");

  let currentTransform = d3.zoomIdentity;

  const zoom = d3
    .zoom()
    .scaleExtent([0.3, 3])
    .filter((event) => event.type === "wheel" || event.type === "dblclick")
    .on("zoom", (event) => {
      currentTransform = event.transform;
      g.attr("transform", event.transform);
    });
  svg.call(zoom);

  // ── Marquee selection ──
  const marquee = svg
    .append("rect")
    .attr("fill", "rgba(0, 102, 204, 0.1)")
    .attr("stroke", "#0066cc")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "4,2")
    .style("display", "none");

  let marqueeStart = null;
  let isMarqueeSelecting = false;

  bgRect.on("mousedown", function (event) {
    const [x, y] = d3.pointer(event, svg.node());
    marqueeStart = { x, y };
    isMarqueeSelecting = true;
    marquee.attr("x", x).attr("y", y).attr("width", 0).attr("height", 0).style("display", "block");
    if (!event.shiftKey) {
      selectedNodes.clear();
      updateSelectionVisuals();
    }
    event.preventDefault();
    event.stopPropagation();
  });

  d3.select(document)
    .on("mousemove.unifiedMarquee", function (event) {
      if (!isMarqueeSelecting || !marqueeStart) return;
      const [x, y] = d3.pointer(event, svg.node());
      const minX = Math.min(marqueeStart.x, x);
      const minY = Math.min(marqueeStart.y, y);
      marquee.attr("x", minX).attr("y", minY).attr("width", Math.abs(x - marqueeStart.x)).attr("height", Math.abs(y - marqueeStart.y));
    })
    .on("mouseup.unifiedMarquee", function (event) {
      if (!isMarqueeSelecting) return;
      const [x, y] = d3.pointer(event, svg.node());
      const minX = Math.min(marqueeStart.x, x);
      const minY = Math.min(marqueeStart.y, y);
      const w = Math.abs(x - marqueeStart.x);
      const h = Math.abs(y - marqueeStart.y);

      if (w > 5 || h > 5) {
        const mRect = {
          x1: (minX - currentTransform.x) / currentTransform.k,
          y1: (minY - currentTransform.y) / currentTransform.k,
          x2: (minX + w - currentTransform.x) / currentTransform.k,
          y2: (minY + h - currentTransform.y) / currentTransform.k
        };
        chartData.nodes.forEach((n) => {
          if (n.x >= mRect.x1 && n.x <= mRect.x2 && n.y >= mRect.y1 && n.y <= mRect.y2) {
            selectedNodes.add(n.id);
          }
        });
        updateSelectionVisuals();
        updateSelectionStatus();
      }

      marquee.style("display", "none");
      marqueeStart = null;
      isMarqueeSelecting = false;
    });

  bgRect.on("click", function (event) {
    if (!isMarqueeSelecting) {
      selectedNodes.clear();
      updateSelectionVisuals();
      updateSelectionStatus();
      dismissTooltip();
    }
  });

  d3.select("body").on("keydown.unifiedChart", function (event) {
    if (event.key === "Escape") {
      selectedNodes.clear();
      updateSelectionVisuals();
      updateSelectionStatus();
      dismissTooltip();
    }
  });

  // ── Links ──
  const linkGroup = g.append("g").attr("class", "links");
  const linkElements = linkGroup
    .selectAll("line")
    .data(chartData.links)
    .join("line")
    .attr("stroke", (d) => d.color)
    .attr("stroke-opacity", 0.5)
    .attr("stroke-width", (d) => (d.type === "category-technique" ? 2 : 1))
    .style("pointer-events", "none");

  function updateLinks() {
    linkElements
      .attr("x1", (d) => { const s = typeof d.source === "string" ? chartData.nodeById.get(d.source) : d.source; return s ? s.x : 0; })
      .attr("y1", (d) => { const s = typeof d.source === "string" ? chartData.nodeById.get(d.source) : d.source; return s ? s.y : 0; })
      .attr("x2", (d) => { const t = typeof d.target === "string" ? chartData.nodeById.get(d.target) : d.target; return t ? t.x : 0; })
      .attr("y2", (d) => { const t = typeof d.target === "string" ? chartData.nodeById.get(d.target) : d.target; return t ? t.y : 0; });
  }

  // ── Category nodes ──
  const nodeGroup = g.append("g").attr("class", "nodes");

  const categoryNodes = nodeGroup
    .selectAll(".category-node")
    .data(chartData.nodes.filter((n) => n.type === "category"))
    .join("g")
    .attr("class", "category-node")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab");

  categoryNodes.each(function (d) {
    const group = d3.select(this);
    group.append("rect")
      .attr("width", d.width).attr("height", d.height)
      .attr("x", -d.width / 2).attr("y", -d.height / 2)
      .attr("rx", config.categoryRadius).attr("ry", config.categoryRadius)
      .attr("fill", d.color).attr("stroke", "#fff").attr("stroke-width", 2);
    group.append("text")
      .attr("class", "category-label")
      .attr("text-anchor", "middle").attr("dy", "0.35em")
      .text(d.name);
  });

  // ── Technique nodes ──
  const techniqueNodes = nodeGroup
    .selectAll(".technique-node")
    .data(chartData.nodes.filter((n) => n.type === "technique"))
    .join("g")
    .attr("class", "technique-node")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab");

  techniqueNodes
    .append("path")
    .attr("d", d3.symbol().type(d3.symbolTriangle).size(config.techniqueSymbolSize))
    .attr("fill", (d) => (d.isOrphan ? "#e0e0e0" : d.color))
    .attr("stroke", (d) => (d.isOrphan ? "#999" : "#fff"))
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", (d) => (d.isOrphan ? "3,2" : "none"))
    .attr("opacity", (d) => (d.isOrphan ? 0.5 : 1));

  function renderTechniqueLabels() {
    techniqueNodes.selectAll(".label-group").remove();
    techniqueNodes.each(function (d) {
      const anchor = currentAnchors[d.id] || "start";
      const group = d3.select(this).append("g").attr("class", "label-group");

      let text;
      if (anchor === "middle") {
        text = group.append("text").attr("class", "node-label").attr("text-anchor", "middle").attr("x", 0).attr("y", 18).text(d.name);
      } else if (anchor === "end") {
        text = group.append("text").attr("class", "node-label").attr("text-anchor", "end").attr("x", -config.labelOffset).attr("y", 5).text(d.name);
      } else {
        text = group.append("text").attr("class", "node-label").attr("text-anchor", "start").attr("x", config.labelOffset).attr("y", 5).text(d.name);
      }

      const bbox = text.node().getBBox();
      group.insert("rect", "text").attr("class", "label-bg")
        .attr("x", bbox.x - 2).attr("y", bbox.y - 1)
        .attr("width", bbox.width + 4).attr("height", bbox.height + 2);

      if (d.isOrphan) {
        text.style("fill", "#999").style("font-style", "italic");
      }
    });
  }

  renderTechniqueLabels();

  // ── Provider nodes ──
  const providerNodes = nodeGroup
    .selectAll(".provider-node")
    .data(chartData.nodes.filter((n) => n.type === "provider"))
    .join("g")
    .attr("class", "provider-node")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab");

  providerNodes
    .append("circle")
    .attr("r", config.providerRadius)
    .attr("fill", (d) => d.color)
    .attr("stroke", "#fff")
    .attr("stroke-width", 2);

  function renderProviderLabels() {
    providerNodes.selectAll(".label-group").remove();
    providerNodes.each(function (d) {
      const anchor = currentAnchors[d.id] || "start";
      const group = d3.select(this).append("g").attr("class", "label-group");
      const text = group.append("text")
        .attr("class", "node-label")
        .attr("text-anchor", anchor)
        .attr("x", anchor === "start" ? config.labelOffset : -config.labelOffset)
        .attr("y", 5)
        .text(d.name);
      const bbox = text.node().getBBox();
      group.insert("rect", "text").attr("class", "label-bg")
        .attr("x", bbox.x - 2).attr("y", bbox.y - 1)
        .attr("width", bbox.width + 4).attr("height", bbox.height + 2);
    });
  }

  renderProviderLabels();

  // ── Drag ──
  function setupDrag(selection) {
    let dragStartPositions = new Map();

    selection.call(
      d3.drag()
        .on("start", function (event, d) {
          isDragging = true;
          dismissTooltip();
          if (!selectedNodes.has(d.id)) {
            if (!event.sourceEvent.shiftKey) selectedNodes.clear();
            selectedNodes.add(d.id);
            updateSelectionVisuals();
            updateSelectionStatus();
          }
          dragStartPositions.clear();
          selectedNodes.forEach((id) => {
            const node = chartData.nodeById.get(id);
            if (node) dragStartPositions.set(id, { x: node.x, y: node.y });
          });
          d3.select(this).raise().classed("dragging", true);
        })
        .on("drag", function (event, d) {
          const startPos = dragStartPositions.get(d.id);
          if (!startPos) return;
          const dx = event.x - startPos.x;
          const dy = event.y - startPos.y;

          selectedNodes.forEach((id) => {
            const node = chartData.nodeById.get(id);
            const nodeStart = dragStartPositions.get(id);
            if (node && nodeStart) {
              node.x = nodeStart.x + dx;
              node.y = nodeStart.y + dy;
            }
          });

          categoryNodes.filter((n) => selectedNodes.has(n.id)).attr("transform", (n) => `translate(${n.x},${n.y})`);
          techniqueNodes.filter((n) => selectedNodes.has(n.id)).attr("transform", (n) => `translate(${n.x},${n.y})`);
          providerNodes.filter((n) => selectedNodes.has(n.id)).attr("transform", (n) => `translate(${n.x},${n.y})`);

          updateLinks();

          if (!layoutModified) {
            layoutModified = true;
            status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
          }
        })
        .on("end", function () {
          d3.select(this).classed("dragging", false);
          dragStartPositions.clear();
          isDragging = false;
        })
    );
  }

  setupDrag(categoryNodes);
  setupDrag(techniqueNodes);
  setupDrag(providerNodes);

  // ── Click to select ──
  [categoryNodes, techniqueNodes, providerNodes].forEach((sel) => {
    sel.on("click", function (event, d) {
      event.stopPropagation();
      if (event.ctrlKey || event.shiftKey || event.metaKey) {
        if (selectedNodes.has(d.id)) selectedNodes.delete(d.id);
        else selectedNodes.add(d.id);
      } else {
        selectedNodes.clear();
        selectedNodes.add(d.id);
      }
      updateSelectionVisuals();
      updateSelectionStatus();
    });
  });

  // Link pointer-events disabled to allow marquee selection through links

  function showLinkTooltip(event, d, persistent = false) {
    hideLinkTooltip();
    const source = typeof d.source === "string" ? chartData.nodeById.get(d.source) : d.source;
    const target = typeof d.target === "string" ? chartData.nodeById.get(d.target) : d.target;
    if (!source || !target) return null;

    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "unified-link-tooltip")
      .style("position", "absolute")
      .style("text-align", "left")
      .style("padding", "10px")
      .style("font", "12px sans-serif")
      .style("background", "rgba(0, 0, 0, 0.95)")
      .style("color", "white")
      .style("border-radius", "4px")
      .style("max-width", "400px")
      .style("box-shadow", "0 4px 6px rgba(0,0,0,0.3)")
      .style("border", "1px solid #333")
      .style("pointer-events", persistent ? "auto" : "none")
      .style("z-index", 1000)
      .style("left", event.pageX + 10 + "px")
      .style("top", event.pageY - 28 + "px")
      .style("opacity", 0);

    if (d.data) {
      const sourceHtml = d.data.source_uri
        ? `<a href="${d.data.source_uri}" target="_blank" style="color: #64b5f6;">${d.data.source || "View Source"}</a>`
        : d.data.source || "Unknown";

      const evidenceTexts = d.data.evidenceTexts || [];
      let evidenceHtml = "";
      if (evidenceTexts.length > 0) {
        const snippets = evidenceTexts.map((txt) => {
          const display = txt.length > 200 ? txt.substring(0, 199) + "\u2026" : txt;
          return `<div style="font-style:italic;color:#ddd;line-height:1.4;margin-bottom:4px;">"\u201C${display}\u201D</div>`;
        });
        evidenceHtml = `<p style="margin:6px 0 4px 0;"><strong>Evidence (${evidenceTexts.length}):</strong></p>` + snippets.join("");
      }

      tooltip.html(
        `<h4 style="margin:0 0 8px 0;color:#ffa726;font-size:14px;">${source.name} \u2192 ${target.name}</h4>` +
        `<p style="margin:4px 0;"><strong>Source:</strong> ${sourceHtml}</p>` +
        `<p style="margin:4px 0;"><strong>Model(s):</strong> ${d.data.model || "N/A"}</p>` +
        evidenceHtml +
        `<div style="margin-top:8px;padding-top:6px;border-top:1px solid #555;"><strong>Confidence:</strong> ${d.data.confidence || "Unknown"}</div>`
      );
    } else {
      tooltip.html(`<h4 style="margin:0;color:#ffa726;">${source.name} \u2192 ${target.name}</h4>`);
    }

    tooltip.transition().duration(200).style("opacity", 0.95);
    return persistent ? tooltip : null;
  }

  function hideLinkTooltip() {
    if (!persistentTooltip) d3.selectAll(".unified-link-tooltip").remove();
  }

  function dismissTooltip() {
    if (persistentTooltip) {
      persistentTooltip.remove();
      persistentTooltip = null;
    }
    if (selectedLinkElement) {
      selectedLinkElement.attr("stroke-width", 1).attr("stroke-opacity", 0.5);
      selectedLinkElement = null;
    }
    d3.selectAll(".unified-link-tooltip").remove();
  }

  // ── Selection visuals ──
  function updateSelectionVisuals() {
    [categoryNodes, techniqueNodes, providerNodes].forEach((sel) => {
      sel.classed("selected", (d) => selectedNodes.has(d.id));
      sel.select("circle, rect, path")
        .attr("stroke", (d) => (selectedNodes.has(d.id) ? "#0066cc" : "#fff"))
        .attr("stroke-width", (d) => (selectedNodes.has(d.id) ? 3 : 2));
    });

    if (selectedNodes.size > 0) {
      linkElements.style("opacity", (d) => {
        const sId = typeof d.source === "string" ? d.source : d.source.id;
        const tId = typeof d.target === "string" ? d.target : d.target.id;
        return selectedNodes.has(sId) || selectedNodes.has(tId) ? 0.6 : 0.08;
      });
      [categoryNodes, techniqueNodes, providerNodes].forEach((sel) => {
        sel.style("opacity", (d) => (selectedNodes.has(d.id) ? 1 : 0.3));
      });
    } else {
      linkElements.style("opacity", 0.5);
      [categoryNodes, techniqueNodes, providerNodes].forEach((sel) => {
        sel.style("opacity", 1);
      });
    }
  }

  // ── Layout application ──
  function applyLayout(positions, labelAnchors, layoutName) {
    currentLayoutName = layoutName;
    currentAnchors = { ...labelAnchors };

    chartData.nodes.forEach((node) => {
      const pos = positions[node.id];
      if (pos) {
        node.x = pos.x;
        node.y = pos.y;
        node.fx = null;
        node.fy = null;
      }
    });

    categoryNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    techniqueNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    providerNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);

    renderTechniqueLabels();
    renderProviderLabels();
    updateLinks();

    layoutModified = true;
    status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
  }

  // ── Force simulation ──
  function startForce() {
    stopForce();
    forceSimulation = layouts.createForceSimulation(
      chartData.nodes, chartData.links, selectedNodes, chartData.nodeById
    );
    forceSimulation.on("tick", () => {
      categoryNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      techniqueNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      providerNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      updateLinks();
    });
    forceSimulation.alpha(1).restart();
    forceBtn.style("background", "#e0e0e0");
    layoutModified = true;
  }

  function stopForce() {
    if (forceSimulation) {
      forceSimulation.stop();
      chartData.nodes.forEach((n) => { n.fx = n.x; n.fy = n.y; });
      forceSimulation = null;
    }
    forceBtn.style("background", "#fff");
  }

  updateLinks();

  return container.node();
}
