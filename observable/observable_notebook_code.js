function _1(md) {
  return (
    md`# LLM Safety Mechanisms Explorer

This project supports holistic analysis of Large Language Model safety mechanisms, using data from my [LLM Safety Mechanisms GitHub repository](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms). Please raise any issues/suggestions via GitHub.

## Why do we need it?
_Understanding which safety mechanisms are implemented across large language models currently requires piecing together information from scattered documentation, each using different terminology and varying levels of detail. This work will provides a structured, queryable view of safety technique coverage across major frontier models - as a coverage profile that assists researchers, practitioners, and policymakers to make informed risk assessments._`
  )
}

function _2(md) {
  return (
    md`## Provider-Technique Relationships
This is designed to support coverage analysis. Use the filter below this graph to reduce the dataset for improved clarity. You can apply force layout on selected subsets of nodes. `
  )
}

function _unifiedChart(unifiedChartData, unifiedChartConfig, unifiedChartLayouts, unifiedChartValidatedLayout, d3, localStorage, unifiedLayoutStorageKey, location) {
  const chartData = unifiedChartData;
  const config = unifiedChartConfig;
  const layouts = unifiedChartLayouts;
  const validatedLayout = unifiedChartValidatedLayout;
  const { width, height } = config;

  // --- Apply initial positions from validated layout ---
  let currentLayoutName = validatedLayout.layoutName;
  let currentAnchors = { ...validatedLayout.labelAnchors };

  chartData.nodes.forEach((node) => {
    const pos = validatedLayout.positions[node.id];
    if (pos) {
      node.x = pos.x;
      node.y = pos.y;
    }
  });

  // --- State ---
  const selectedNodes = new Set();
  let forceSimulation = null;
  let layoutModified = false;
  let persistentTooltip = null;
  let selectedLinkElement = null;
  let isDragging = false;

  // ── Container ──
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
    border-radius: 4px; background: #fff; cursor: pointer;
    transition: background 0.15s;
  `;

  function addButton(parent, label, onClick) {
    return parent
      .append("button")
      .attr("style", buttonStyle)
      .text(label)
      .on("click", onClick)
      .on("mouseover", function () {
        d3.select(this).style("background", "#f0f0f0");
      })
      .on("mouseout", function () {
        d3.select(this).style("background", "#fff");
      });
  }

  const statusText = {
    saved: "✓ Using saved layout",
    default: "Using balanced layout"
  };

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
          status.text("⚠ Unsaved changes").style("color", "#c9190b");
        } else {
          status
            .text(statusText[validatedLayout.source] || statusText.default)
            .style(
              "color",
              validatedLayout.source === "default" ? "#666" : "#2e7d32"
            );
        }
      }, duration);
    }
  }

  function updateSelectionStatus() {
    selectionStatus.text(
      selectedNodes.size === 0
        ? ""
        : `${selectedNodes.size} selected (Esc to clear)`
    );
  }

  // --- Save ---
  addButton(toolbar, "💾 Save Layout", function () {
    try {
      const positions = {};
      chartData.nodes.forEach((n) => {
        positions[n.id] = { x: n.x, y: n.y };
      });
      const payload = {
        positions,
        labelAnchors: currentAnchors,
        layoutName: currentLayoutName
      };
      localStorage.setItem(unifiedLayoutStorageKey, JSON.stringify(payload));
      layoutModified = false;
      showStatus("✓ Layout saved!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("✗ Save failed: " + e.message, "#c9190b", 3000);
    }
  });

  // --- Balanced Layout ---
  addButton(toolbar, "⊞ Balanced", function () {
    stopForce();
    const result = layouts.balancedLayout(chartData);
    applyLayout(result.positions, result.labelAnchors, "balanced");
    showStatus("⊞ Balanced layout applied (unsaved)", "#7c5e10", 3000);
  });

  // --- Sequential Layout ---
  addButton(toolbar, "☰ Sequential", function () {
    stopForce();
    const result = layouts.sequentialLayout(chartData);
    applyLayout(result.positions, result.labelAnchors, "sequential");
    showStatus("☰ Sequential layout applied (unsaved)", "#7c5e10", 3000);
  });

  // --- Force ---
  const forceBtn = addButton(toolbar, "⚡ Force", function () {
    if (forceSimulation) {
      stopForce();
      showStatus("Force stopped", "#666", 2000);
    } else {
      startForce();
      showStatus(
        "⚡ Force active on " +
        (selectedNodes.size > 0 ? selectedNodes.size + " selected" : "all") +
        " nodes",
        "#7c5e10",
        0
      );
    }
  });

  // --- Export ---
  addButton(toolbar, "📤 Export", function () {
    try {
      const positions = {};
      chartData.nodes.forEach((n) => {
        positions[n.id] = { x: n.x, y: n.y };
      });
      const payload = {
        positions,
        labelAnchors: currentAnchors,
        layoutName: currentLayoutName
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: "application/json"
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "unified-chart-layout.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showStatus("✓ Layout exported!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("✗ Export failed: " + e.message, "#c9190b", 3000);
    }
  });

  // --- Import ---
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
          if (!imported.positions)
            throw new Error("Invalid layout: missing positions");
          localStorage.setItem(
            unifiedLayoutStorageKey,
            JSON.stringify(imported)
          );
          showStatus("✓ Imported! Reloading...", "#2e7d32", 1000);
          setTimeout(() => location.reload(), 1000);
        } catch (err) {
          showStatus("✗ Import failed: " + err.message, "#c9190b", 3000);
        }
      };
      reader.readAsText(file);
    });

  addButton(toolbar, "📥 Import", () => fileInput.node().click());

  // --- Clear Selection ---
  addButton(toolbar, "⊘ Clear", () => {
    selectedNodes.clear();
    updateSelectionVisuals();
    updateSelectionStatus();
  });

  // --- Reset ---
  addButton(toolbar, "↺ Reset", function () {
    try {
      localStorage.removeItem(unifiedLayoutStorageKey);
      location.reload();
    } catch (e) {
      showStatus("✗ Reset failed: " + e.message, "#c9190b", 3000);
    }
  });

  // Layout sync stats
  if (validatedLayout.stats.stale > 0 || validatedLayout.stats.newNodes > 0) {
    const parts = [];
    if (validatedLayout.stats.stale > 0)
      parts.push(`${validatedLayout.stats.stale} stale removed`);
    if (validatedLayout.stats.newNodes > 0)
      parts.push(`${validatedLayout.stats.newNodes} new (default pos)`);
    toolbar
      .append("span")
      .style("font-size", "11px")
      .style("color", "#7c5e10")
      .style("margin-left", "8px")
      .style("padding", "4px 8px")
      .style("background", "#fff8e1")
      .style("border-radius", "4px")
      .style("border", "1px solid #ffe082")
      .html(`⟳ Layout sync: ${parts.join(", ")}`);
  }

  // ══════════════════════════════════════════════════════
  //  SVG + ZOOM
  // ══════════════════════════════════════════════════════
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

  // Invisible background rect to capture mouse events on empty space
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

  // ── Marquee selection (bound to background rect directly) ──
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
    marquee
      .attr("x", x)
      .attr("y", y)
      .attr("width", 0)
      .attr("height", 0)
      .style("display", "block");
    if (!event.shiftKey) {
      selectedNodes.clear();
      updateSelectionVisuals();
    }
    event.preventDefault();
    event.stopPropagation();
  });

  // Use document-level mousemove/mouseup so marquee tracks even outside the SVG
  d3.select(document)
    .on("mousemove.unifiedMarquee", function (event) {
      if (!isMarqueeSelecting || !marqueeStart) return;
      const [x, y] = d3.pointer(event, svg.node());
      const minX = Math.min(marqueeStart.x, x);
      const minY = Math.min(marqueeStart.y, y);
      const w = Math.abs(x - marqueeStart.x);
      const h = Math.abs(y - marqueeStart.y);
      marquee
        .attr("x", minX)
        .attr("y", minY)
        .attr("width", w)
        .attr("height", h);
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
          if (
            n.x >= mRect.x1 &&
            n.x <= mRect.x2 &&
            n.y >= mRect.y1 &&
            n.y <= mRect.y2
          ) {
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

  // Click on background to clear selection
  bgRect.on("click", function (event) {
    if (!isMarqueeSelecting) {
      selectedNodes.clear();
      updateSelectionVisuals();
      updateSelectionStatus();
      dismissTooltip();
    }
  });

  // Keyboard
  d3.select("body").on("keydown.unifiedChart", function (event) {
    if (event.key === "Escape") {
      selectedNodes.clear();
      updateSelectionVisuals();
      updateSelectionStatus();
      dismissTooltip();
    }
  });

  // ══════════════════════════════════════════════════════
  //  RENDER: Links
  // ══════════════════════════════════════════════════════
  const linkGroup = g.append("g").attr("class", "links");
  const linkElements = linkGroup
    .selectAll("line")
    .data(chartData.links)
    .join("line")
    .attr("stroke", (d) => d.color)
    .attr("stroke-opacity", 0.5)
    .attr("stroke-width", (d) => (d.type === "category-technique" ? 2 : 1))
    .style("cursor", "pointer");

  function updateLinks() {
    linkElements
      .attr("x1", (d) => {
        const s =
          typeof d.source === "string"
            ? chartData.nodeById.get(d.source)
            : d.source;
        return s ? s.x : 0;
      })
      .attr("y1", (d) => {
        const s =
          typeof d.source === "string"
            ? chartData.nodeById.get(d.source)
            : d.source;
        return s ? s.y : 0;
      })
      .attr("x2", (d) => {
        const t =
          typeof d.target === "string"
            ? chartData.nodeById.get(d.target)
            : d.target;
        return t ? t.x : 0;
      })
      .attr("y2", (d) => {
        const t =
          typeof d.target === "string"
            ? chartData.nodeById.get(d.target)
            : d.target;
        return t ? t.y : 0;
      });
  }

  // ══════════════════════════════════════════════════════
  //  RENDER: Nodes
  // ══════════════════════════════════════════════════════
  const nodeGroup = g.append("g").attr("class", "nodes");

  // --- Categories ---
  const categoryNodes = nodeGroup
    .selectAll(".category-node")
    .data(chartData.nodes.filter((n) => n.type === "category"))
    .join("g")
    .attr("class", "category-node")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab");

  categoryNodes.each(function (d) {
    const group = d3.select(this);
    group
      .append("rect")
      .attr("width", d.width)
      .attr("height", d.height)
      .attr("x", -d.width / 2)
      .attr("y", -d.height / 2)
      .attr("rx", config.categoryRadius)
      .attr("ry", config.categoryRadius)
      .attr("fill", d.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);
    group
      .append("text")
      .attr("class", "category-label")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .text(d.name);
  });

  // ══════════════════════════════════════════════════════
  //  RENDER: Technique nodes
  // ══════════════════════════════════════════════════════
  // --- Techniques ---
  const techniqueNodes = nodeGroup
    .selectAll(".technique-node")
    .data(chartData.nodes.filter((n) => n.type === "technique"))
    .join("g")
    .attr("class", "technique-node")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab");

  techniqueNodes
    .append("path")
    .attr(
      "d",
      d3.symbol().type(d3.symbolTriangle).size(config.techniqueSymbolSize)
    )
    .attr("fill", (d) => (d.isOrphan ? "#e0e0e0" : d.color))
    .attr("stroke", (d) => (d.isOrphan ? "#999" : "#fff"))
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", (d) => (d.isOrphan ? "3,2" : "none"))
    .attr("opacity", (d) => (d.isOrphan ? 0.5 : 1));

  // --- Technique labels (position depends on layout) ---
  function renderTechniqueLabels() {
    techniqueNodes.selectAll(".label-group").remove();
    techniqueNodes.each(function (d) {
      const anchor = currentAnchors[d.id] || "start";
      const group = d3.select(this).append("g").attr("class", "label-group");

      let text;
      if (anchor === "middle") {
        // Sequential layout: text below, centered
        text = group
          .append("text")
          .attr("class", "node-label")
          .attr("text-anchor", "middle")
          .attr("x", 0)
          .attr("y", 18)
          .text(d.name);
      } else if (anchor === "end") {
        // Left side: text right-aligned, adjacent to LEFT of node
        text = group
          .append("text")
          .attr("class", "node-label")
          .attr("text-anchor", "end")
          .attr("x", -config.labelOffset)
          .attr("y", 5)
          .text(d.name);
      } else {
        // Right side: text left-aligned, adjacent to RIGHT of node
        text = group
          .append("text")
          .attr("class", "node-label")
          .attr("text-anchor", "start")
          .attr("x", config.labelOffset)
          .attr("y", 5)
          .text(d.name);
      }

      const bbox = text.node().getBBox();
      group
        .insert("rect", "text")
        .attr("class", "label-bg")
        .attr("x", bbox.x - 2)
        .attr("y", bbox.y - 1)
        .attr("width", bbox.width + 4)
        .attr("height", bbox.height + 2);

      // Dim orphan technique labels
      if (d.isOrphan) {
        text.style("fill", "#999").style("font-style", "italic");
      }
    });
  }

  renderTechniqueLabels();

  // ══════════════════════════════════════════════════════
  //  RENDER: Provider nodes
  // ══════════════════════════════════════════════════════
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

  // Provider labels
  function renderProviderLabels() {
    providerNodes.selectAll(".label-group").remove();
    providerNodes.each(function (d) {
      const anchor = currentAnchors[d.id] || "start";
      const group = d3.select(this).append("g").attr("class", "label-group");
      const text = group
        .append("text")
        .attr("class", "node-label")
        .attr("text-anchor", anchor)
        .attr(
          "x",
          anchor === "start" ? config.labelOffset : -config.labelOffset
        )
        .attr("y", 5)
        .text(d.name);
      const bbox = text.node().getBBox();
      group
        .insert("rect", "text")
        .attr("class", "label-bg")
        .attr("x", bbox.x - 2)
        .attr("y", bbox.y - 1)
        .attr("width", bbox.width + 4)
        .attr("height", bbox.height + 2);
    });
  }

  renderProviderLabels();

  // ══════════════════════════════════════════════════════
  //  INTERACTIONS: Drag
  // ══════════════════════════════════════════════════════
  function setupDrag(selection) {
    let dragStartPositions = new Map();

    selection.call(
      d3
        .drag()
        .on("start", function (event, d) {
          isDragging = true;
          dismissTooltip();
          if (!selectedNodes.has(d.id)) {
            // Dragging an unselected node: clear others unless shift held
            if (!event.sourceEvent.shiftKey) selectedNodes.clear();
            selectedNodes.add(d.id);
            updateSelectionVisuals();
            updateSelectionStatus();
          }
          // If node is already selected, preserve the full selection for group drag
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

          categoryNodes
            .filter((n) => selectedNodes.has(n.id))
            .attr("transform", (n) => `translate(${n.x},${n.y})`);
          techniqueNodes
            .filter((n) => selectedNodes.has(n.id))
            .attr("transform", (n) => `translate(${n.x},${n.y})`);
          providerNodes
            .filter((n) => selectedNodes.has(n.id))
            .attr("transform", (n) => `translate(${n.x},${n.y})`);

          updateLinks();

          if (!layoutModified) {
            layoutModified = true;
            status.text("⚠ Unsaved changes").style("color", "#c9190b");
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

  // ══════════════════════════════════════════════════════
  //  INTERACTIONS: Click to select
  // ══════════════════════════════════════════════════════
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

  // ══════════════════════════════════════════════════════
  //  INTERACTIONS: Link tooltips
  // ══════════════════════════════════════════════════════
  linkElements
    .on("pointerover", function (event, d) {
      if (persistentTooltip || d.type !== "provider-technique") return;
      d3.select(this).attr("stroke-width", 3).attr("stroke-opacity", 0.8);
      showLinkTooltip(event, d);
    })
    .on("pointerout", function (event, d) {
      if (persistentTooltip) return;
      d3.select(this)
        .attr("stroke-width", d.type === "category-technique" ? 2 : 1)
        .attr("stroke-opacity", 0.5);
      hideLinkTooltip();
    })
    .on("click", function (event, d) {
      if (d.type !== "provider-technique") return;
      event.stopPropagation();
      dismissTooltip();
      selectedLinkElement = d3.select(this);
      selectedLinkElement.attr("stroke-width", 3).attr("stroke-opacity", 0.8);
      persistentTooltip = showLinkTooltip(event, d, true);
    });

  function showLinkTooltip(event, d, persistent = false) {
    hideLinkTooltip();
    const source =
      typeof d.source === "string"
        ? chartData.nodeById.get(d.source)
        : d.source;
    const target =
      typeof d.target === "string"
        ? chartData.nodeById.get(d.target)
        : d.target;
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
        ? `<a href="${d.data.source_uri
        }" target="_blank" style="color: #64b5f6;">${d.data.source || "View Source"
        }</a>`
        : d.data.source || "Unknown";

      // Build evidence snippets HTML from normalised array
      const evidenceTexts = d.data.evidenceTexts || [];
      let evidenceHtml = "";
      if (evidenceTexts.length > 0) {
        const snippets = evidenceTexts.map((txt) => {
          const display = txt.length > 200 ? txt.substring(0, 199) + "…" : txt;
          return `<div style="font-style:italic;color:#ddd;line-height:1.4;margin-bottom:4px;">"${display}"</div>`;
        });
        evidenceHtml =
          `<p style="margin:6px 0 4px 0;"><strong>Evidence (${evidenceTexts.length}):</strong></p>` +
          snippets.join("");
      }

      tooltip.html(
        `<h4 style="margin:0 0 8px 0;color:#ffa726;font-size:14px;">${source.name} → ${target.name}</h4>` +
        `<p style="margin:4px 0;"><strong>Source:</strong> ${sourceHtml}</p>` +
        `<p style="margin:4px 0;"><strong>Model(s):</strong> ${d.data.model || "N/A"
        }</p>` +
        evidenceHtml +
        `<div style="margin-top:8px;padding-top:6px;border-top:1px solid #555;"><strong>Confidence:</strong> ${d.data.confidence || "Unknown"
        }</div>`
      );
    } else {
      tooltip.html(
        `<h4 style="margin:0;color:#ffa726;">${source.name} → ${target.name}</h4>`
      );
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

  // ══════════════════════════════════════════════════════
  //  SELECTION VISUALS
  // ══════════════════════════════════════════════════════
  function updateSelectionVisuals() {
    [categoryNodes, techniqueNodes, providerNodes].forEach((sel) => {
      sel.classed("selected", (d) => selectedNodes.has(d.id));
      sel
        .select("circle, rect, path")
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

  // ══════════════════════════════════════════════════════
  //  LAYOUT APPLICATION
  // ══════════════════════════════════════════════════════
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
    status.text("⚠ Unsaved changes").style("color", "#c9190b");
  }

  // ══════════════════════════════════════════════════════
  //  FORCE SIMULATION (selection-only)
  // ══════════════════════════════════════════════════════
  function startForce() {
    stopForce();
    forceSimulation = layouts.createForceSimulation(
      chartData.nodes,
      chartData.links,
      selectedNodes,
      chartData.nodeById
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
      chartData.nodes.forEach((n) => {
        n.fx = n.x;
        n.fy = n.y;
      });
      forceSimulation = null;
    }
    forceBtn.style("background", "#fff");
  }

  // ══════════════════════════════════════════════════════
  //  INITIAL LINK POSITIONS
  // ══════════════════════════════════════════════════════
  updateLinks();

  return container.node();
}


function _4(md) {
  return (
    md`## Dataset Filter
Constrain the collection using the following tools.`
  )
}

function _filters(data, html, d3) {
  // --- DATA PREPARATION START ---
  // 1. Extract Providers from the data.flatPairs (which contains the live connections)
  // We format them as {id, name} objects to match your template code.
  const uniqueProviders = Array.from(
    new Set(data.flatPairs.map((d) => d.provider))
  )
    .filter((p) => p) // Remove nulls
    .sort()
    .map((p) => ({ id: p, name: p }));

  // 2. Prepare Categories Lookup
  const catMap = new Map(data.categories.map((c) => [c.id, c.name]));

  // 3. Enrich Techniques with 'category_name' so your grouping logic works
  const techniquesWithCategories = data.techniques.map((t) => ({
    id: t.id,
    name: t.name,
    category_name: catMap.get(t.categoryId) || "Uncategorized"
  }));
  // --- DATA PREPARATION END ---

  const form = html`<div style="background: #f8f9fa; border-radius: 8px; padding: 10px; margin-bottom: 10px; font-family: sans-serif;">
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 10px;">
      
      <div>
        <h4 style="margin-top: 0; color: #333;">Providers</h4>
        <div style="max-height: 250px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
          ${uniqueProviders
      .map(
        (provider) =>
          `<label style="display: block; margin-bottom: 8px; cursor: pointer;">
              <input type="checkbox" name="providers" value="${provider.id}" style="margin-right: 8px;">
              <span style="font-size: 12px;">${provider.name}</span>
            </label>`
      )
      .join("")}
        </div>
        <div style="margin-top: 10px;">
          <button type="button" id="select-all-providers" style="font-size: 11px; padding: 4px 5px; margin-right: 5px;">Select All</button>
          <button type="button" id="clear-providers" style="font-size: 11px; padding: 4px 5px;">Clear All</button>
        </div>
      </div>
      
      <div>
        <h4 style="margin-top: 0; color: #333;">Categories & Techniques</h4>
        <div style="max-height: 250px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
          ${(() => {
      // Group techniques by category
      const techniquesByCategory = new Map();
      techniquesWithCategories.forEach((technique) => {
        const categoryName = technique.category_name || "Other";
        if (!techniquesByCategory.has(categoryName)) {
          techniquesByCategory.set(categoryName, []);
        }
        techniquesByCategory.get(categoryName).push(technique);
      });

      // Sort categories and techniques
      const sortedCategories = Array.from(
        techniquesByCategory.entries()
      ).sort(([a], [b]) => a.localeCompare(b));

      return sortedCategories
        .map(([categoryName, techniques], categoryIndex) => {
          // Use D3 for colors if available, else simple fallback
          const categoryColor =
            typeof d3 !== "undefined"
              ? d3
                .scaleOrdinal(d3.schemeTableau10)
                .domain(Array.from(techniquesByCategory.keys()))(
                  categoryName
                )
              : "#333";

          const categoryId = `category-${categoryIndex}`;

          return `
                <div style="margin-bottom: 5px; border-left: 4px solid ${categoryColor}; padding-left: 5px;">
                  <label style="display: block; font-weight: bold; cursor: pointer; margin-bottom: 5px;">
                    <input type="checkbox" name="categories" value="${categoryName}" id="${categoryId}" style="margin-right: 8px;">
                    <span style="color: ${categoryColor}; font-size: 12px;">${categoryName}</span>
                    <span style="color: #666; font-size: 11px; font-weight: normal;"> (${techniques.length
            })</span>
                  </label>
                  <div style="margin-left: 10px;">
                    ${techniques
              .sort((a, b) => a.name.localeCompare(b.name))
              .map(
                (technique) =>
                  `<label style="display: block; margin: 0 0 4px 0; padding: 0; cursor: pointer;">
                        <input type="checkbox" name="techniques" value="${technique.name}" data-category="${categoryName}" style="margin-right: 5px;">
                        <span style="font-size: 12px; color: #555;">${technique.name}</span>
                      </label>`
              )
              .join("")}
                  </div>
                </div>
              `;
        })
        .join("");
    })()}
        </div>
        <div style="margin-top: 5px;">
          <button type="button" id="select-all-categories" style="font-size: 11px; padding: 4px 5px; margin-right: 5px;">Select All Categories</button>
          <button type="button" id="clear-categories" style="font-size: 11px; padding: 4px 5px;">Clear All</button>
        </div>
      </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;">
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Minimum Confidence</label>
        <input name="rating" type="range" min="0" max="3" step="1" value="0" style="width: 100%;">
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888;">
             <span>All</span><span>Low</span><span>Med</span><span>High</span>
        </div>
        <span style="font-size: 11px; color: #666;">Current: <span id="rating-value">All</span></span>
      </div>
      
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Search</label>
        <input name="search" type="text" placeholder="Search evidence descriptions, summaries..." style="width: 100%; padding: 8px;">
      </div>
    </div>
    
    <div style="margin-top: 5px; text-align: center;">
      <button type="button" id="clear-all" style="padding: 5px 10px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Clear All Filters
      </button>
    </div>
    
    <div style="margin-top: 5px; font-size: 11px; color: #666; border-top: 1px solid #ddd; padding-top: 5px;">
      <strong>Selected:</strong> 
      <span id="selection-summary">No filters applied</span>
    </div>
  </div>`;

  // Helper functions
  const getSelectedValues = (name) => {
    return Array.from(
      form.querySelectorAll(`input[name="${name}"]:checked`)
    ).map((input) => input.value);
  };

  const getSelectedText = (name) => {
    return Array.from(
      form.querySelectorAll(`input[name="${name}"]:checked`)
    ).map((input) => {
      const label = input.closest("label").textContent.trim();
      return label.split("(")[0].trim(); // Remove count from category names
    });
  };

  // Rating display update
  const ratingSpan = form.querySelector("#rating-value");
  const ratingInput = form.querySelector('input[name="rating"]');
  const ratingLabels = { 0: "All", 1: "Low+", 2: "Medium+", 3: "High" };

  ratingInput.addEventListener("input", () => {
    ratingSpan.textContent = ratingLabels[ratingInput.value];
    updateSummary();
    // Dispatch input immediately so charts update while dragging
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  // Category checkbox logic - when category is checked, check all its techniques
  form
    .querySelectorAll('input[name="categories"]')
    .forEach((categoryCheckbox) => {
      categoryCheckbox.addEventListener("change", (e) => {
        const categoryName = e.target.value;
        const isChecked = e.target.checked;

        // Find all technique checkboxes for this category
        const techniqueCheckboxes = form.querySelectorAll(
          `input[name="techniques"][data-category="${categoryName}"]`
        );
        techniqueCheckboxes.forEach((checkbox) => {
          checkbox.checked = isChecked;
        });

        updateSummary();
        form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
      });
    });

  // Technique checkbox logic - update category checkbox state
  form
    .querySelectorAll('input[name="techniques"]')
    .forEach((techniqueCheckbox) => {
      techniqueCheckbox.addEventListener("change", (e) => {
        const categoryName = e.target.dataset.category;
        const categoryCheckbox = form.querySelector(
          `input[name="categories"][value="${categoryName}"]`
        );

        // Check if all techniques in this category are selected
        const allTechniques = form.querySelectorAll(
          `input[name="techniques"][data-category="${categoryName}"]`
        );
        const checkedTechniques = form.querySelectorAll(
          `input[name="techniques"][data-category="${categoryName}"]:checked`
        );

        if (checkedTechniques.length === allTechniques.length) {
          categoryCheckbox.checked = true;
          categoryCheckbox.indeterminate = false;
        } else if (checkedTechniques.length === 0) {
          categoryCheckbox.checked = false;
          categoryCheckbox.indeterminate = false;
        } else {
          categoryCheckbox.checked = false;
          categoryCheckbox.indeterminate = true;
        }

        updateSummary();
        form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
      });
    });

  // Button event listeners
  form.querySelector("#select-all-providers").addEventListener("click", () => {
    form
      .querySelectorAll('input[name="providers"]')
      .forEach((cb) => (cb.checked = true));
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  form.querySelector("#clear-providers").addEventListener("click", () => {
    form
      .querySelectorAll('input[name="providers"]')
      .forEach((cb) => (cb.checked = false));
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  form.querySelector("#select-all-categories").addEventListener("click", () => {
    form
      .querySelectorAll('input[name="categories"], input[name="techniques"]')
      .forEach((cb) => (cb.checked = true));
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  form.querySelector("#clear-categories").addEventListener("click", () => {
    form
      .querySelectorAll('input[name="categories"], input[name="techniques"]')
      .forEach((cb) => {
        cb.checked = false;
        cb.indeterminate = false;
      });
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  form.querySelector("#clear-all").addEventListener("click", () => {
    form.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = false;
      cb.indeterminate = false;
    });
    ratingInput.value = 0;
    ratingSpan.textContent = "All";
    form.querySelector('input[name="search"]').value = "";
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  // Update selection summary
  const updateSummary = () => {
    const selectedProviders = getSelectedText("providers");
    const selectedCategories = getSelectedText("categories");
    const selectedTechniques = getSelectedText("techniques");
    const minRating = parseFloat(ratingInput.value);
    const searchTerm = form.querySelector('input[name="search"]').value;

    const summaryParts = [];

    if (selectedProviders.length > 0) {
      summaryParts.push(`Providers: ${selectedProviders.join(", ")}`);
    }
    if (selectedCategories.length > 0) {
      summaryParts.push(`Categories: ${selectedCategories.join(", ")}`);
    }
    if (selectedTechniques.length > 0) {
      summaryParts.push(`Techniques: ${selectedTechniques.length} selected`);
    }
    if (minRating > 0) {
      summaryParts.push(`Min Confidence: ${ratingLabels[minRating]}`);
    }
    if (searchTerm) {
      summaryParts.push(`Search: "${searchTerm}"`);
    }

    form.querySelector("#selection-summary").textContent =
      summaryParts.length > 0 ? summaryParts.join(" | ") : "No filters applied";
  };

  // Search input listener
  form.querySelector('input[name="search"]').addEventListener("input", () => {
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  // Initialize form value
  form.value = {
    providers: [],
    categories: [],
    techniques: [],
    rating: 0,
    search: ""
  };

  // Update form value when inputs change
  form.addEventListener("input", () => {
    form.value = {
      providers: getSelectedValues("providers"),
      categories: getSelectedValues("categories"),
      techniques: getSelectedValues("techniques"), // These are now Technique Names
      rating: parseFloat(ratingInput.value) || 0,
      search: form.querySelector('input[name="search"]').value || ""
    };
  });

  updateSummary();
  return form;
}


function _6(md) {
  return (
    md`## Safety Mechanisms by Category
This chart provides a visual overview of the safety mechanisms documented in this project. The Categories and individual have techniques have been defined as a common taxonomy across the set of providers over months of iteration and analysis. This has been a data-driven approach, collapsing members where there was high overlap. I've also removed life cycle stage as higher order categories, and these are now represented intersectionally with techniques in a different section of the dataset.`
  )
}

function _sunburstChart(data, filteredData, d3, categoryColors) {
  const width = 928;
  const radius = width / 2;

  // --- DATA ADAPTER START ---
  const catLookup = new Map();
  data.categories.forEach((c) => {
    catLookup.set(c.id, c.name);
  });

  const hierarchyData = {
    name: "Safety Mechanisms",
    children: []
  };

  const techniquesByCategory = new Map();

  data.techniques.forEach((technique) => {
    const categoryName = catLookup.get(technique.categoryId) || "Other";
    if (!techniquesByCategory.has(categoryName)) {
      techniquesByCategory.set(categoryName, []);
    }
    techniquesByCategory.get(categoryName).push(technique);
  });

  Array.from(techniquesByCategory.entries()).forEach(
    ([categoryName, techniques]) => {
      const categoryNode = {
        name: categoryName,
        children: []
      };

      techniques.forEach((technique) => {
        const evidenceForTechnique = filteredData.filter(
          (d) => d.technique === technique.name
        );

        const implementingProviders = [
          ...new Set(evidenceForTechnique.map((d) => d.provider))
        ];

        const scoreMap = { High: 3, Medium: 2, Low: 1, Unknown: 0 };
        const avgEffectiveness =
          evidenceForTechnique.length > 0
            ? evidenceForTechnique.reduce(
              (sum, d) => sum + (scoreMap[d.confidence] || 0),
              0
            ) / evidenceForTechnique.length
            : 0;

        categoryNode.children.push({
          name: technique.name,
          // UPDATED: Set value to 1 to ensure equal angles for all techniques
          value: 1,
          providers: implementingProviders,
          providerCount: implementingProviders.length,
          evidenceCount: evidenceForTechnique.length, // Kept for tooltips & labels
          avgEffectiveness: avgEffectiveness,
          technique: technique,
          category: categoryName
        });
      });

      categoryNode.children.sort((a, b) => a.name.localeCompare(b.name));

      if (categoryNode.children.length > 0) {
        hierarchyData.children.push(categoryNode);
      }
    }
  );

  hierarchyData.children.sort((a, b) => a.name.localeCompare(b.name));
  // --- DATA ADAPTER END ---

  const hierarchy = d3
    .hierarchy(hierarchyData)
    .sum((d) => d.value || 0)
    .sort((a, b) => a.data.name.localeCompare(b.data.name));

  const partition = d3.partition().size([2 * Math.PI, radius]);
  partition(hierarchy);

  const innerRadius = 3;
  const ringWidth = (radius - innerRadius) / 2;

  const arc = d3
    .arc()
    .startAngle((d) => d.x0)
    .endAngle((d) => d.x1)
    .innerRadius((d) => {
      if (d.depth === 0) return 0;
      if (d.depth === 1) return innerRadius;
      return innerRadius + ringWidth;
    })
    .outerRadius((d) => {
      if (d.depth === 0) return innerRadius;
      if (d.depth === 1) return innerRadius + ringWidth;
      return radius;
    });

  const color = d3
    .scaleOrdinal()
    .domain(Object.keys(categoryColors))
    .range(Object.values(categoryColors));

  const svg = d3
    .create("svg")
    .attr("viewBox", [-width / 2, -width / 2, width, width])
    .style("font", "18px sans-serif");

  const g = svg.selectAll("g").data(hierarchy.descendants()).join("g");

  const path = g
    .append("path")
    .attr("fill", (d) => {
      if (d.depth === 0) return "#f0f0f0";
      let node = d;
      while (node.depth > 1) node = node.parent;
      return color(node.data.name);
    })
    .attr("fill-opacity", (d) => {
      if (d.depth === 0) return 1;
      if (d.depth === 2) return 0.6;
      return 1;
    })
    .attr("stroke", "#fff")
    .attr("stroke-width", 1)
    .attr("d", arc)
    .style("cursor", (d) => (d.depth > 0 ? "pointer" : "default"));

  path.append("title").text((d) => {
    if (d.depth === 0) return "Safety Mechanisms Overview";
    if (d.depth === 1) {
      const techniqueCount = d.data.children.length;
      const totalEvidence = d.data.children.reduce(
        (sum, child) => sum + child.evidenceCount,
        0
      );
      return `Category: ${d.data.name}\n${techniqueCount} techniques\n${totalEvidence} records`;
    }
    if (d.depth === 2) {
      return `Technique: ${d.data.name}\nRecords: ${d.data.evidenceCount}`;
    }
    return d.data.name;
  });

  function wrapText(text, maxChars) {
    if (text.length <= maxChars) return [text];
    const words = text.split(/\s+/);
    const lines = [];
    let currentLine = "";
    words.forEach((word) => {
      if (currentLine.length + word.length + 1 <= maxChars) {
        currentLine += (currentLine.length > 0 ? " " : "") + word;
      } else {
        if (currentLine.length > 0) lines.push(currentLine);
        currentLine = word;
      }
    });
    if (currentLine.length > 0) lines.push(currentLine);
    return lines;
  }

  g.append("g")
    .attr("class", "label")
    .style("pointer-events", "none")
    .attr("transform", (d) => {
      if (d.depth === 0) return "";
      const angle = (d.x0 + d.x1) / 2;
      const degrees = (angle * 180) / Math.PI - 90;
      let labelRadius =
        d.depth === 1
          ? innerRadius + ringWidth * 0.55
          : innerRadius + ringWidth * 1.05;
      return `rotate(${degrees}) translate(${labelRadius},0)`;
    })
    .each(function (d) {
      if (d.depth === 0) return;

      const group = d3.select(this);
      const angle = (d.x0 + d.x1) / 2;
      const isRightSide = angle < Math.PI;
      const segmentAngle = d.x1 - d.x0;
      const minAngleForLabel = 0.005;

      if (segmentAngle > minAngleForLabel) {
        if (d.depth === 1) {
          group
            .append("text")
            .attr("transform", angle >= Math.PI ? "rotate(180)" : "")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .style("font-size", "11px")
            .style("font-weight", "bold")
            .style("fill", "#fff")
            .text(d.data.name);
        } else {
          const isZero = d.data.evidenceCount === 0;
          const labelText = isZero ? d.data.name + " (0)" : d.data.name;
          const lines = wrapText(labelText, 38);
          const textColor = "#000";

          lines.forEach((line, i) => {
            group
              .append("text")
              .attr("transform", angle >= Math.PI ? "rotate(180)" : "")
              .attr("text-anchor", isRightSide ? "start" : "end")
              .attr("dy", `${(i - lines.length / 2 + 0.75) * 1.1}em`)
              .attr("x", 0)
              .style("font-size", "12px")
              .style("fill", textColor)
              .style("font-style", isZero ? "italic" : "normal")
              .text(line);
          });
        }
      }
    });

  return svg.node();
}


function _8(filteredData, data, md) {
  return (
    md`
## Summary Statistics

**Total Records:** ${filteredData.length.toLocaleString()} ${filteredData.length !== data.flatPairs.length
        ? `(filtered from ${data.flatPairs.length.toLocaleString()})`
        : ''
      }

| Metric | Currently Linked | Total in Dataset |
| :--- | :--- | :--- |
| **Techniques** | **${new Set(filteredData.map(d => d.technique)).size}** | ${data.techniques.length} |
| **Categories** | **${new Set(filteredData.map(d => d.category)).size}** | ${data.categories.length} |
| **Providers** | **${new Set(filteredData.map(d => d.provider)).size}** | ${new Set(data.flatPairs.map(d => d.provider)).size} |

${filteredData.length > 0 ? `
**Active Categories:** ${Array.from(new Set(filteredData.map(d => d.category))).sort().join(', ')}

**Active Providers:** ${Array.from(new Set(filteredData.map(d => d.provider))).sort().join(', ')}
` : '**No data matches current filters**'}`
  )
}

function _9(htl) {
  return (
    htl.html`<hr/>`
  )
}

function _10(md) {
  return (
    md`## Model Development Lifecycle
Safety techniques mapped across the six phases of model development. Techniques appearing in multiple phases are connected with bridge lines. The governance band spans the full lifecycle to reflect its cross-cutting nature. Use the provider filter to compare coverage profiles.`
  )
}

function _lifecycleChart(lifecycleChartData, lifecycleConfig, d3, data) {
  const chartData = lifecycleChartData;
  const cfg = lifecycleConfig;

  // --- State ---
  let selectedProvider = null;

  // --- Container ---
  const container = d3.create("div").style("position", "relative");

  // --- Provider filter bar ---
  const filterBar = container
    .append("div")
    .style("margin-bottom", "12px")
    .style("display", "flex")
    .style("align-items", "center")
    .style("gap", "12px")
    .style("font-family", "'Segoe UI', system-ui, sans-serif");

  filterBar
    .append("label")
    .style("font-size", "13px")
    .style("font-weight", "600")
    .style("color", "#444")
    .text("Filter by provider:");

  const providerSelect = filterBar
    .append("select")
    .style("font-size", "13px")
    .style("padding", "4px 8px")
    .style("border", "1px solid #ccc")
    .style("border-radius", "4px")
    .style("background", "#fff")
    .on("change", function () {
      selectedProvider = this.value || null;
      updateProviderHighlight();
    });

  providerSelect.append("option").attr("value", "").text("All providers");
  chartData.allProviders.forEach((p) => {
    providerSelect.append("option").attr("value", p).text(p);
  });

  const providerStatus = filterBar
    .append("span")
    .style("font-size", "12px")
    .style("color", "#888");

  // --- SVG ---
  const svg = container
    .append("svg")
    .attr("width", cfg.width)
    .attr("height", cfg.height)
    .attr("viewBox", `0 0 ${cfg.width} ${cfg.height}`)
    .style("font-family", "'Segoe UI', system-ui, sans-serif")
    .style("background", "#fafafa")
    .style("border-radius", "8px")
    .style("border", "1px solid #e0e0e0");

  // --- Defs ---
  const defs = svg.append("defs");

  const shadowFilter = defs
    .append("filter")
    .attr("id", "lc-shadow")
    .attr("x", "-10%")
    .attr("y", "-10%")
    .attr("width", "120%")
    .attr("height", "130%");
  shadowFilter
    .append("feDropShadow")
    .attr("dx", 0)
    .attr("dy", 1)
    .attr("stdDeviation", 1.5)
    .attr("flood-color", "#000")
    .attr("flood-opacity", 0.08);

  defs
    .append("marker")
    .attr("id", "lc-arrowhead")
    .attr("viewBox", "0 0 10 7")
    .attr("refX", 10)
    .attr("refY", 3.5)
    .attr("markerWidth", 10)
    .attr("markerHeight", 7)
    .attr("orient", "auto")
    .append("polygon")
    .attr("points", "0 0, 10 3.5, 0 7")
    .attr("fill", "#aaa");

  // ─────────────────────────────────────────────
  //  LAYER 1: BEZIER CONNECTORS (drawn first, behind everything)
  // ─────────────────────────────────────────────
  const connectorGroup = svg.append("g").attr("class", "lc-connectors");

  chartData.connectors.forEach((conn) => {
    const x1 = conn.govPos.cx;
    const y1 = conn.govPos.y + conn.govPos.height; // bottom of governance node
    const x2 = conn.tempPos.cx;
    const y2 = conn.tempPos.y; // top of temporal node

    // Control points: pull horizontally toward midpoint, vertically toward middle
    const midY = (y1 + y2) / 2;
    const cp1x = x1;
    const cp1y = y1 + (midY - y1) * 0.6;
    const cp2x = x2;
    const cp2y = y2 - (y2 - midY) * 0.6;

    connectorGroup
      .append("path")
      .attr("class", `lc-connector lc-connector-${conn.techId}`)
      .attr(
        "d",
        `M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`
      )
      .attr("fill", "none")
      .attr("stroke", cfg.connector.color)
      .attr("stroke-width", cfg.connector.strokeWidth)
      .attr("stroke-dasharray", cfg.connector.dashArray)
      .attr("opacity", cfg.connector.opacity);

    // Small endpoint circles
    connectorGroup
      .append("circle")
      .attr("class", `lc-connector lc-connector-${conn.techId}`)
      .attr("cx", x1)
      .attr("cy", y1)
      .attr("r", 3)
      .attr("fill", cfg.connector.color)
      .attr("opacity", cfg.connector.opacity);

    connectorGroup
      .append("circle")
      .attr("class", `lc-connector lc-connector-${conn.techId}`)
      .attr("cx", x2)
      .attr("cy", y2)
      .attr("r", 3)
      .attr("fill", cfg.connector.color)
      .attr("opacity", cfg.connector.opacity);
  });

  // ─────────────────────────────────────────────
  //  LAYER 2: GOVERNANCE BAND (top)
  // ─────────────────────────────────────────────
  const govGroup = svg.append("g").attr("class", "lc-governance");

  govGroup
    .append("rect")
    .attr("x", cfg.margin.left)
    .attr("y", cfg.governance.top)
    .attr("width", cfg.width - cfg.margin.left - cfg.margin.right)
    .attr("height", cfg.governance.height)
    .attr("rx", 6)
    .attr("fill", "#ECEFF1")
    .attr("stroke", "#90A4AE")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "6,3")
    .attr("opacity", 0.5);

  govGroup
    .append("text")
    .attr("x", cfg.margin.left + 12)
    .attr("y", cfg.governance.top + cfg.governance.labelOffsetY)
    .attr("font-size", "12px")
    .attr("font-weight", "600")
    .attr("fill", "#546E7A")
    .text("Governance & Compliance");

  govGroup
    .append("text")
    .attr("x", cfg.width - cfg.margin.right - 12)
    .attr("y", cfg.governance.top + cfg.governance.labelOffsetY)
    .attr("text-anchor", "end")
    .attr("font-size", "10px")
    .attr("fill", "#90A4AE")
    .text("organisational oversight across all phases →");

  // Governance nodes
  chartData.governanceTechniques.forEach((tech) => {
    const pos = chartData.govPositions.get(tech.id);
    if (pos) renderTechNode(govGroup, tech, pos, false);
  });

  // ─────────────────────────────────────────────
  //  LAYER 3: TIMELINE ARROW
  // ─────────────────────────────────────────────
  const timelineY = cfg.phases.areaTop - 18;

  svg
    .append("line")
    .attr("x1", cfg.margin.left)
    .attr("y1", timelineY)
    .attr("x2", cfg.width - cfg.margin.right - 2)
    .attr("y2", timelineY)
    .attr("stroke", "#bbb")
    .attr("stroke-width", 1.5)
    .attr("marker-end", "url(#lc-arrowhead)");

  svg
    .append("text")
    .attr("x", cfg.margin.left)
    .attr("y", timelineY - 6)
    .attr("font-size", "10px")
    .attr("fill", "#999")
    .text("MODEL DEVELOPMENT LIFECYCLE");

  // ─────────────────────────────────────────────
  //  LAYER 4: TEMPORAL PHASE COLUMNS
  // ─────────────────────────────────────────────
  const phaseGroup = svg.append("g").attr("class", "lc-phases");

  chartData.columns.forEach((col) => {
    const g = phaseGroup.append("g");

    // Column background
    g.append("rect")
      .attr("x", col.x)
      .attr("y", cfg.phases.areaTop)
      .attr("width", col.width)
      .attr("height", cfg.phases.areaBottom - cfg.phases.areaTop)
      .attr("rx", 6)
      .attr("fill", cfg.phaseColors[col.phaseId] || "#f5f5f5")
      .attr("stroke", cfg.phaseBorderColors[col.phaseId] || "#ddd")
      .attr("stroke-width", 1)
      .attr("opacity", 0.5);

    // Phase header
    g.append("rect")
      .attr("x", col.x)
      .attr("y", cfg.phases.areaTop)
      .attr("width", col.width)
      .attr("height", cfg.phases.headerHeight)
      .attr("rx", 6)
      .attr("fill", cfg.phaseBorderColors[col.phaseId] || "#999")
      .attr("opacity", 0.85);

    g.append("text")
      .attr("x", col.centerX)
      .attr("y", cfg.phases.areaTop + cfg.phases.headerHeight / 2 + 1)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "600")
      .attr("fill", "#fff")
      .text(col.phaseName);

    // Technique count
    g.append("text")
      .attr("x", col.x + col.width - 8)
      .attr("y", cfg.phases.areaTop + cfg.phases.headerHeight + 12)
      .attr("text-anchor", "end")
      .attr("font-size", "10px")
      .attr("fill", "#999")
      .text(`${col.techniques.length}`);
  });

  // ─────────────────────────────────────────────
  //  LAYER 5: TECHNIQUE NODES (temporal columns)
  // ─────────────────────────────────────────────
  const nodesGroup = svg.append("g").attr("class", "lc-nodes");

  chartData.columns.forEach((col) => {
    (col.techniques || []).forEach((tech) => {
      const posKey = tech._isEcho ? `${tech.id}__temporal` : tech.id;
      const pos = chartData.nodePositions.get(posKey);
      if (pos) renderTechNode(nodesGroup, tech, pos, !!tech._isEcho);
    });
  });

  // ─────────────────────────────────────────────
  //  LAYER 6: SPANNING NODES (across adjacent columns)
  // ─────────────────────────────────────────────
  chartData.spanningPositions.forEach((span) => {
    const g = nodesGroup
      .append("g")
      .attr("class", "lc-tech-node")
      .attr("data-tech-id", span.tech.id)
      .attr("transform", `translate(${span.x}, ${span.y})`)
      .style("cursor", "pointer");

    g.append("rect")
      .attr("width", span.width)
      .attr("height", span.height)
      .attr("rx", cfg.node.radius)
      .attr("fill", "#fff")
      .attr("stroke", span.tech.categoryColor)
      .attr("stroke-width", 1.5)
      .attr("filter", "url(#lc-shadow)");

    // Category colour left edge
    g.append("rect")
      .attr("width", 4)
      .attr("height", span.height)
      .attr("rx", 2)
      .attr("fill", span.tech.categoryColor)
      .attr("opacity", 0.85);

    // Label centred
    g.append("text")
      .attr("x", span.width / 2)
      .attr("y", span.height / 2 + 1)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("font-size", `${cfg.node.fontSize}px`)
      .attr("fill", "#333")
      .attr("font-weight", "500")
      .text(span.tech.name);

    // Phase labels at each end
    const fromCol = chartData.columnLookup.get(span.fromPhase);
    const toCol = chartData.columnLookup.get(span.toPhase);
    if (fromCol && toCol) {
      g.append("text")
        .attr("x", fromCol.centerX - span.x)
        .attr("y", span.height + 12)
        .attr("text-anchor", "middle")
        .attr("font-size", "9px")
        .attr("fill", "#aaa")
        .text(`◂ ${fromCol.phaseName}`);
      g.append("text")
        .attr("x", toCol.centerX - span.x)
        .attr("y", span.height + 12)
        .attr("text-anchor", "middle")
        .attr("font-size", "9px")
        .attr("fill", "#aaa")
        .text(`${toCol.phaseName} ▸`);
    }

    attachTooltip(g, span.tech, span);
  });

  // ─────────────────────────────────────────────
  //  LAYER 7: HARM & CONTENT CLASSIFICATION BAND (bottom)
  // ─────────────────────────────────────────────
  const harmGroup = svg.append("g").attr("class", "lc-harm");

  harmGroup
    .append("rect")
    .attr("x", cfg.margin.left)
    .attr("y", cfg.harm.top)
    .attr("width", cfg.width - cfg.margin.left - cfg.margin.right)
    .attr("height", cfg.harm.height)
    .attr("rx", 6)
    .attr("fill", "#FFF3E0")
    .attr("stroke", "#FF9800")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "6,3")
    .attr("opacity", 0.4);

  harmGroup
    .append("text")
    .attr("x", cfg.margin.left + 12)
    .attr("y", cfg.harm.top + cfg.harm.labelOffsetY)
    .attr("font-size", "12px")
    .attr("font-weight", "600")
    .attr("fill", "#E65100")
    .text("Harm & Content Classification");

  harmGroup
    .append("text")
    .attr("x", cfg.width - cfg.margin.right - 12)
    .attr("y", cfg.harm.top + cfg.harm.labelOffsetY)
    .attr("text-anchor", "end")
    .attr("font-size", "10px")
    .attr("fill", "#FF9800")
    .text("cross-stage classifiers applied at data curation & runtime →");

  chartData.harmTechniques.forEach((tech) => {
    const pos = chartData.harmPositions.get(tech.id);
    if (pos) renderTechNode(harmGroup, tech, pos, false);
  });

  // ─────────────────────────────────────────────
  //  TOOLTIP
  // ─────────────────────────────────────────────
  const tooltip = container
    .append("div")
    .style("position", "absolute")
    .style("display", "none")
    .style("background", "#fff")
    .style("border", "1px solid #ddd")
    .style("border-radius", "6px")
    .style("padding", "10px 14px")
    .style("font-size", "12px")
    .style("max-width", "320px")
    .style("box-shadow", "0 2px 8px rgba(0,0,0,0.12)")
    .style("pointer-events", "none")
    .style("z-index", "10")
    .style("font-family", "'Segoe UI', system-ui, sans-serif");

  // ─────────────────────────────────────────────
  //  NODE RENDERER
  // ─────────────────────────────────────────────
  function renderTechNode(parent, tech, pos, isEcho) {
    const g = parent
      .append("g")
      .attr("class", "lc-tech-node")
      .attr("data-tech-id", tech.id)
      .attr("transform", `translate(${pos.x}, ${pos.y})`)
      .style("cursor", "pointer");

    // Background rect — echo nodes get light grey border
    g.append("rect")
      .attr("width", pos.width)
      .attr("height", pos.height)
      .attr("rx", cfg.node.radius)
      .attr("fill", isEcho ? "#fafafa" : "#fff")
      .attr("stroke", isEcho ? "#bbb" : tech.categoryColor)
      .attr("stroke-width", isEcho ? 1 : 1.5)
      .attr("filter", isEcho ? "none" : "url(#lc-shadow)");

    // Category colour left edge — muted for echo
    g.append("rect")
      .attr("width", 4)
      .attr("height", pos.height)
      .attr("rx", 2)
      .attr("fill", isEcho ? "#ccc" : tech.categoryColor)
      .attr("opacity", isEcho ? 0.4 : 0.85);

    // Label — echo nodes: lighter grey, italic
    const maxChars = Math.floor((pos.width - 20) / 6.5);
    const label =
      tech.name.length > maxChars
        ? tech.name.slice(0, maxChars - 1) + "…"
        : tech.name;

    g.append("text")
      .attr("x", cfg.node.padding.x + 4)
      .attr("y", pos.height / 2 + 1)
      .attr("dominant-baseline", "middle")
      .attr("font-size", `${cfg.node.fontSize}px`)
      .attr("fill", isEcho ? "#aaa" : "#333")
      .attr("font-weight", isEcho ? "normal" : "500")
      .attr("font-style", isEcho ? "italic" : "normal")
      .text(label);

    attachTooltip(g, tech, pos);
  }

  // ─────────────────────────────────────────────
  //  TOOLTIP + CONNECTOR HIGHLIGHT
  // ─────────────────────────────────────────────
  function attachTooltip(g, tech, pos) {
    g.on("mouseenter", function () {
      // Highlight connectors for this technique
      svg
        .selectAll(`.lc-connector-${tech.id}`)
        .attr("opacity", 1)
        .attr("stroke-width", 2.5);

      const phases = (tech.lifecycleStages || [])
        .map((s) => {
          const def = (data.lifecycle || []).find((p) => p.id === s);
          return def?.name || s;
        })
        .join("  →  ");

      const providerList =
        tech.providerNames.length > 0
          ? tech.providerNames.join(", ")
          : "<em>No provider evidence yet</em>";

      tooltip
        .style("display", "block")
        .html(
          `<div style="font-weight:600; margin-bottom:4px;">${tech.name}</div>` +
          `<div style="color:#666; margin-bottom:6px;">${tech.description || ""
          }</div>` +
          `<div style="font-size:11px; color:${tech.categoryColor}; margin-bottom:4px;">` +
          `■ ${tech.categoryName}</div>` +
          `<div style="font-size:11px; color:#888; margin-bottom:4px;">` +
          `Phases: ${phases}</div>` +
          `<div style="font-size:11px; color:#666;">` +
          `Providers: ${providerList}</div>`
        );

      const tooltipX =
        pos.x + pos.width + 328 > cfg.width
          ? pos.x - 330
          : pos.x + pos.width + 8;

      tooltip.style("left", tooltipX + "px").style("top", pos.y + "px");
    });

    g.on("mouseleave", function () {
      svg
        .selectAll(`.lc-connector-${tech.id}`)
        .attr("opacity", cfg.connector.opacity)
        .attr("stroke-width", cfg.connector.strokeWidth);
      tooltip.style("display", "none");
    });
  }

  // ─────────────────────────────────────────────
  //  CATEGORY LEGEND
  // ─────────────────────────────────────────────
  const uniqueCats = [
    ...new Map(
      chartData.allTechniques.map((t) => {
        const cat = data.categories?.find((c) => c.id === t.categoryId) || {};
        return [
          t.categoryId,
          {
            id: t.categoryId,
            name: cat.name || t.categoryId,
            color: cat.color || "#999"
          }
        ];
      })
    ).values()
  ].sort((a, b) => a.name.localeCompare(b.name));

  const legend = container
    .append("div")
    .style("display", "flex")
    .style("gap", "16px")
    .style("margin-top", "10px")
    .style("flex-wrap", "wrap")
    .style("font-family", "'Segoe UI', system-ui, sans-serif");

  legend
    .append("span")
    .style("font-size", "11px")
    .style("font-weight", "600")
    .style("color", "#666")
    .style("align-self", "center")
    .text("Categories:");

  uniqueCats.forEach((cat) => {
    const item = legend
      .append("span")
      .style("display", "inline-flex")
      .style("align-items", "center")
      .style("gap", "5px")
      .style("font-size", "11px")
      .style("color", "#555");

    item
      .append("span")
      .style("width", "10px")
      .style("height", "10px")
      .style("border-radius", "2px")
      .style("background", cat.color)
      .style("display", "inline-block");

    item.append("span").text(cat.name);
  });

  // ─────────────────────────────────────────────
  //  PROVIDER FILTER
  // ─────────────────────────────────────────────
  function updateProviderHighlight() {
    if (!selectedProvider) {
      svg.selectAll(".lc-tech-node").attr("opacity", 1);
      svg.selectAll(".lc-connector").attr("opacity", cfg.connector.opacity);
      providerStatus.text("");
      return;
    }

    const providerTechNames = new Set();
    (data.flatPairs || []).forEach((fp) => {
      if (fp.provider === selectedProvider) {
        providerTechNames.add(fp.technique);
      }
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
      const match = [...providerTechIds].some((id) =>
        cls.includes(`lc-connector-${id}`)
      );
      d3.select(this).attr("opacity", match ? 0.8 : 0.08);
    });

    providerStatus.text(
      `${providerTechIds.size} of ${chartData.allTechniques.length} techniques evidenced`
    );
  }

  return container.node();
}


function _12(htl) {
  return (
    htl.html`<hr/>`
  )
}

function _13(md) {
  return (
    md`## Documentation Map
The following chart shows the relationship between documents in the collection to providers (via models). This is to provide a quick overview as to which documentation has been brought into the dataset for analysis and will also assist in coverage analysis as I identify gaps in information.
Click and drag to move things around. you can export the layout and save it as your prefer. Tooltips on the document nodes provide the URIs for the original source document referenced.`
  )
}

function _networkViz(positionedGraph, validatedLayout, networkConfig, d3, localStorage, layoutStorageKey, confirm, location, autoLayout, providerColors) {
  const {
    nodes,
    providers,
    models,
    evidence,
    resolvedLinks,
    nodeById,
    orphanModels,
    orphanEvidence
  } = positionedGraph;

  const { source: layoutSource, stats: layoutStats } = validatedLayout;

  const {
    width,
    height,
    centerX,
    centerY,
    providerRadius,
    modelRadius,
    evidenceRadius,
    nodeRadius,
    evidenceRect,
    colors,
    linkColors
  } = networkConfig;

  // ── Selection state ──
  const selectedNodes = new Set();

  // ── Container ──
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
    border-radius: 4px; background: #fff; cursor: pointer;
    transition: background 0.15s;
  `;

  function addButton(parent, label, onClick, insertPos) {
    const btn = insertPos
      ? parent.insert("button", insertPos)
      : parent.append("button");
    return btn
      .attr("style", buttonStyle)
      .text(label)
      .on("click", onClick)
      .on("mouseover", function () {
        d3.select(this).style("background", "#f0f0f0");
      })
      .on("mouseout", function () {
        d3.select(this).style("background", "#fff");
      });
  }

  const statusText = {
    saved: "✓ Using saved layout",
    attached: "✓ Using default layout",
    default: "Using radial layout"
  };

  const status = toolbar
    .append("span")
    .style("font-size", "11px")
    .style("color", layoutSource === "default" ? "#666" : "#2e7d32")
    .style("margin-left", "12px")
    .style("min-width", "160px")
    .text(statusText[layoutSource]);

  const selectionStatus = toolbar
    .append("span")
    .style("font-size", "11px")
    .style("color", "#666")
    .style("margin-left", "12px")
    .text("");

  let layoutModified = false;

  function showStatus(message, color, duration = 2000) {
    status.text(message).style("color", color);
    if (duration > 0) {
      setTimeout(() => {
        if (layoutModified) {
          status.text("⚠ Unsaved changes").style("color", "#c9190b");
        } else {
          status
            .text(statusText[layoutSource])
            .style("color", layoutSource === "default" ? "#666" : "#2e7d32");
        }
      }, duration);
    }
  }

  function updateSelectionStatus() {
    selectionStatus.text(
      selectedNodes.size === 0
        ? ""
        : `${selectedNodes.size} selected (drag background to select, Esc to clear)`
    );
  }

  // ── Toolbar buttons ──
  addButton(
    toolbar,
    "💾 Save Layout",
    function () {
      try {
        const layout = {};
        nodes.forEach((n) => {
          layout[n.id] = { x: n.x, y: n.y };
        });
        localStorage.setItem(layoutStorageKey, JSON.stringify(layout));
        layoutModified = false;
        showStatus("✓ Layout saved!", "#2e7d32", 2000);
      } catch (e) {
        showStatus("✗ Save failed: " + e.message, "#c9190b", 3000);
      }
    },
    ":first-child"
  );

  addButton(
    toolbar,
    "↺ Reset to Default",
    function () {
      if (
        confirm("Reset to default layout? This will clear your saved changes.")
      ) {
        try {
          localStorage.removeItem(layoutStorageKey);
          location.reload();
        } catch (e) {
          showStatus("✗ Reset failed: " + e.message, "#c9190b", 3000);
        }
      }
    },
    ":nth-child(2)"
  );

  addButton(
    toolbar,
    "⚡ Auto Layout",
    function () {
      // Apply autoLayout positions
      nodes.forEach((n) => {
        const pos = autoLayout[n.id];
        if (pos) {
          n.x = pos.x;
          n.y = pos.y;
        }
      });

      // Update all node positions
      g.selectAll(".providers g, .models g, .evidence g").attr(
        "transform",
        (d) => `translate(${d.x},${d.y})`
      );

      // Re-apply label anchoring from autoLayout hints
      // Providers
      g.selectAll(".providers g text")
        .attr("text-anchor", (d) => {
          if (d.labelAnchor) return d.labelAnchor;
          const a = d.angle;
          if (a > Math.PI / 4 && a < (3 * Math.PI) / 4) return "middle";
          if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4) return "middle";
          return a > Math.PI / 2 || a < -Math.PI / 2 ? "end" : "start";
        })
        .attr("x", (d) => {
          if (d.labelAnchor === "end") return -nodeRadius.provider - 6;
          if (d.labelAnchor === "start") return nodeRadius.provider + 6;
          const a = d.angle;
          if (a > Math.PI / 4 && a < (3 * Math.PI) / 4) return 0;
          if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4) return 0;
          return a > Math.PI / 2 || a < -Math.PI / 2
            ? -nodeRadius.provider - 6
            : nodeRadius.provider + 6;
        })
        .attr("y", (d) => {
          if (d.labelAnchor) return 4;
          const a = d.angle;
          if (a > Math.PI / 4 && a < (3 * Math.PI) / 4)
            return nodeRadius.provider + 14;
          if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4)
            return -nodeRadius.provider - 6;
          return 4;
        });

      // Models
      g.selectAll(".models g text")
        .attr("text-anchor", (d) => {
          if (d.labelAnchor) return d.labelAnchor;
          return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2
            ? "end"
            : "start";
        })
        .attr("x", (d) => {
          if (d.labelAnchor === "end") return -nodeRadius.model - 4;
          if (d.labelAnchor === "start") return nodeRadius.model + 4;
          return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2
            ? -nodeRadius.model - 4
            : nodeRadius.model + 4;
        });

      // Evidence
      g.selectAll(".evidence g text")
        .attr("text-anchor", (d) => {
          if (d.labelAnchor) return d.labelAnchor;
          return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2
            ? "end"
            : "start";
        })
        .attr("x", (d) => {
          if (d.labelAnchor === "end") return -evidenceRect.width / 2 - 6;
          if (d.labelAnchor === "start") return evidenceRect.width / 2 + 6;
          return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2
            ? -evidenceRect.width / 2 - 6
            : evidenceRect.width / 2 + 6;
        });

      updateLinks();

      layoutModified = true;
      showStatus("⚡ Auto layout applied (unsaved)", "#7c5e10", 3000);
    },
    ":nth-child(3)"
  );

  addButton(
    toolbar,
    "📤 Export Layout",
    function () {
      try {
        const layout = {};
        nodes.forEach((n) => {
          layout[n.id] = { x: n.x, y: n.y };
        });
        const blob = new Blob([JSON.stringify(layout, null, 2)], {
          type: "application/json"
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "network-layout.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showStatus("✓ Layout exported!", "#2e7d32", 2000);
      } catch (e) {
        showStatus("✗ Export failed: " + e.message, "#c9190b", 3000);
      }
    },
    ":nth-child(3)"
  );

  // Import file input + button
  const fileInput = toolbar
    .insert("input", ":nth-child(4)")
    .attr("type", "file")
    .attr("accept", ".json")
    .style("display", "none")
    .on("change", function () {
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const layout = JSON.parse(e.target.result);
          const keys = Object.keys(layout);
          if (keys.length === 0) throw new Error("Empty layout file");
          const sample = layout[keys[0]];
          if (typeof sample.x !== "number" || typeof sample.y !== "number")
            throw new Error("Invalid layout format");
          localStorage.setItem(layoutStorageKey, JSON.stringify(layout));
          showStatus("✓ Imported! Reloading...", "#2e7d32", 1000);
          setTimeout(() => location.reload(), 1000);
        } catch (err) {
          showStatus("✗ Import failed: " + err.message, "#c9190b", 3000);
        }
      };
      reader.onerror = () =>
        showStatus("✗ Could not read file", "#c9190b", 3000);
      reader.readAsText(file);
    });

  addButton(
    toolbar,
    "📥 Import Layout",
    () => fileInput.node().click(),
    ":nth-child(5)"
  );

  addButton(
    toolbar,
    "⊘ Clear Selection",
    () => clearSelection(),
    ":nth-child(6)"
  );

  // ── Status indicators ──
  if (orphanModels > 0 || orphanEvidence > 0) {
    toolbar
      .append("span")
      .style("font-size", "11px")
      .style("color", "#c9190b")
      .style("margin-left", "16px")
      .style("padding", "4px 8px")
      .style("background", "#fee")
      .style("border-radius", "4px")
      .style("border", "1px solid #fcc")
      .html(
        `⚠ Orphans: ${orphanModels > 0
          ? `${orphanModels} model${orphanModels > 1 ? "s" : ""}`
          : ""
        }${orphanModels > 0 && orphanEvidence > 0 ? ", " : ""}${orphanEvidence > 0
          ? `${orphanEvidence} doc${orphanEvidence > 1 ? "s" : ""}`
          : ""
        }`
      );
  }

  if (layoutStats.stale > 0 || layoutStats.newNodes > 0) {
    const parts = [];
    if (layoutStats.stale > 0) parts.push(`${layoutStats.stale} stale removed`);
    if (layoutStats.newNodes > 0)
      parts.push(`${layoutStats.newNodes} new (radial)`);
    toolbar
      .append("span")
      .style("font-size", "11px")
      .style("color", "#7c5e10")
      .style("margin-left", "8px")
      .style("padding", "4px 8px")
      .style("background", "#fff8e1")
      .style("border-radius", "4px")
      .style("border", "1px solid #ffe082")
      .html(`⟳ Layout sync: ${parts.join(", ")}`);
  }

  // ── SVG + Zoom ──
  const svg = container
    .append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("width", width)
    .attr("height", height)
    .style("background", "#fafafa");

  const g = svg.append("g");
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
    .attr("class", "marquee")
    .attr("fill", "rgba(0, 102, 204, 0.1)")
    .attr("stroke", "#0066cc")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "4,2")
    .style("display", "none");

  let marqueeStart = null;
  let isMarqueeSelecting = false;

  svg.on("mousedown", function (event) {
    if (
      event.target === svg.node() ||
      (event.target.tagName === "rect" &&
        event.target.classList.contains("marquee-bg"))
    ) {
      const [x, y] = d3.pointer(event, svg.node());
      marqueeStart = { x, y };
      isMarqueeSelecting = true;
      marquee
        .attr("x", x)
        .attr("y", y)
        .attr("width", 0)
        .attr("height", 0)
        .style("display", "block");
      if (!event.shiftKey) clearSelection();
      event.preventDefault();
    }
  });

  svg.on("mousemove", function (event) {
    if (!isMarqueeSelecting || !marqueeStart) return;
    const [x, y] = d3.pointer(event, svg.node());
    const minX = Math.min(marqueeStart.x, x);
    const minY = Math.min(marqueeStart.y, y);
    const w = Math.abs(x - marqueeStart.x);
    const h = Math.abs(y - marqueeStart.y);
    marquee.attr("x", minX).attr("y", minY).attr("width", w).attr("height", h);
    const mRect = {
      x1: (minX - currentTransform.x) / currentTransform.k,
      y1: (minY - currentTransform.y) / currentTransform.k,
      x2: (minX + w - currentTransform.x) / currentTransform.k,
      y2: (minY + h - currentTransform.y) / currentTransform.k
    };
    g.selectAll(".providers g, .models g, .evidence g").classed(
      "marquee-hover",
      (d) =>
        d.x >= mRect.x1 && d.x <= mRect.x2 && d.y >= mRect.y1 && d.y <= mRect.y2
    );
  });

  svg.on("mouseup", function (event) {
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
      nodes.forEach((n) => {
        if (
          n.x >= mRect.x1 &&
          n.x <= mRect.x2 &&
          n.y >= mRect.y1 &&
          n.y <= mRect.y2
        )
          selectedNodes.add(n.id);
      });
      updateSelectionVisuals();
    }
    g.selectAll(".marquee-hover").classed("marquee-hover", false);
    marquee.style("display", "none");
    marqueeStart = null;
    isMarqueeSelecting = false;
  });

  svg.on("mouseleave", function () {
    if (isMarqueeSelecting) {
      g.selectAll(".marquee-hover").classed("marquee-hover", false);
      marquee.style("display", "none");
      marqueeStart = null;
      isMarqueeSelecting = false;
    }
  });

  // ── Guide circles (radial mode only) ──
  if (layoutSource === "default") {
    [providerRadius, modelRadius, evidenceRadius].forEach((r) => {
      g.append("circle")
        .attr("cx", centerX)
        .attr("cy", centerY)
        .attr("r", r)
        .attr("fill", "none")
        .attr("stroke", "#eee")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "4,4");
    });
  }

  // ── Links ──
  const linkGroup = g.append("g").attr("class", "links");
  const linkElements = linkGroup
    .selectAll("line")
    .data(resolvedLinks)
    .join("line")
    .attr("x1", (d) => d.source.x)
    .attr("y1", (d) => d.source.y)
    .attr("x2", (d) => d.target.x)
    .attr("y2", (d) => d.target.y)
    .attr("stroke", (d) => linkColors[d.type])
    .attr("stroke-width", (d) => (d.type === "owns" ? 1.5 : 0.75))
    .attr("stroke-opacity", 0.4);

  function updateLinks() {
    linkElements
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
  }

  // ── Node styling helpers ──
  function getNodeStroke(d) {
    if (selectedNodes.has(d.id)) return "#0066cc";
    if (d.isOrphan) return "#c9190b";
    if (d.type === "provider") return "#fff";
    return providerColors[d.providerName] || colors.evidenceBorder;
  }

  function getNodeStrokeWidth(d) {
    if (selectedNodes.has(d.id)) return 3;
    if (d.isOrphan) return 3;
    if (d.type === "provider") return 2;
    return 1.5;
  }

  function updateSelectionVisuals() {
    g.selectAll(".providers g, .models g, .evidence g")
      .classed("selected", (d) => selectedNodes.has(d.id))
      .select("circle, rect")
      .attr("stroke-width", (d) => getNodeStrokeWidth(d))
      .attr("stroke", (d) => getNodeStroke(d));
    updateSelectionStatus();
  }

  function clearSelection() {
    selectedNodes.clear();
    updateSelectionVisuals();
  }

  // ── Tooltip ──
  const tooltip = d3
    .select("body")
    .append("div")
    .attr("class", "network-tooltip")
    .style("position", "absolute")
    .style("visibility", "hidden")
    .style("background", "white")
    .style("border", "1px solid #ddd")
    .style("border-radius", "4px")
    .style("padding", "8px 12px")
    .style("font-size", "11px")
    .style("max-width", "350px")
    .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
    .style("z-index", 1000)
    .style("pointer-events", "auto");

  let tooltipTimeout = null;
  let isOverTooltip = false;
  let isOverNode = false;
  let isDragging = false;

  function hideTooltip() {
    tooltip.style("visibility", "hidden");
    isOverNode = false;
  }

  function showTooltip(event, d) {
    if (isDragging) return;
    if (tooltipTimeout) {
      clearTimeout(tooltipTimeout);
      tooltipTimeout = null;
    }
    isOverNode = true;
    const orphanWarning = d.isOrphan
      ? `<div style="color:#c9190b; margin-top:4px; padding-top:4px; border-top:1px solid #eee;">⚠ Orphan: ${d.type === "model"
        ? "No documents reference this model"
        : "No models linked to this document"
      }</div>`
      : "";
    tooltip
      .style("visibility", "visible")
      .html(
        `<strong>${d.label}</strong><br/>
        <em>Type:</em> ${d.type}${d.docType ? ` (${d.docType})` : ""}<br/>
        ${d.providerName ? `<em>Provider:</em> ${d.providerName}<br/>` : ""}
        ${d.modelCount !== undefined
          ? `<em>Models covered:</em> ${d.modelCount}<br/>`
          : ""
        }
        ${d.url
          ? `<a href="${d.url}" target="_blank" style="color:#2563eb; text-decoration:underline;">View document ↗</a>`
          : ""
        }
        ${orphanWarning}`
      )
      .style("top", event.pageY - 10 + "px")
      .style("left", event.pageX + 15 + "px");
  }

  function scheduleHideTooltip() {
    if (tooltipTimeout) clearTimeout(tooltipTimeout);
    tooltipTimeout = setTimeout(() => {
      if (!isOverTooltip && !isOverNode) tooltip.style("visibility", "hidden");
    }, 300);
  }

  tooltip
    .on("mouseenter", function () {
      isOverTooltip = true;
      if (tooltipTimeout) {
        clearTimeout(tooltipTimeout);
        tooltipTimeout = null;
      }
    })
    .on("mouseleave", function () {
      isOverTooltip = false;
      scheduleHideTooltip();
    });

  // ── Drag behavior ──
  function drag() {
    let dragStartPositions = new Map();
    return d3
      .drag()
      .on("start", function (event, d) {
        isDragging = true;
        hideTooltip();
        if (!selectedNodes.has(d.id)) {
          selectedNodes.clear();
          selectedNodes.add(d.id);
          updateSelectionVisuals();
        }
        dragStartPositions.clear();
        selectedNodes.forEach((id) => {
          const node = nodeById.get(id);
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
          const node = nodeById.get(id);
          const nodeStart = dragStartPositions.get(id);
          if (node && nodeStart) {
            node.x = nodeStart.x + dx;
            node.y = nodeStart.y + dy;
          }
        });
        g.selectAll(".providers g, .models g, .evidence g")
          .filter((n) => selectedNodes.has(n.id))
          .attr("transform", (n) => `translate(${n.x},${n.y})`);
        updateLinks();
        if (!layoutModified) {
          layoutModified = true;
          status.text("⚠ Unsaved changes").style("color", "#c9190b");
        }
      })
      .on("end", function () {
        d3.select(this).classed("dragging", false);
        dragStartPositions.clear();
        isDragging = false;
      });
  }

  // ── Render provider nodes ──
  const providerNodes = g
    .append("g")
    .attr("class", "providers")
    .selectAll("g")
    .data(providers)
    .join("g")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab")
    .call(drag());

  providerNodes
    .append("circle")
    .attr("r", nodeRadius.provider)
    .attr("fill", (d) => providerColors[d.providerName] || "#999")
    .attr("stroke", "#fff")
    .attr("stroke-width", 2);

  providerNodes
    .append("text")
    .text((d) => d.label)
    .attr("text-anchor", (d) => {
      const a = d.angle;
      if (a > Math.PI / 4 && a < (3 * Math.PI) / 4) return "middle";
      if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4) return "middle";
      return a > Math.PI / 2 || a < -Math.PI / 2 ? "end" : "start";
    })
    .attr("x", (d) => {
      const a = d.angle;
      if (a > Math.PI / 4 && a < (3 * Math.PI) / 4) return 0;
      if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4) return 0;
      return a > Math.PI / 2 || a < -Math.PI / 2
        ? -nodeRadius.provider - 6
        : nodeRadius.provider + 6;
    })
    .attr("y", (d) => {
      const a = d.angle;
      if (a > Math.PI / 4 && a < (3 * Math.PI) / 4)
        return nodeRadius.provider + 14;
      if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4)
        return -nodeRadius.provider - 6;
      return 4;
    })
    .style("font-size", "11px")
    .style("font-weight", "bold")
    .style("fill", "#333")
    .style("pointer-events", "none");

  // ── Render model nodes ──
  const modelNodes = g
    .append("g")
    .attr("class", "models")
    .selectAll("g")
    .data(models)
    .join("g")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab")
    .call(drag());

  modelNodes
    .append("circle")
    .attr("r", nodeRadius.model)
    .attr("fill", (d) => {
      const color = providerColors[d.providerName];
      return color ? d3.color(color).brighter(0.5) : colors.model;
    })
    .attr("stroke", (d) =>
      d.isOrphan ? "#c9190b" : providerColors[d.providerName] || "#fff"
    )
    .attr("stroke-width", (d) => (d.isOrphan ? 3 : 1));

  modelNodes
    .append("text")
    .text((d) => d.label)
    .attr("text-anchor", (d) =>
      d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? "end" : "start"
    )
    .attr("x", (d) =>
      d.angle > Math.PI / 2 || d.angle < -Math.PI / 2
        ? -nodeRadius.model - 4
        : nodeRadius.model + 4
    )
    .attr("y", 3)
    .style("font-size", "8px")
    .style("fill", "#555")
    .style("pointer-events", "none");

  // ── Render evidence nodes ──
  const evidenceNodes = g
    .append("g")
    .attr("class", "evidence")
    .selectAll("g")
    .data(evidence)
    .join("g")
    .attr("transform", (d) => `translate(${d.x},${d.y})`)
    .style("cursor", "grab")
    .call(drag());

  evidenceNodes
    .append("rect")
    .attr("x", -evidenceRect.width / 2)
    .attr("y", -evidenceRect.height / 2)
    .attr("width", evidenceRect.width)
    .attr("height", evidenceRect.height)
    .attr("rx", 2)
    .attr("ry", 2)
    .attr("fill", colors.evidence)
    .attr("stroke", (d) =>
      d.isOrphan
        ? "#c9190b"
        : providerColors[d.providerName] || colors.evidenceBorder
    )
    .attr("stroke-width", (d) => (d.isOrphan ? 3 : 1.5));

  evidenceNodes
    .append("text")
    .text((d) =>
      d.label.length > 35 ? d.label.substring(0, 33) + "..." : d.label
    )
    .attr("text-anchor", (d) =>
      d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? "end" : "start"
    )
    .attr("x", (d) =>
      d.angle > Math.PI / 2 || d.angle < -Math.PI / 2
        ? -evidenceRect.width / 2 - 6
        : evidenceRect.width / 2 + 6
    )
    .attr("y", 3)
    .style("font-size", "7px")
    .style("fill", "#666")
    .style("pointer-events", "none");

  // ── Node interactions ──
  const allNodes = g.selectAll(".providers g, .models g, .evidence g");

  allNodes
    .on("mouseenter", function (event, d) {
      if (isDragging || isMarqueeSelecting) return;
      showTooltip(event, d);
    })
    .on("mousemove", function (event) {
      if (isDragging || isMarqueeSelecting) return;
      tooltip
        .style("top", event.pageY - 10 + "px")
        .style("left", event.pageX + 15 + "px");
    })
    .on("mouseleave", function () {
      isOverNode = false;
      if (!isDragging) scheduleHideTooltip();
    })
    .on("mousedown", function (event) {
      hideTooltip();
      event.stopPropagation();
    });

  // ── Keyboard ──
  d3.select("body").on("keydown.networkGraph", function (event) {
    if (event.key === "Escape") clearSelection();
  });

  // ── CSS ──
  svg.append("style").text(`
    .dragging { cursor: grabbing !important; }
    .selected circle, .selected rect { filter: drop-shadow(0 0 3px #0066cc); }
    .marquee-hover circle, .marquee-hover rect { filter: drop-shadow(0 0 2px #0066cc); opacity: 0.8; }
  `);

  return container.node();
}


function _15(htl) {
  return (
    htl.html`<hr/>`
  )
}

function _excludedDataSummary(data, providerColors, html) {
  const exclusions = {
    missingProvider: [],
    missingTechnique: [],
    orphanedModelRefs: [], // RENAMED for clarity
    missingCategory: []
  };

  // Helper Sets for lookup
  const techIds = new Set(data.raw.techniques.map((t) => t.id));
  const catIds = new Set(data.raw.categories.map((c) => c.id));

  // UPDATED: Check against official Provider IDs if available
  const providerIds = new Set(
    data.raw.providers
      ? data.raw.providers.map((p) => p.id)
      : Object.keys(providerColors || {}) // Fallback
  );

  // Check Techniques
  Object.values(data.raw.techniqueMap)
    .flat()
    .forEach((d) => {
      if (!techIds.has(d.techniqueId)) {
        exclusions.missingTechnique.push({ _techniqueId: d.techniqueId });
      }
    });

  // Check Categories
  data.raw.techniques.forEach((t) => {
    if (!catIds.has(t.categoryId)) {
      exclusions.missingCategory.push({ _categoryId: t.categoryId });
    }
  });

  // Check Providers
  data.raw.evidence.forEach((s) => {
    if (s.provider) {
      // Check if the ID exists (case-insensitive)
      const isKnown = [...providerIds].some(
        (id) => id.toLowerCase() === s.provider.toLowerCase()
      );
      if (!isKnown) {
        exclusions.missingProvider.push({ _providerId: s.provider });
      }
    }
  });

  // Check Models - UPDATED to count unique orphaned references
  if (data.raw.models && Array.isArray(data.raw.models)) {
    const knownModelIds = new Set(data.raw.models.map((m) => m.id));
    const orphanedModels = new Set(); // Track unique orphaned IDs

    data.raw.evidence.forEach((s) => {
      if (s.models) {
        s.models.forEach((m) => {
          if (!knownModelIds.has(m.modelId)) {
            orphanedModels.add(m.modelId);
            exclusions.orphanedModelRefs.push({ _modelId: m.modelId });
          }
        });
      }
    });
  }

  // CALCULATE: Models in models.json with no technique mappings
  const modelsWithoutTechniques = new Set();
  if (data.raw.models && Array.isArray(data.raw.models)) {
    const modelsWithTechniques = new Set();

    // Collect all models that have techniques
    data.flatPairs.forEach((pair) => {
      if (pair.model) {
        // Handle comma-separated model lists
        pair.model.split(", ").forEach((modelId) => {
          modelsWithTechniques.add(modelId.trim());
        });
      }
    });

    // Find models without techniques
    data.raw.models.forEach((m) => {
      if (!modelsWithTechniques.has(m.id)) {
        modelsWithoutTechniques.add(m.id);
      }
    });
  }

  // Get unique counts
  const uniqueMissingProviders = new Set(
    exclusions.missingProvider.map((item) => item._providerId)
  );
  const uniqueOrphanedModels = new Set(
    exclusions.orphanedModelRefs.map((item) => item._modelId)
  );

  // Render Report
  return html`<div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
    <h3 style="color: #856404; margin-top: 0;">📊 Data Quality Report</h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #28a745;">${data.flatPairs.length
    }</div>
        <div style="font-size: 14px; color: #666;">Valid Technique Mappings</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: ${uniqueMissingProviders.size > 0 ? "#dc3545" : "#28a745"
    };">${uniqueMissingProviders.size}</div>
        <div style="font-size: 14px; color: #666;">Orphaned Provider IDs</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: ${uniqueOrphanedModels.size > 0 ? "#dc3545" : "#28a745"
    };">${uniqueOrphanedModels.size}</div>
        <div style="font-size: 14px; color: #666;">Orphaned Model IDs</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: ${modelsWithoutTechniques.size > 0 ? "#ffc107" : "#28a745"
    };">${modelsWithoutTechniques.size}</div>
        <div style="font-size: 14px; color: #666;">Models Without Techniques</div>
      </div>
    </div>
    
    <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
      <h4 style="margin-top: 0; color: #495057;">📖 Definitions</h4>
      <ul style="margin: 0; padding-left: 20px; color: #6c757d; font-size: 13px;">
        <li><strong>Orphaned Provider IDs:</strong> Provider IDs referenced in evidence.json but not defined in providers.json</li>
        <li><strong>Orphaned Model IDs:</strong> Model IDs referenced in evidence.json but not defined in models.json</li>
        <li><strong>Models Without Techniques:</strong> Models defined in models.json but with no safety techniques detected or mapped</li>
      </ul>
    </div>
    
    ${uniqueMissingProviders.size > 0
      ? html`
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">🏢 Orphaned Provider IDs (${uniqueMissingProviders.size
        })</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
            These provider IDs appear in evidence.json but are not defined in providers.json. 
            Add them to providers.json or fix the provider field in evidence.json.
          </div>
          ${[...uniqueMissingProviders]
          .map(
            (id) =>
              `<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px;">${id}</code>`
          )
          .join(" ")}
        </div>
      </details>`
      : ""
    }
    
    ${uniqueOrphanedModels.size > 0
      ? html`
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">🤖 Orphaned Model IDs (${uniqueOrphanedModels.size
        })</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
            These model IDs appear in evidence.json but are not defined in models.json. 
            Add them to models.json or fix the modelId references in evidence.json.
          </div>
          ${[...uniqueOrphanedModels]
          .map(
            (id) =>
              `<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px;">${id}</code>`
          )
          .join(" ")}
        </div>
      </details>`
      : ""
    }
    
    ${modelsWithoutTechniques.size > 0
      ? html`
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">⚠️ Models Without Techniques (${modelsWithoutTechniques.size
        })</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
            These models are defined in models.json but have no safety techniques mapped in model_technique_map.json. 
            This may indicate missing documentation analysis or models that haven't been processed yet.
          </div>
          ${[...modelsWithoutTechniques]
          .map(
            (id) =>
              `<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px;">${id}</code>`
          )
          .join(" ")}
        </div>
      </details>`
      : ""
    }
  </div>`;
}


function _exportOptions(html, filteredData, filters) {
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
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `llm-safety-mechanisms-${new Date().toISOString().split("T")[0]
      }.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportCSV = () => {
    // UPDATED: Headers match new data structure
    const headers = [
      "Provider",
      "Category",
      "Technique",
      "Model",
      "Confidence",
      "Source",
      "Source URI",
      "Evidence"
    ];

    const csvData = [
      headers.join(","),
      ...filteredData.map((d) => {
        // Handle evidence array or string, and escape quotes
        let evidenceText = Array.isArray(d.evidence)
          ? d.evidence
            .filter((e) =>
              typeof e === "object" ? e.active !== false : true
            )
            .map((e) => (typeof e === "object" ? e.text : e))
            .filter(Boolean)
            .join(" | ")
          : (typeof d.evidence === "object" ? d.evidence.text : d.evidence) ||
          "";
        evidenceText = evidenceText.replace(/"/g, '""');

        // Map new fields safely
        return [
          `"${d.provider || ""}"`,
          `"${d.category || ""}"`,
          `"${d.technique || ""}"`,
          `"${d.model || ""}"`,
          `"${d.confidence || ""}"`,
          `"${d.source || ""}"`,
          `"${d.source_uri || ""}"`,
          `"${evidenceText}"`
        ].join(",");
      })
    ].join("\n");

    const dataBlob = new Blob([csvData], { type: "text/csv" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `llm-safety-mechanisms-${new Date().toISOString().split("T")[0]
      }.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportConfig = () => {
    const config = {
      // UPDATED: Pluralized keys to match your filter logic
      filters: {
        providers: filters.providers,
        categories: filters.categories,
        techniques: filters.techniques,
        rating: filters.rating,
        search: filters.search
      },
      timestamp: new Date().toISOString(),
      recordCount: filteredData.length
    };

    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `llm-safety-config-${new Date().toISOString().split("T")[0]
      }.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  div.querySelector("#export-json").addEventListener("click", exportJSON);
  div.querySelector("#export-csv").addEventListener("click", exportCSV);
  div.querySelector("#export-config").addEventListener("click", exportConfig);

  return div;
}


function _table(Inputs, filteredData) {
  return (
    Inputs.table(
      filteredData.map((d) => {
        // Extract first evidence snippet if array, handle missing data
        const cleanEvidence = Array.isArray(d.evidence)
          ? d.evidence
            .filter((e) => (typeof e === "object" ? e.active !== false : true))
            .map((e) => (typeof e === "object" ? e.text : e))
            .filter(Boolean)
            .join(" | ") || "No evidence available"
          : (typeof d.evidence === "object" ? d.evidence.text : d.evidence) ||
          "No evidence available";

        return {
          Category: d.category,
          Provider: d.provider,
          Technique: d.technique,
          Model: d.model,
          Confidence: d.confidence, // Renamed from Score to match data
          Source: d.source, // New field
          // Renamed from Description
          Evidence:
            cleanEvidence.length > 100
              ? cleanEvidence.substring(0, 100) + "..."
              : cleanEvidence
        };
      }),
      {
        columns: [
          "Category",
          "Provider",
          "Technique",
          "Model",
          "Confidence",
          "Source",
          "Evidence"
        ],
        // Optional formatting to make the table readable
        width: {
          Evidence: 300,
          Source: 150,
          Model: 150
        },
        layout: "auto"
      }
    )
  )
}

function _19(htl) {
  return (
    htl.html`<hr/>`
  )
}

function _20(md) {
  return (
    md`## Current (& Planned) Activity
This project is under active development. Current priorities include:
* **Improving detection accuracy and improving human review workflows** — [_Underway_] Manual ground-truth labelling against source documentation is underway to empirically tune the semantic matching thresholds. The goal is reliable, automated linking of models to techniques with transparent confidence levels. I'm also running post-labelling analysis to optimise the technique and category taxonomy to minimise overlap (and concept confusability) by the automated linking workflow. 'm also making improvements to the human review user interface with a view to optimising the linking output review workflow - including capture of link origination sources (NLU/LLM/Human) - which will lead into simpler feedback mechanisms (including community-based contributions).
* **Reported Safety Incidents** - [_Planned_] Reported safety incidents linked to models, with a mechanism for public users to submit incidents as well as performing automated scans for them. Recent issues with Grok stand out as an excellent example, as do situations like ChatGPT encouraging risky/dangerous behaviours.
`
  )
}

function _21(htl) {
  return (
    htl.html`<hr/>`
  )
}

function _22(md) {
  return (
    md`## Documentation

### Data Sources
This notebook fetches live data from the following GitHub repository endpoints:
- **Evidence**: \\\`evidence.json\\\` - Points at sources of documentation (and soon, third party analysis) for models. This is used by /scripts/ingest_universal.py to map techniques to models. Metadata for the document ion evidence.json lists the provider and model versions to which it relates.
- **Techniques**: \\\`techniques.json\\\` - Catalog of safety techniques and methodologies. These are expanded with additional semantic content (descriptions, alternative equivalent terminology, etc) to support the automation step which correlates evidence (and related models) with techniques using NLU libraries
- **Providers**: \\\`providers.json\\\` - LLM provider name
- **Models**: \\\`models.json\\\` - Model versions

### Methodology
- **Data Processing**: Documentation sources are converted to flat file using Python (BeautifulSoup), then matched against the semantic concepts captured in techniques.json using vectorization: it uses a Bi-Encoder model (all-mpnet-base-v2) to convert the descriptions of these techniques into mathematical vector embeddings
- **Confidence**: this is calculated via a Cross-Encoder model (nli-deberta-v3-small) trained on Natural Language Inference (NLI). High Confidence: > 80% entailment score, Medium Confidence: > 50% entailment score.
- **Filtering**: Multi-dimensional filtering across providers, techniques, ratings, and free-text search

### Usage Examples

#### Basic Filtering
1. Select a provider from the dropdown to focus on specific implementations
2. Choose a technique type to analyze particular safety approaches
3. Adjust the minimum rating slider to filter by confidence threshold
4. Use the search box for free-text filtering across descriptions

#### Advanced Analytics
- **Provider Comparison**: Compare safety mechanism adoption across providers

#### Data Export
- **JSON Export**: Full structured data with all fields and metadata
- **CSV Export**: Tabular format suitable for spreadsheet analysis
- **Configuration Export**: Save current filter settings for reproducibility

**Repository**: [LLM Safety Mechanisms](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms)  
**License**: MIT  
**Maintainer**: Sasha Agafonoff`
  )
}

function _23(htl) {
  return (
    htl.html`<hr/>`
  )
}

function _24(md) {
  return (
    md`## Supporting Code for Notebook`
  )
}

function _embedAPI(filteredData, d3, URLSearchParams) {
  return {
    // Get chart data for embedding
    getChartData: (type, filters = {}) => {
      let data = filteredData;

      switch (type) {
        case "distribution":
          return data.map((d) => ({ x: d.effectiveness_score, y: 1 }));
        case "provider-comparison":
          return Array.from(
            d3.rollup(
              data,
              (v) => v.length,
              (d) => d.provider_name
            )
          );
        case "technique-effectiveness":
          return Array.from(
            d3.rollup(
              data,
              (v) => d3.mean(v, (d) => d.effectiveness_score),
              (d) => d.technique_name
            )
          );
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
      return `${window.location.origin}${window.location.pathname
        }?${params.toString()}`;
    },

    // Get summary statistics
    getSummaryStats: () => ({
      totalRecords: filteredData.length,
      uniqueProviders: new Set(filteredData.map((d) => d.provider_id)).size,
      uniqueTechniques: new Set(filteredData.map((d) => d.technique_id)).size,
      avgEffectiveness:
        filteredData.reduce((sum, d) => sum + d.effectiveness_score, 0) /
        filteredData.length || 0
    })
  };
}


async function _data(d3) {
  const BASE_URL =
    "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data";

  // 1. Fetch
  const [
    evidence,
    techniques,
    categories,
    techniqueMap,
    models,
    providers,
    lifecycle
  ] = await Promise.all([
    d3.json(`${BASE_URL}/evidence.json`).then((d) => d.sources || d),
    d3.json(`${BASE_URL}/techniques.json`),
    d3.json(`${BASE_URL}/categories.json`),
    d3.json(`${BASE_URL}/model_technique_map.json`),
    d3
      .json(`${BASE_URL}/models.json`)
      .then((d) => d.models || d)
      .catch(() => []),
    d3.json(`${BASE_URL}/providers.json`).catch(() => []),

    d3.json(`${BASE_URL}/model_lifecycle.json`).catch(() => [])
  ]);
  // 2. Lookup Maps
  const techLookup = new Map(techniques.map((t) => [t.id, t]));
  const catLookup = new Map(categories.map((c) => [c.id, c]));

  // 3. Hydrate & Flatten
  const flatPairs = evidence.flatMap((source) => {
    // Try multiple keys to find detections in techniqueMap
    // Priority: 1) source.id, 2) source.url, 3) source.title
    let detections = [];

    if (source.id && techniqueMap[source.id]) {
      detections = techniqueMap[source.id];
    } else if (
      source.url &&
      source.url !== "<missing>" &&
      techniqueMap[source.url]
    ) {
      detections = techniqueMap[source.url];
    } else if (techniqueMap[source.title]) {
      detections = techniqueMap[source.title];
    }

    const modelString =
      source.models && source.models.length > 0
        ? source.models.map((m) => m.modelId).join(", ")
        : source.title;

    return detections
      .map((d) => {
        const def = techLookup.get(d.techniqueId);
        if (!def) return null;
        return {
          provider: source.provider || "Unknown",
          model: modelString,
          technique: def.name,
          category: catLookup.get(def.categoryId)?.name || "Uncategorized",
          confidence: d.confidence,
          source: source.title,
          source_uri: source.url,
          evidence: d.evidence
        };
      })
      .filter((t) => t !== null);
  });

  // 4. Enriched Models
  const enrichedModels = evidence.map((source) => {
    const sourcePairs = flatPairs.filter((p) => p.source === source.title);
    const techniquesList = sourcePairs.map((p) => {
      const techDef = techniques.find((t) => t.name === p.technique);
      return {
        id: techDef?.id,
        name: p.technique,
        category: p.category,
        categoryId: techDef?.categoryId,
        confidence: p.confidence,
        evidence: p.evidence
      };
    });
    return {
      ...source,
      id:
        source.models && source.models.length > 0
          ? source.models[0].modelId
          : source.title.replace(/[^a-zA-Z0-9-_]/g, ""),
      techniqueCount: techniquesList.length,
      techniques: techniquesList
    };
  });

  return {
    raw: {
      evidence,
      techniques,
      categories,
      techniqueMap,
      models,
      providers,
      lifecycle
    },
    enrichedModels,
    flatPairs,
    categories,
    techniques,
    lifecycle
  };
}


function _filteredData(data, filters) {
  // 1. Safety Check: Ensure data is loaded
  if (!data || !data.flatPairs) return [];

  // 2. Start with the Flat List of (Model -> Technique) connections
  let filtered = [...data.flatPairs];

  // Helper map for converting text confidence to numbers for filtering
  const confidenceScore = { High: 3, Medium: 2, Low: 1, Unknown: 0 };

  try {
    // Provider filter
    if (filters && filters.providers && filters.providers.length > 0) {
      // Matches d.provider (String name, e.g. "Meta")
      filtered = filtered.filter((d) => filters.providers.includes(d.provider));
    }

    // Category filter
    if (filters && filters.categories && filters.categories.length > 0) {
      // Matches d.category (String name, e.g. "Alignment")
      filtered = filtered.filter((d) =>
        filters.categories.includes(d.category)
      );
    }

    // Technique filter
    if (filters && filters.techniques && filters.techniques.length > 0) {
      // Matches d.technique (String name, e.g. "Red Teaming")
      filtered = filtered.filter((d) =>
        filters.techniques.includes(d.technique)
      );
    }

    // Rating/Confidence filter (High/Medium/Low)
    if (filters && filters.rating && filters.rating > 0) {
      filtered = filtered.filter(
        (d) => (confidenceScore[d.confidence] || 0) >= filters.rating
      );
    }

    // Search filter
    if (filters && filters.search && filters.search !== "") {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter((d) => {
        // Search across Model, Provider, Technique, and the Evidence Text itself
        const inModel = d.model && d.model.toLowerCase().includes(searchTerm);
        const inProvider =
          d.provider && d.provider.toLowerCase().includes(searchTerm);
        const inTechnique =
          d.technique && d.technique.toLowerCase().includes(searchTerm);
        const inCategory =
          d.category && d.category.toLowerCase().includes(searchTerm);

        // Check array of evidence snippets
        const inEvidence =
          d.evidence &&
          d.evidence.some((txt) => txt.toLowerCase().includes(searchTerm));

        return inModel || inProvider || inTechnique || inCategory || inEvidence;
      });
    }

    return filtered;
  } catch (error) {
    console.error("Error in filtering:", error);
    return data.flatPairs; // Fallback to all data
  }
}


async function _audit(globalThis) {
  const RAW =
    "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data";
  const fetchJSON = async (url) => {
    try {
      return await (await fetch(url, { cache: "no-store" })).json();
    } catch {
      return null;
    }
  };

  // Prefer in-notebook data, else fetch from repo
  const MRAW =
    globalThis.data?.models ?? (await fetchJSON(`${RAW}/models.json`));
  const ERAW =
    globalThis.data?.evidence ?? (await fetchJSON(`${RAW}/evidence.json`));
  const TRAW =
    globalThis.data?.techniques ??
    (await fetchJSON(`${RAW}/techniques.json`)) ??
    [];

  // ---------- helpers ----------
  const norm = (s) =>
    (s ?? "")
      .toString()
      .normalize("NFKC")
      .trim()
      .replace(/[\u2010-\u2015–—−]/g, "-")
      .replace(/\s+/g, " ")
      .replace(/\s*\/\s*/g, "/")
      .replace(/\s*-\s*/g, "-")
      .replace(/_+/g, "-");
  const slug = (s) =>
    norm(s)
      .toLowerCase()
      .replace(/[^a-z0-9.+/-]+/g, "")
      .replace(/-+/g, "-")
      .replace(/^[-/]+|[-/]+$/g, "");

  const pick = (o, ...ks) => {
    for (const k of ks) if (o && o[k] != null) return o[k];
  };
  const get = (o, path) => {
    // shallow dot-path getter (e.g. "model.name")
    if (!o || !path) return undefined;
    return path
      .split(".")
      .reduce((v, k) => (v && v[k] != null ? v[k] : undefined), o);
  };

  const splitId = (id) => {
    if (typeof id !== "string") return [undefined, undefined];
    const s = id.includes(":") ? ":" : id.includes("/") ? "/" : null;
    if (!s) return [undefined, undefined];
    const [p, ...rest] = id.split(s);
    return [p, rest.join(s)];
  };

  const isHttpUrl = (u) => {
    try {
      const x = new URL(u);
      return x.protocol === "http:" || x.protocol === "https:";
    } catch {
      return false;
    }
  };
  const keyFor = (prov, model) => `${slug(prov)}:${slug(model)}`;

  // Coerce various shapes into arrays
  const coerceArray = (raw, { assumeProviderBuckets = false } = {}) => {
    if (!raw) return [];
    if (Array.isArray(raw)) return raw;

    for (const k of ["models", "evidence", "records", "items", "data"])
      if (Array.isArray(raw[k])) return raw[k];

    if (
      assumeProviderBuckets ||
      (raw &&
        typeof raw === "object" &&
        Object.values(raw).every((v) => typeof v === "object"))
    ) {
      const rows = [];
      for (const [bucket, val] of Object.entries(raw)) {
        if (Array.isArray(val))
          for (const r of val) rows.push({ ...r, _bucket: bucket });
        else if (val) rows.push({ ...val, _bucket: bucket });
      }
      if (rows.length) return rows;
    }

    const vals = Object.values(raw);
    if (vals.length && vals.every((v) => typeof v === "object")) return vals;

    return [];
  };

  // ---------- MODELS ----------
  const modelsRaw = coerceArray(MRAW, { assumeProviderBuckets: true });
  const models = modelsRaw
    .map((m, i) => {
      const idLike = pick(m, "id", "key", "slug", "model_id", "modelKey");
      let provider =
        pick(m, "provider", "vendor", "org", "developer", "company") ??
        m._bucket;
      let model = pick(m, "model", "name", "model_name", "title");
      if ((!provider || !model) && idLike) {
        const [p, rest] = splitId(idLike);
        if (p && rest) {
          provider = provider ?? p;
          model = model ?? rest;
        }
      }
      // also try nested model object
      provider = provider ?? get(m, "model.provider");
      model = model ?? get(m, "model.name") ?? get(m, "model.id");
      if (!provider || !model) return null;
      const key = keyFor(provider, model);
      return {
        i,
        key,
        provider,
        model,
        family: pick(m, "family", "series"),
        version: pick(m, "version"),
        _raw: m
      };
    })
    .filter(Boolean);

  const modelByKey = new Map(models.map((m) => [m.key, m]));

  // ---------- EVIDENCE ----------
  const evidenceRaw = coerceArray(ERAW, { assumeProviderBuckets: true });

  const extractTechs = (e) => {
    const set = new Set();
    const tSingle = pick(
      e,
      "technique",
      "technique_id",
      "technique_slug",
      "safety_technique",
      "tech",
      "tech_id",
      "tech_slug"
    );
    const tArray = pick(
      e,
      "techniques",
      "techs",
      "tags",
      "technique_slugs",
      "technique_ids",
      "mechanisms",
      "safety_mechanisms"
    );
    if (tSingle) set.add(slug(tSingle));
    if (Array.isArray(tArray)) {
      for (const t of tArray) {
        if (!t) continue;
        if (typeof t === "string") set.add(slug(t));
        else set.add(slug(pick(t, "id", "slug", "name") ?? JSON.stringify(t)));
      }
    }
    return [...set];
  };

  const ev = evidenceRaw.map((e, i) => {
    // Try explicit fields first
    let provider = pick(e, "provider", "vendor", "org") ?? e._bucket;
    let model = pick(e, "model", "model_name", "name", "title", "id", "slug");

    // If not present, infer from combined id/key OR nested
    const idLike = pick(
      e,
      "model_id",
      "model_key",
      "modelId",
      "modelKey",
      "target_model",
      "target",
      "id",
      "key"
    );
    if ((!provider || !model) && typeof idLike === "string") {
      const [p, rest] = splitId(idLike);
      if (p && rest) {
        provider = provider ?? p;
        model = model ?? rest;
      }
    }
    if (!provider || !model) {
      provider = provider ?? get(e, "model.provider");
      model = model ?? get(e, "model.name") ?? get(e, "model.id");
    }

    const url = pick(e, "url", "source_url", "href");
    const claim = pick(e, "claim", "summary", "note", "description");
    const status = pick(e, "status", "state");
    const techs = extractTechs(e);

    const key = provider && model ? keyFor(provider, model) : undefined;

    return {
      i,
      key,
      provider,
      model,
      techniques: techs,
      url,
      urlOk: isHttpUrl(url),
      status,
      claim,
      _raw: e
    };
  });

  // ---------- Techniques universe ----------
  const techCatalog = Array.from(
    new Set(
      (Array.isArray(TRAW) ? TRAW : coerceArray(TRAW))
        .map((t) => pick(t, "id", "slug", "name"))
        .filter(Boolean)
        .map(slug)
    )
  ).sort();

  const techInEvidence = Array.from(
    new Set(ev.flatMap((d) => d.techniques))
  ).sort();
  const techUniverse = techCatalog.length ? techCatalog : techInEvidence;

  // ---------- Indexes & buckets ----------
  const evidenceByModel = new Map();
  for (const e of ev) {
    if (!e.key) continue;
    if (!evidenceByModel.has(e.key)) evidenceByModel.set(e.key, []);
    evidenceByModel.get(e.key).push(e);
  }

  const modelsWithoutEvidence = models.filter(
    (m) => !evidenceByModel.has(m.key)
  );
  const orphanEvidence = ev.filter((e) => e.key && !modelByKey.has(e.key));
  const providerOnlyEvidence = ev.filter((e) => !e.model && e.provider);
  const evidenceWithoutModelKey = ev.filter(
    (e) =>
      !e.key &&
      (e.provider || e.model || pick(e, "model_id", "model_key", "id", "key"))
  );

  const invalidUrls = ev.filter((e) => e.url !== undefined && !e.urlOk);
  const missingTechnique = ev.filter((e) => (e.techniques?.length ?? 0) === 0);
  const missingProviderOrModel = ev.filter((e) => !e.provider || !e.model);

  // duplicates (same model key + technique + url)
  const dupeMap = new Map();
  for (const e of ev) {
    const techs = e.techniques.length ? e.techniques : ["no-tech"];
    for (const t of techs) {
      const k = JSON.stringify({
        key:
          e.key ??
          `prov:${slug(e.provider ?? "")}-model:${slug(e.model ?? "")}`,
        tech: t,
        url: e.url ? norm(e.url) : "no-url"
      });
      if (!dupeMap.has(k)) dupeMap.set(k, []);
      dupeMap.get(k).push(e);
    }
  }
  const duplicateEvidence = Array.from(dupeMap.values()).filter(
    (g) => g.length > 1
  );

  // provider mismatches (only detectable when model exists)
  const providerMismatches = ev
    .filter((e) => e.key && modelByKey.has(e.key) && e.provider)
    .filter((e) => slug(e.provider) !== slug(modelByKey.get(e.key).provider))
    .map((e) => {
      const m = modelByKey.get(e.key);
      return {
        evidence_index: e.i,
        evidence_provider: e.provider,
        model_provider: m?.provider,
        model: m?.model,
        key: e.key
      };
    });

  // ---------- Coverage ----------
  const coverageByModel = models.map((m) => {
    const list = evidenceByModel.get(m.key) ?? [];
    const present = Array.from(
      new Set(list.flatMap((e) => e.techniques))
    ).sort();
    const missing = techUniverse.filter((t) => !present.includes(t));
    return {
      key: m.key,
      provider: m.provider,
      model: m.model,
      evidence_count: list.length,
      techniques_present: present,
      techniques_missing_relative_to_universe: missing
    };
  });

  const coverageByTechnique = techUniverse
    .map((t) => {
      const have = new Set(
        ev
          .filter(
            (e) =>
              (e.techniques || []).includes(t) && e.key && modelByKey.has(e.key)
          )
          .map((e) => e.key)
      );
      const missing = models
        .filter((m) => !have.has(m.key))
        .map((m) => ({ key: m.key, provider: m.provider, model: m.model }));
      return {
        technique: t,
        count_missing: missing.length,
        models_missing: missing
      };
    })
    .sort((a, b) => b.count_missing - a.count_missing);

  // ---------- Summary ----------
  const summary = {
    models_shape: Array.isArray(MRAW)
      ? "array"
      : MRAW && typeof MRAW === "object"
        ? "object"
        : typeof MRAW,
    evidence_shape: Array.isArray(ERAW)
      ? "array"
      : ERAW && typeof ERAW === "object"
        ? "object"
        : typeof ERAW,
    models_total: models.length,
    evidence_total: ev.length,
    techniques_in_catalog: techCatalog.length,
    techniques_in_evidence: techInEvidence.length,
    technique_universe_size: techUniverse.length,
    models_with_evidence: models.length - modelsWithoutEvidence.length,
    models_without_evidence: modelsWithoutEvidence.length,
    orphan_evidence_count: orphanEvidence.length,
    provider_only_evidence_count: providerOnlyEvidence.length,
    evidence_without_modelkey_count: evidenceWithoutModelKey.length,
    duplicate_groups: duplicateEvidence.length,
    invalid_url_count: invalidUrls.length,
    missing_technique_count: missingTechnique.length,
    missing_provider_or_model_count: missingProviderOrModel.length,
    provider_mismatch_count: providerMismatches.length
  };

  return {
    summary,
    coverageByModel,
    coverageByTechnique,
    modelsWithoutEvidence,
    orphanEvidence,
    providerOnlyEvidence,
    evidenceWithoutModelKey,
    duplicateEvidence,
    invalidUrls,
    missingTechnique,
    missingProviderOrModel,
    providerMismatches,
    _models: models.map(({ _raw, ...r }) => r),
    _evidence: ev.map(({ _raw, ...r }) => r),
    _techUniverse: techUniverse
  };
}


function _29(md) {
  return (
    md`## Aesthetic Bits`
  )
}

async function _colorSchemes(d3) {
  const baseUrl =
    "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data/";

  const [categories, providers] = await Promise.all([
    fetch(`${baseUrl}categories.json`).then((d) => d.json()),
    fetch(`${baseUrl}providers.json`).then((d) => d.json())
  ]);

  const categoryNames = categories.map((c) => c.name).sort();
  const providerNames = providers.map((p) => p.name).sort();

  // Use consistent color generation for both
  const generateColors = (items, saturation = 0.7, lightness = 0.5) => {
    const colorMap = {};
    const hueStep = 360 / items.length;
    items.forEach((item, i) => {
      colorMap[item] = d3.hsl(i * hueStep, saturation, lightness).toString();
    });
    return colorMap;
  };

  return {
    categories: generateColors(categoryNames, 0.6, 0.55),
    providers: generateColors(providerNames, 0.5, 0.6)
  };
}


function _categoryColors(colorSchemes) {
  return (
    colorSchemes.categories
  )
}

function _providerColors(colorSchemes) {
  return (
    colorSchemes.providers
  )
}

function _33(md) {
  return (
    md`## Document Map Code`
  )
}

function _networkConfig() {
  return (
    {
      width: 1000,
      height: 1000,
      centerX: 400,
      centerY: 350,
      providerRadius: 100,
      modelRadius: 200,
      evidenceRadius: 300,
      nodeRadius: {
        provider: 20,
        model: 8
      },
      evidenceRect: {
        width: 14,
        height: 24
      },
      colors: {
        model: "#457b9d",
        evidence: "#e9ecef",
        evidenceBorder: "#adb5bd"
      },
      linkColors: {
        owns: "#888",
        documents: "#888"
      }
    }
  )
}

function _networkGraph(data) {
  const nodes = [];
  const links = [];
  const nodeSet = new Set();

  // Track which models have evidence and which evidence has models
  const modelsWithEvidence = new Set();
  const evidenceWithModels = new Set();

  // First pass: identify all model-evidence relationships
  data.raw.evidence.forEach((source) => {
    if (source.models && source.models.length > 0) {
      source.models.forEach((m) => {
        modelsWithEvidence.add(m.modelId);
      });
      evidenceWithModels.add(
        source.id || source.title.replace(/[^a-zA-Z0-9]/g, "-")
      );
    }
  });

  // Create lookup from provider ID to name for color matching
  const providerIdToName = new Map(
    data.raw.providers.map((p) => [p.id, p.name])
  );

  // 1. Create Provider nodes
  data.raw.providers.forEach((provider) => {
    const nodeId = `provider:${provider.id}`;
    if (!nodeSet.has(nodeId)) {
      nodeSet.add(nodeId);
      nodes.push({
        id: nodeId,
        label: provider.name,
        type: "provider",
        providerId: provider.id,
        providerName: provider.name,
        headquarters: provider.headquarters,
        providerType: provider.type
      });
    }
  });

  // 2. Create Model nodes (deduplicated across all evidence)
  const modelMap = new Map();
  data.raw.evidence.forEach((source) => {
    if (source.models && source.models.length > 0) {
      source.models.forEach((m) => {
        if (!modelMap.has(m.modelId)) {
          modelMap.set(m.modelId, {
            name: m.name || m.modelId,
            providerId: source.provider,
            providerName: providerIdToName.get(source.provider)
          });
        }
      });
    }
  });

  modelMap.forEach((info, modelId) => {
    const nodeId = `model:${modelId}`;
    if (!nodeSet.has(nodeId)) {
      nodeSet.add(nodeId);
      nodes.push({
        id: nodeId,
        label: info.name,
        type: "model",
        providerId: info.providerId,
        providerName: info.providerName,
        isOrphan: !modelsWithEvidence.has(modelId) // Model has no evidence
      });
      const providerNodeId = `provider:${info.providerId}`;
      if (nodeSet.has(providerNodeId)) {
        links.push({
          source: providerNodeId,
          target: nodeId,
          type: "owns"
        });
      }
    }
  });

  // 3. Create Evidence (document) nodes and link to models
  data.raw.evidence.forEach((source) => {
    const evidenceId = `evidence:${source.id || source.title.replace(/[^a-zA-Z0-9]/g, "-")
      }`;
    const hasValidModels = source.models && source.models.length > 0;

    if (!nodeSet.has(evidenceId)) {
      nodeSet.add(evidenceId);
      nodes.push({
        id: evidenceId,
        label: source.title,
        type: "evidence",
        docType: source.type,
        providerId: source.provider,
        providerName: providerIdToName.get(source.provider),
        url: source.url,
        modelCount: source.models ? source.models.length : 0,
        isOrphan: !hasValidModels // Evidence has no models
      });
    }

    if (hasValidModels) {
      source.models.forEach((m) => {
        const modelNodeId = `model:${m.modelId}`;
        if (nodeSet.has(modelNodeId)) {
          links.push({
            source: evidenceId,
            target: modelNodeId,
            type: "documents"
          });
        }
      });
    }
  });

  return { nodes, links };
}


function _layoutStorageKey() {
  return (
    "network-graph-layout-v1"
  )
}

function _defaultLayout(FileAttachment) {
  return (
    FileAttachment("network-layout.json").json()
  )
}

function _positionedGraph(networkGraph, validatedLayout, networkConfig, d3) {
  const { nodes, links } = networkGraph;
  const { layout, source, stats } = validatedLayout;
  const { centerX, centerY, providerRadius, modelRadius, evidenceRadius } =
    networkConfig;

  // Group nodes by type
  const providers = nodes.filter((n) => n.type === "provider");
  const models = nodes.filter((n) => n.type === "model");
  const evidence = nodes.filter((n) => n.type === "evidence");

  // Create provider angle mapping for radial fallback
  const providerAngles = new Map();
  const angleStep = (2 * Math.PI) / providers.length;
  providers.forEach((p, i) => {
    const angle = i * angleStep - Math.PI / 2;
    providerAngles.set(p.providerId, angle);
    p.angle = angle;
    p.x = centerX + providerRadius * Math.cos(angle);
    p.y = centerY + providerRadius * Math.sin(angle);
  });

  // Position models by provider
  const modelsByProvider = d3.group(models, (d) => d.providerId);
  modelsByProvider.forEach((providerModels, providerId) => {
    const providerAngle = providerAngles.get(providerId);
    if (providerAngle === undefined) return;
    const arcSpread = angleStep * 0.7;
    const modelAngleStep =
      providerModels.length > 1 ? arcSpread / (providerModels.length - 1) : 0;
    const startAngle = providerAngle - arcSpread / 2;
    providerModels.forEach((m, i) => {
      const angle =
        providerModels.length > 1
          ? startAngle + i * modelAngleStep
          : providerAngle;
      m.angle = angle;
      m.x = centerX + modelRadius * Math.cos(angle);
      m.y = centerY + modelRadius * Math.sin(angle);
    });
  });

  // Position evidence by provider
  const evidenceByProvider = d3.group(evidence, (d) => d.providerId);
  evidenceByProvider.forEach((providerEvidence, providerId) => {
    const providerAngle = providerAngles.get(providerId);
    if (providerAngle === undefined) return;
    const arcSpread = angleStep * 0.8;
    const evidenceAngleStep =
      providerEvidence.length > 1
        ? arcSpread / (providerEvidence.length - 1)
        : 0;
    const startAngle = providerAngle - arcSpread / 2;
    providerEvidence.forEach((e, i) => {
      const angle =
        providerEvidence.length > 1
          ? startAngle + i * evidenceAngleStep
          : providerAngle;
      e.angle = angle;
      e.x = centerX + evidenceRadius * Math.cos(angle);
      e.y = centerY + evidenceRadius * Math.sin(angle);
    });
  });

  // Apply validated layout positions (overrides radial for known nodes)
  let applied = 0;
  if (layout) {
    nodes.forEach((n) => {
      const saved = layout[n.id];
      if (
        saved &&
        typeof saved.x === "number" &&
        typeof saved.y === "number" &&
        isFinite(saved.x) &&
        isFinite(saved.y)
      ) {
        n.x = saved.x;
        n.y = saved.y;
        applied++;
      }
    });
    stats.applied = applied;
    console.info(
      `Layout (${source}): ${applied} applied, ` +
      `${stats.stale} stale removed, ${stats.newNodes} new nodes`
    );
  }

  // Resolve links against live nodes only
  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  const resolvedLinks = links
    .map((l) => ({
      source: nodeById.get(l.source) || l.source,
      target: nodeById.get(l.target) || l.target,
      type: l.type
    }))
    .filter(
      (l) =>
        l.source &&
        l.target &&
        typeof l.source.x === "number" &&
        typeof l.target.x === "number"
    );

  // Count orphans
  const orphanModels = models.filter((m) => m.isOrphan).length;
  const orphanEvidence = evidence.filter((e) => e.isOrphan).length;

  return {
    nodes,
    providers,
    models,
    evidence,
    resolvedLinks,
    nodeById,
    orphanModels,
    orphanEvidence
  };
}


function _autoLayout(networkGraph, networkConfig, d3) {
  const { nodes, links } = networkGraph;
  const { width, height, nodeRadius, evidenceRect } = networkConfig;

  // Group nodes by type
  const providers = nodes.filter((n) => n.type === "provider");
  const models = nodes.filter((n) => n.type === "model");
  const evidence = nodes.filter((n) => n.type === "evidence");

  // Group models and evidence by provider
  const modelsByProvider = d3.group(models, (d) => d.providerId);
  const evidenceByProvider = d3.group(evidence, (d) => d.providerId);

  // Build provider groups with sizing info
  const providerGroups = providers.map((p) => {
    const pModels = modelsByProvider.get(p.providerId) || [];
    const pEvidence = evidenceByProvider.get(p.providerId) || [];
    const rowCount = Math.max(pModels.length, pEvidence.length, 1);
    return { provider: p, models: pModels, evidence: pEvidence, rowCount };
  });

  // Layout constants — tuned for 1000px wide chart
  const groupGapY = 25; // vertical gap between provider groups
  const modelRowHeight = 22; // vertical spacing per model row
  const evidenceRowHeight = 24; // slightly taller for evidence (extra gap)
  const groupPaddingY = 8; // top/bottom padding within a group
  const colGap = 40; // horizontal gap between the two major columns
  const providerColX = 0; // provider node x offset within group
  const modelColX = 70; // model column x offset within group
  const evidenceColX = 190; // evidence column x offset within group
  const groupWidth = 460; // width of one provider group

  // Calculate each group's height based on whichever column is taller
  providerGroups.forEach((g) => {
    const modelHeight = g.models.length * modelRowHeight;
    const evidenceHeight = g.evidence.length * evidenceRowHeight;
    g.height =
      Math.max(modelHeight, evidenceHeight, modelRowHeight) + groupPaddingY * 2;
  });

  // --- Balanced column distribution via LPT scheduling ---
  const sorted = [...providerGroups].sort((a, b) => b.height - a.height);

  const col1Groups = [];
  const col2Groups = [];
  let col1Height = 0;
  let col2Height = 0;

  for (const g of sorted) {
    const h1 = col1Height + (col1Groups.length > 0 ? groupGapY : 0) + g.height;
    const h2 = col2Height + (col2Groups.length > 0 ? groupGapY : 0) + g.height;

    if (h1 <= h2) {
      col1Groups.push(g);
      col1Height = h1;
    } else {
      col2Groups.push(g);
      col2Height = h2;
    }
  }

  // Re-sort each column so largest groups are at top
  col1Groups.sort((a, b) => b.rowCount - a.rowCount);
  col2Groups.sort((a, b) => b.rowCount - a.rowCount);

  // Recalculate actual column heights after re-sorting
  const col1TotalHeight = col1Groups.reduce(
    (sum, g, i) => sum + g.height + (i > 0 ? groupGapY : 0),
    0
  );
  const col2TotalHeight = col2Groups.reduce(
    (sum, g, i) => sum + g.height + (i > 0 ? groupGapY : 0),
    0
  );

  // Column x positions — center within the available width
  const totalWidth = groupWidth * 2 + colGap;
  const startX = (width - totalWidth) / 2;
  const col1X = startX;
  const col2X = startX + groupWidth + colGap;

  // Position nodes within each column
  function layoutColumn(groups, baseX, totalH) {
    let y = (height - totalH) / 2;

    groups.forEach((g) => {
      const { provider, models: pModels, evidence: pEvidence } = g;

      // Provider node: vertically centered within its group
      const groupCenterY = y + g.height / 2;
      provider.x = baseX + providerColX;
      provider.y = groupCenterY;
      // Label hint: provider labels go LEFT of node
      provider.labelAnchor = "end";

      // Models: vertically centered within group using model row height
      const modelBlockHeight = pModels.length * modelRowHeight;
      const modelStartY =
        y + (g.height - modelBlockHeight) / 2 + modelRowHeight / 2;
      pModels.forEach((m, i) => {
        m.x = baseX + modelColX;
        m.y = modelStartY + i * modelRowHeight;
        // Label hint: model labels go LEFT of node
        m.labelAnchor = "end";
      });

      // Evidence: vertically centered within group using evidence row height
      const evidenceBlockHeight = pEvidence.length * evidenceRowHeight;
      const evidenceStartY =
        y + (g.height - evidenceBlockHeight) / 2 + evidenceRowHeight / 2;
      pEvidence.forEach((e, i) => {
        e.x = baseX + evidenceColX;
        e.y = evidenceStartY + i * evidenceRowHeight;
        // Label hint: evidence labels go RIGHT of node
        e.labelAnchor = "start";
      });

      y += g.height + groupGapY;
    });
  }

  layoutColumn(col1Groups, col1X, col1TotalHeight);
  layoutColumn(col2Groups, col2X, col2TotalHeight);

  // Build the layout map
  const layout = {};
  nodes.forEach((n) => {
    layout[n.id] = { x: n.x, y: n.y };
  });

  return layout;
}


function _validatedLayout(networkGraph, localStorage, layoutStorageKey, defaultLayout) {
  const { nodes } = networkGraph;
  const liveNodeIds = new Set(nodes.map((n) => n.id));

  let layout = null;
  let source = "default";
  let stats = { applied: 0, stale: 0, newNodes: 0 };

  // Try localStorage first
  try {
    const saved = localStorage.getItem(layoutStorageKey);
    if (saved) {
      layout = JSON.parse(saved);
      source = "saved";
    }
  } catch (e) {
    console.warn("Could not load saved layout:", e);
  }

  // Fall back to attached default
  if (!layout && defaultLayout) {
    layout = JSON.parse(JSON.stringify(defaultLayout));
    source = "attached";
  }

  if (layout) {
    // Remove stale entries (nodes no longer in live data)
    const staleIds = Object.keys(layout).filter((id) => !liveNodeIds.has(id));
    staleIds.forEach((id) => delete layout[id]);
    stats.stale = staleIds.length;
    if (staleIds.length > 0) {
      console.warn(
        `Layout cleanup: removed ${staleIds.length} stale node(s):`,
        staleIds
      );
    }

    // Identify new nodes not in saved layout
    const savedIds = new Set(Object.keys(layout));
    const newNodeIds = nodes
      .filter((n) => !savedIds.has(n.id))
      .map((n) => n.id);
    stats.newNodes = newNodeIds.length;
    if (newNodeIds.length > 0) {
      console.info(
        `Layout: ${newNodeIds.length} new node(s) will use radial positions:`,
        newNodeIds
      );
    }
  }

  return { layout, source, stats };
}


function _savedLayout(localStorage, layoutStorageKey) {
  try {
    const saved = localStorage.getItem(layoutStorageKey);
    return saved ? JSON.parse(saved) : null;
  } catch (e) {
    return null;
  }
}


function _42(md) {
  return (
    md`## Unified Chart Code`
  )
}

function _unifiedChartConfig() {
  return (
    {
      width: 1100,
      height: 900,

      // Technique nodes
      techniqueSpacingY: 22,
      techniqueSymbolSize: 150,

      // Category nodes
      categoryPadding: 15,
      categoryRadius: 8,
      categoryMinWidth: 120,
      categoryHeight: 35,
      categoryTechGap: 20,
      categoryGroupGap: 30,

      // Provider nodes
      providerRadius: 10,
      providerSpacing: 30,

      // Labels
      labelFontSize: "12px",
      categoryFontSize: "14px",
      labelBgOpacity: 0.6,
      labelPadding: 4,
      labelOffset: 15,

      // Margins for the default balanced layout
      nodeMargins: {
        left: 80,
        right: 80,
        top: 60,
        bottom: 80
      },

      // Sequential layout column positions (fractions of width)
      sequentialColumns: {
        category: 0.12,
        technique: 0.45,
        provider: 0.82
      },

      // Force simulation defaults (applied to selected nodes only)
      force: {
        linkDistanceProviderTechnique: 120,
        linkDistanceCategoryTechnique: 40,
        linkStrengthProviderTechnique: 0.2,
        linkStrengthCategoryTechnique: 0.6,
        chargeProvider: -60,
        chargeTechnique: -25,
        chargeCategory: 0,
        collideProvider: 20,
        collideTechnique: 10,
        alphaDecay: 0.03,
        velocityDecay: 0.4
      }
    }
  )
}

function _unifiedLayoutStorageKey() {
  return (
    "unified-chart-layout-v1"
  )
}

function _unifiedChartData(unifiedChartConfig, providerColors, data, filteredData, categoryColors, d3) {
  const config = unifiedChartConfig;

  // --- Color helpers ---
  function getProviderColor(providerName) {
    if (!providerName) return "#999";
    if (providerColors[providerName]) return providerColors[providerName];
    const keys = Object.keys(providerColors);
    const match = keys.find(
      (k) => k.toLowerCase() === providerName.toLowerCase()
    );
    return match ? providerColors[match] : "#999";
  }

  function darkenColor(hex, amount = 40) {
    const num = parseInt(hex.replace("#", ""), 16);
    const r = Math.max(0, (num >> 16) - amount);
    const g = Math.max(0, ((num >> 8) & 0x00ff) - amount);
    const b = Math.max(0, (num & 0x0000ff) - amount);
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
  }

  // --- Build category ID → name lookup from full dataset ---
  const catLookup = new Map(data.categories.map((c) => [c.id, c.name]));

  // --- Build the FULL technique list grouped by category (from data.techniques) ---
  const allTechniquesByCategory = new Map();
  data.techniques.forEach((t) => {
    const catName = catLookup.get(t.categoryId) || "Uncategorized";
    if (!allTechniquesByCategory.has(catName)) {
      allTechniquesByCategory.set(catName, []);
    }
    allTechniquesByCategory.get(catName).push(t.name);
  });

  // Sort and deduplicate techniques within each category
  allTechniquesByCategory.forEach((techs, cat) => {
    allTechniquesByCategory.set(cat, [...new Set(techs)].sort());
  });

  // All categories that have at least one technique
  const allCategories = [...allTechniquesByCategory.keys()].sort();

  // --- Providers come from filteredData (only those with evidence in current filter) ---
  const selectedProviders = [
    ...new Set(filteredData.map((d) => d.provider))
  ].sort();

  // --- Build provider→category→technique→evidence lookup from filteredData ---
  const evidenceLookup = {};
  filteredData.forEach((evidence) => {
    const { provider, category, technique } = evidence;
    if (!evidenceLookup[provider]) evidenceLookup[provider] = {};
    if (!evidenceLookup[provider][category])
      evidenceLookup[provider][category] = {};
    if (!evidenceLookup[provider][category][technique]) {
      evidenceLookup[provider][category][technique] = [];
    }
    evidenceLookup[provider][category][technique].push({
      ...evidence,
      evidenceTexts: Array.isArray(evidence.evidence)
        ? evidence.evidence.map((e) =>
          typeof e === "string" ? e : e.text || e.snippet || JSON.stringify(e)
        )
        : evidence.evidence
          ? [
            typeof evidence.evidence === "string"
              ? evidence.evidence
              : JSON.stringify(evidence.evidence)
          ]
          : []
    });
  });

  // --- Build category groups using the FULL technique list ---
  const categoryGroups = allCategories.map((cat) => {
    const techniques = allTechniquesByCategory.get(cat) || [];
    const groupHeight =
      config.categoryHeight +
      config.categoryTechGap +
      techniques.length * config.techniqueSpacingY;
    return { name: cat, techniques, groupHeight };
  });

  // --- Measure text helper ---
  function measureText(text, fontSize = "14px", fontWeight = "bold") {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    context.font = `${fontWeight} ${fontSize} sans-serif`;
    return context.measureText(text).width;
  }

  // --- Build graph nodes and links ---
  const nodes = [];
  const links = [];
  const nodeById = new Map();

  // Provider nodes
  selectedProviders.forEach((provider) => {
    const node = {
      id: `provider-${provider}`,
      name: provider,
      type: "provider",
      color: getProviderColor(provider),
      x: 0,
      y: 0
    };
    nodes.push(node);
    nodeById.set(node.id, node);
  });

  // Category and technique nodes — from the FULL technique catalogue
  allCategories.forEach((category) => {
    const textWidth = measureText(category);
    const nodeWidth = Math.max(
      textWidth + config.categoryPadding * 2,
      config.categoryMinWidth
    );
    const catColor = categoryColors[category] || "#666";

    const categoryNode = {
      id: `category-${category}`,
      name: category,
      type: "category",
      color: catColor,
      width: nodeWidth,
      height: config.categoryHeight,
      x: 0,
      y: 0
    };
    nodes.push(categoryNode);
    nodeById.set(categoryNode.id, categoryNode);

    const techniques = allTechniquesByCategory.get(category) || [];
    techniques.forEach((techName) => {
      const techId = `technique-${category}-${techName}`;

      // Check if any provider in the current filter has evidence for this technique
      let hasEvidence = false;
      selectedProviders.forEach((provider) => {
        if (evidenceLookup[provider]?.[category]?.[techName]) {
          hasEvidence = true;
        }
      });

      const techNode = {
        id: techId,
        name: techName,
        type: "technique",
        category: category,
        color: catColor,
        isOrphan: !hasEvidence,
        x: 0,
        y: 0
      };
      nodes.push(techNode);
      nodeById.set(techId, techNode);

      // Category → technique link
      links.push({
        source: categoryNode.id,
        target: techId,
        type: "category-technique",
        color: darkenColor(catColor, 40)
      });

      // Provider → technique links (only where evidence exists)
      selectedProviders.forEach((provider) => {
        const evidenceList = evidenceLookup[provider]?.[category]?.[techName];
        if (evidenceList && evidenceList.length > 0) {
          links.push({
            source: `provider-${provider}`,
            target: techId,
            type: "provider-technique",
            color: d3.color(getProviderColor(provider)).darker(0.4).toString(),
            data: evidenceList[0]
          });
        }
      });
    });
  });

  return {
    nodes,
    links,
    nodeById,
    selectedProviders,
    selectedCategories: allCategories,
    categoryGroups,
    techniquesByCategory: allTechniquesByCategory,
    evidenceLookup,
    getProviderColor,
    darkenColor,
    measureText
  };
}


function _unifiedChartLayouts(unifiedChartConfig, d3) {
  const config = unifiedChartConfig;

  // ==========================================================
  // BALANCED LAYOUT (default)
  // Categories distributed left/right via LPT scheduling,
  // techniques hanging below each category,
  // providers in a centered column.
  // ==========================================================
  function balancedLayout(chartData) {
    const {
      nodes,
      nodeById,
      categoryGroups,
      selectedProviders,
      selectedCategories
    } = chartData;
    const { width, height } = config;
    const positions = {};
    const labelAnchors = {};

    // --- LPT scheduling: distribute category groups across two columns ---
    const sorted = [...categoryGroups].sort(
      (a, b) => b.groupHeight - a.groupHeight
    );
    const leftGroups = [];
    const rightGroups = [];
    let leftHeight = 0;
    let rightHeight = 0;

    for (const group of sorted) {
      const addedHeight = group.groupHeight + config.categoryGroupGap;
      if (leftHeight <= rightHeight) {
        leftGroups.push(group);
        leftHeight += addedHeight;
      } else {
        rightGroups.push(group);
        rightHeight += addedHeight;
      }
    }

    // Re-sort within each column alphabetically for stability
    leftGroups.sort((a, b) => a.name.localeCompare(b.name));
    rightGroups.sort((a, b) => a.name.localeCompare(b.name));

    // Column height calculator
    const colHeight = (groups) =>
      groups.reduce(
        (sum, g, i) =>
          sum + g.groupHeight + (i > 0 ? config.categoryGroupGap : 0),
        0
      );

    // --- Position categories and their techniques ---
    function layoutColumn(groups, xCenter, isLeft) {
      const totalH = colHeight(groups);
      let y = (height - totalH) / 2 + config.nodeMargins.top;

      groups.forEach((group) => {
        const catId = `category-${group.name}`;
        positions[catId] = { x: xCenter, y: y + config.categoryHeight / 2 };
        labelAnchors[catId] = "middle";

        group.techniques.forEach((techName, i) => {
          const techId = `technique-${group.name}-${techName}`;
          const techY =
            y +
            config.categoryHeight +
            config.categoryTechGap +
            i * config.techniqueSpacingY;
          positions[techId] = { x: xCenter, y: techY };
          // Left half: text right-aligned adjacent to LEFT of node
          // Right half: text left-aligned adjacent to RIGHT of node
          labelAnchors[techId] = isLeft ? "end" : "start";
        });

        y += group.groupHeight + config.categoryGroupGap;
      });
    }

    const leftX = config.nodeMargins.left + config.categoryMinWidth / 2 + 60;
    const rightX =
      width - config.nodeMargins.right - config.categoryMinWidth / 2 - 60;

    layoutColumn(leftGroups, leftX, true);
    layoutColumn(rightGroups, rightX, false);

    // --- Providers in center column ---
    const centerX = width / 2;
    const providerBlockHeight =
      selectedProviders.length * config.providerSpacing;
    const providerStartY =
      (height - providerBlockHeight) / 2 + config.providerSpacing / 2;

    selectedProviders.forEach((provider, i) => {
      const pid = `provider-${provider}`;
      positions[pid] = {
        x: centerX,
        y: providerStartY + i * config.providerSpacing
      };
      labelAnchors[pid] = "start";
    });

    return { positions, labelAnchors, layoutName: "balanced" };
  }

  // ==========================================================
  // SEQUENTIAL LAYOUT (3-column)
  // Categories | Techniques | Providers
  // Text below techniques (centered), text right of providers
  // ==========================================================
  function sequentialLayout(chartData) {
    const { nodes, nodeById, categoryGroups, selectedProviders } = chartData;
    const { width, height } = config;
    const positions = {};
    const labelAnchors = {};

    const colX = {
      category: width * config.sequentialColumns.category,
      technique: width * config.sequentialColumns.technique,
      provider: width * config.sequentialColumns.provider
    };

    // Adaptive spacing: fit all techniques vertically
    const allTechniqueCount = categoryGroups.reduce(
      (sum, g) => sum + g.techniques.length,
      0
    );
    const techSpacing = Math.min(
      config.techniqueSpacingY,
      (height - 100) / Math.max(allTechniqueCount, 1)
    );

    // Categories and techniques
    const catPositions = [];
    let catY = config.nodeMargins.top + 20;

    categoryGroups.forEach((group) => {
      positions[`category-${group.name}`] = { x: colX.category, y: catY };
      labelAnchors[`category-${group.name}`] = "middle";
      catPositions.push({
        name: group.name,
        y: catY,
        techniques: group.techniques
      });
      catY +=
        config.categoryHeight +
        config.categoryGroupGap +
        group.techniques.length * techSpacing;
    });

    // Techniques: aligned with their category's Y start
    catPositions.forEach((catPos) => {
      catPos.techniques.forEach((techName, i) => {
        const techId = `technique-${catPos.name}-${techName}`;
        positions[techId] = {
          x: colX.technique,
          y: catPos.y + i * techSpacing
        };
        labelAnchors[techId] = "middle"; // text below, centered
      });
    });

    // Providers: evenly spaced in right column
    const providerBlockHeight =
      selectedProviders.length * config.providerSpacing;
    const providerStartY = Math.max(
      config.nodeMargins.top + 20,
      (height - providerBlockHeight) / 2
    );

    selectedProviders.forEach((provider, i) => {
      const pid = `provider-${provider}`;
      positions[pid] = {
        x: colX.provider,
        y: providerStartY + i * config.providerSpacing
      };
      labelAnchors[pid] = "start";
    });

    return { positions, labelAnchors, layoutName: "sequential" };
  }

  // ==========================================================
  // FORCE (applied to selected nodes only, or all if none)
  // Returns a configured d3 simulation — caller starts/stops it
  // ==========================================================
  function createForceSimulation(nodes, links, selectedNodeIds, nodeById) {
    const fc = config.force;

    const simulatedIds =
      selectedNodeIds.size > 0
        ? selectedNodeIds
        : new Set(nodes.map((n) => n.id));

    // Release fixed positions for simulated nodes, pin the rest
    nodes.forEach((node) => {
      if (simulatedIds.has(node.id)) {
        node.fx = null;
        node.fy = null;
      } else {
        node.fx = node.x;
        node.fy = node.y;
      }
    });

    // Filter links to those connecting at least one simulated node
    const relevantLinks = links
      .map((l) => ({
        source:
          typeof l.source === "object" ? l.source : nodeById.get(l.source),
        target:
          typeof l.target === "object" ? l.target : nodeById.get(l.target),
        type: l.type
      }))
      .filter((l) => l.source && l.target)
      .filter(
        (l) => simulatedIds.has(l.source.id) || simulatedIds.has(l.target.id)
      );

    return d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(relevantLinks)
          .id((d) => d.id)
          .distance((d) =>
            d.type === "provider-technique"
              ? fc.linkDistanceProviderTechnique
              : fc.linkDistanceCategoryTechnique
          )
          .strength((d) =>
            d.type === "provider-technique"
              ? fc.linkStrengthProviderTechnique
              : fc.linkStrengthCategoryTechnique
          )
      )
      .force(
        "charge",
        d3.forceManyBody().strength((d) => {
          if (!simulatedIds.has(d.id)) return 0;
          if (d.type === "provider") return fc.chargeProvider;
          if (d.type === "technique") return fc.chargeTechnique;
          return fc.chargeCategory;
        })
      )
      .force(
        "collide",
        d3.forceCollide().radius((d) => {
          if (!simulatedIds.has(d.id)) return 0;
          return d.type === "provider"
            ? fc.collideProvider
            : fc.collideTechnique;
        })
      )
      .alphaDecay(fc.alphaDecay)
      .velocityDecay(fc.velocityDecay);
  }

  return { balancedLayout, sequentialLayout, createForceSimulation };
}


function _unifiedChartValidatedLayout(unifiedChartData, localStorage, unifiedLayoutStorageKey, unifiedChartLayouts) {
  const { nodes } = unifiedChartData;
  const liveNodeIds = new Set(nodes.map((n) => n.id));

  let savedLayout = null;
  let source = "default";
  const stats = { applied: 0, stale: 0, newNodes: 0 };

  // Try localStorage
  try {
    const saved = localStorage.getItem(unifiedLayoutStorageKey);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.positions && typeof parsed.positions === "object") {
        savedLayout = parsed;
        source = "saved";
      }
    }
  } catch (e) {
    console.warn("Could not load saved unified chart layout:", e);
  }

  if (savedLayout) {
    // Remove stale entries
    const staleIds = Object.keys(savedLayout.positions).filter(
      (id) => !liveNodeIds.has(id)
    );
    staleIds.forEach((id) => delete savedLayout.positions[id]);
    if (savedLayout.labelAnchors) {
      staleIds.forEach((id) => delete savedLayout.labelAnchors[id]);
    }
    stats.stale = staleIds.length;

    // Identify new nodes not in saved layout
    const savedIds = new Set(Object.keys(savedLayout.positions));
    stats.newNodes = nodes.filter((n) => !savedIds.has(n.id)).length;
    stats.applied = nodes.filter((n) => savedIds.has(n.id)).length;
  }

  // Generate balanced layout as the base/fallback
  const balanced = unifiedChartLayouts.balancedLayout(unifiedChartData);

  // Merge: saved positions override balanced where they exist
  const finalPositions = { ...balanced.positions };
  const finalAnchors = { ...balanced.labelAnchors };

  if (savedLayout) {
    Object.entries(savedLayout.positions).forEach(([id, pos]) => {
      if (
        liveNodeIds.has(id) &&
        typeof pos.x === "number" &&
        typeof pos.y === "number" &&
        isFinite(pos.x) &&
        isFinite(pos.y)
      ) {
        finalPositions[id] = pos;
      }
    });
    if (savedLayout.labelAnchors) {
      Object.entries(savedLayout.labelAnchors).forEach(([id, anchor]) => {
        if (liveNodeIds.has(id)) {
          finalAnchors[id] = anchor;
        }
      });
    }
  }

  return {
    positions: finalPositions,
    labelAnchors: finalAnchors,
    layoutName:
      source === "saved" ? savedLayout.layoutName || "saved" : "balanced",
    source,
    stats
  };
}


function _48(md) {
  return (
    md`## Life Cycle Code
`
  )
}

function _lifecycleConfig() {
  return (
    {
      width: 950,
      height: 850,

      margin: { top: 30, right: 30, bottom: 30, left: 30 },

      // --- Governance band (TOP) ---
      governance: {
        top: 40,
        height: 120,
        labelOffsetY: 18
      },

      // --- Temporal phase columns (MIDDLE) ---
      phases: {
        headerHeight: 44,
        headerRadius: 6,
        columnGap: 12,
        areaTop: 195, // below governance band + gap
        areaBottom: 680 // enough for inference column (~11 nodes)
      },

      // --- Harm classification band (BOTTOM) ---
      harm: {
        top: 705,
        height: 220,
        labelOffsetY: 18
      },

      // --- Technique nodes ---
      node: {
        width: 150,
        height: 28,
        radius: 6,
        fontSize: 11,
        padding: { x: 8, y: 6 },
        verticalGap: 6
      },

      // --- Connector lines (governance ↔ temporal) ---
      connector: {
        strokeWidth: 1.5,
        color: "#90A4AE",
        dashArray: "4,3",
        opacity: 0.6
      },

      // --- Phase header colours ---
      phaseColors: {
        "pre-training": "#E8F5E9",
        training: "#E3F2FD",
        evaluation: "#FBE9E7",
        inference: "#F3E5F5",
        monitoring: "#FFF3E0"
      },
      phaseBorderColors: {
        "pre-training": "#66BB6A",
        training: "#42A5F5",
        evaluation: "#EF5350",
        inference: "#AB47BC",
        monitoring: "#FFA726"
      },

      temporalPhaseIds: [
        "pre-training",
        "training",
        "evaluation",
        "inference",
        "monitoring"
      ],

      governanceCategoryId: "cat-governance",
      harmCategoryId: "cat-harm-classification",

      // Techniques that span adjacent temporal columns (rendered as wide nodes)
      spanningTechniques: {
        "tech-configurable-safety": { from: "inference", to: "monitoring" }
      },

      // Techniques duplicated in governance band AND a temporal column (vertical connector)
      governanceConnectors: [
        { techId: "tech-capability-monitoring", temporalPhase: "evaluation" },
        { techId: "tech-incident-reporting", temporalPhase: "monitoring" }
      ]
    }
  )
}

function _lifecycleChartData(lifecycleConfig, data) {
  const cfg = lifecycleConfig;
  const catLookup = new Map(data.categories.map((c) => [c.id, c]));
  const phaseLookup = new Map((data.lifecycle || []).map((p) => [p.id, p]));
  const techniques = data.raw?.techniques || data.techniques || [];

  // --- Build technique → providers map from flatPairs ---
  const techProviders = new Map();
  (data.flatPairs || []).forEach((fp) => {
    if (!techProviders.has(fp.technique)) {
      techProviders.set(fp.technique, new Set());
    }
    techProviders.get(fp.technique).add(fp.provider);
  });

  // --- Enrich all techniques ---
  function enrich(tech) {
    const cat = catLookup.get(tech.categoryId);
    const providers = techProviders.get(tech.name);
    return {
      id: tech.id,
      name: tech.name,
      description: tech.description,
      categoryId: tech.categoryId,
      categoryName: cat?.name || "Other",
      categoryColor: cat?.color || "#999",
      lifecycleStages: tech.lifecycleStages || [],
      providerNames: providers ? [...providers].sort() : []
    };
  }

  // --- Partition into three groups ---
  const governanceTechniques = [];
  const harmTechniques = [];
  const temporalTechniques = [];

  techniques.forEach((tech) => {
    if (tech.categoryId === cfg.governanceCategoryId) {
      governanceTechniques.push(enrich(tech));
    } else if (tech.categoryId === cfg.harmCategoryId) {
      harmTechniques.push(enrich(tech));
    } else {
      temporalTechniques.push(enrich(tech));
    }
  });

  // --- Column geometry ---
  const usableWidth = cfg.width - cfg.margin.left - cfg.margin.right;
  const columnWidth =
    (usableWidth - cfg.phases.columnGap * (cfg.temporalPhaseIds.length - 1)) /
    cfg.temporalPhaseIds.length;

  const columns = cfg.temporalPhaseIds.map((pid, i) => {
    const phaseDef = phaseLookup.get(pid) || { name: pid, description: "" };
    const x = cfg.margin.left + i * (columnWidth + cfg.phases.columnGap);
    return {
      phaseId: pid,
      phaseName: phaseDef.name,
      phaseDescription: phaseDef.description,
      x,
      width: columnWidth,
      centerX: x + columnWidth / 2
    };
  });

  const columnLookup = new Map(columns.map((c) => [c.phaseId, c]));

  // --- Assign temporal techniques to columns ---
  const spanningIds = new Set(Object.keys(cfg.spanningTechniques));

  const phaseGroups = new Map();
  cfg.temporalPhaseIds.forEach((pid) => phaseGroups.set(pid, []));

  const spanningNodes = [];

  temporalTechniques.forEach((tech) => {
    if (spanningIds.has(tech.id)) {
      spanningNodes.push(tech);
      return;
    }
    const primary = (tech.lifecycleStages || []).find((s) =>
      cfg.temporalPhaseIds.includes(s)
    );
    if (primary) {
      phaseGroups.get(primary)?.push(tech);
    }
  });

  // Place governance-connector echo nodes into temporal columns
  const govConnectorIds = new Set(
    cfg.governanceConnectors.map((gc) => gc.techId)
  );
  govConnectorIds.forEach((techId) => {
    const tech = governanceTechniques.find((t) => t.id === techId);
    const connector = cfg.governanceConnectors.find(
      (gc) => gc.techId === techId
    );
    if (tech && connector) {
      phaseGroups
        .get(connector.temporalPhase)
        ?.push({ ...tech, _isEcho: true });
    }
  });

  // --- Position temporal nodes ---
  const nodePositions = new Map();

  columns.forEach((col) => {
    const techs = phaseGroups.get(col.phaseId) || [];
    techs.sort((a, b) => {
      // Echo nodes sort to end of column
      if (a._isEcho !== b._isEcho) return a._isEcho ? 1 : -1;
      const catCmp = a.categoryName.localeCompare(b.categoryName);
      return catCmp !== 0 ? catCmp : a.name.localeCompare(b.name);
    });

    let yOffset = cfg.phases.areaTop + cfg.phases.headerHeight + 16;
    techs.forEach((tech) => {
      const nodeX = col.x + (col.width - cfg.node.width) / 2;
      const posKey = tech._isEcho ? `${tech.id}__temporal` : tech.id;
      nodePositions.set(posKey, {
        x: nodeX,
        y: yOffset,
        cx: nodeX + cfg.node.width / 2,
        cy: yOffset + cfg.node.height / 2,
        width: cfg.node.width,
        height: cfg.node.height,
        phaseId: col.phaseId
      });
      yOffset += cfg.node.height + cfg.node.verticalGap;
    });

    col.techniques = techs;
    col.contentBottom = yOffset;
  });

  // --- Position spanning nodes ---
  const spanningPositions = [];

  spanningNodes.forEach((tech) => {
    const spanDef = cfg.spanningTechniques[tech.id];
    if (!spanDef) return;
    const fromCol = columnLookup.get(spanDef.from);
    const toCol = columnLookup.get(spanDef.to);
    if (!fromCol || !toCol) return;

    const yOffset = Math.max(
      columns.find((c) => c.phaseId === spanDef.from)?.contentBottom || 0,
      columns.find((c) => c.phaseId === spanDef.to)?.contentBottom || 0
    );

    const spanX = fromCol.x + (fromCol.width - cfg.node.width) / 2;
    const spanWidth = toCol.x + toCol.width / 2 + cfg.node.width / 2 - spanX;

    spanningPositions.push({
      tech,
      x: spanX,
      y: yOffset,
      cx: spanX + spanWidth / 2,
      cy: yOffset + cfg.node.height / 2,
      width: spanWidth,
      height: cfg.node.height,
      fromPhase: spanDef.from,
      toPhase: spanDef.to
    });
  });

  // --- Position governance band nodes ---
  governanceTechniques.sort((a, b) => a.name.localeCompare(b.name));

  const govStartY = cfg.governance.top + cfg.governance.labelOffsetY + 20;
  const govNodeWidth = cfg.node.width;
  const govNodesPerRow = Math.floor(
    (usableWidth + cfg.phases.columnGap) / (govNodeWidth + cfg.phases.columnGap)
  );

  const govPositions = new Map();

  governanceTechniques.forEach((tech, i) => {
    const row = Math.floor(i / govNodesPerRow);
    const col = i % govNodesPerRow;
    const itemsInRow = Math.min(
      govNodesPerRow,
      governanceTechniques.length - row * govNodesPerRow
    );
    const totalRowWidth =
      itemsInRow * (govNodeWidth + cfg.phases.columnGap) - cfg.phases.columnGap;
    const rowStartX = cfg.margin.left + (usableWidth - totalRowWidth) / 2;

    const nodeX = rowStartX + col * (govNodeWidth + cfg.phases.columnGap);
    const nodeY = govStartY + row * (cfg.node.height + cfg.node.verticalGap);

    govPositions.set(tech.id, {
      x: nodeX,
      y: nodeY,
      cx: nodeX + govNodeWidth / 2,
      cy: nodeY + cfg.node.height / 2,
      width: govNodeWidth,
      height: cfg.node.height
    });
  });

  // --- Position harm band nodes ---
  harmTechniques.sort((a, b) => a.name.localeCompare(b.name));

  const harmStartY = cfg.harm.top + cfg.harm.labelOffsetY + 20;
  const harmNodeWidth = cfg.node.width;
  const harmNodesPerRow = Math.floor(
    (usableWidth + cfg.phases.columnGap) /
    (harmNodeWidth + cfg.phases.columnGap)
  );

  const harmPositions = new Map();

  harmTechniques.forEach((tech, i) => {
    const row = Math.floor(i / harmNodesPerRow);
    const col = i % harmNodesPerRow;
    const itemsInRow = Math.min(
      harmNodesPerRow,
      harmTechniques.length - row * harmNodesPerRow
    );
    const totalRowWidth =
      itemsInRow * (harmNodeWidth + cfg.phases.columnGap) -
      cfg.phases.columnGap;
    const rowStartX = cfg.margin.left + (usableWidth - totalRowWidth) / 2;

    const nodeX = rowStartX + col * (harmNodeWidth + cfg.phases.columnGap);
    const nodeY = harmStartY + row * (cfg.node.height + cfg.node.verticalGap);

    harmPositions.set(tech.id, {
      x: nodeX,
      y: nodeY,
      cx: nodeX + harmNodeWidth / 2,
      cy: nodeY + cfg.node.height / 2,
      width: harmNodeWidth,
      height: cfg.node.height
    });
  });

  // --- Build governance connector data ---
  const connectors = [];
  cfg.governanceConnectors.forEach((gc) => {
    const govPos = govPositions.get(gc.techId);
    const tempPos = nodePositions.get(`${gc.techId}__temporal`);
    if (govPos && tempPos) {
      const tech = governanceTechniques.find((t) => t.id === gc.techId);
      connectors.push({
        techId: gc.techId,
        techName: tech?.name || gc.techId,
        categoryColor: tech?.categoryColor || "#999",
        govPos,
        tempPos
      });
    }
  });

  // --- Provider list ---
  const allProviders = [
    ...new Set(data.flatPairs?.map((fp) => fp.provider) || [])
  ].sort();

  return {
    columns,
    columnLookup,
    governanceTechniques,
    harmTechniques,
    spanningPositions,
    nodePositions,
    govPositions,
    harmPositions,
    connectors,
    allProviders,
    allTechniques: techniques,
    techProviders
  };
}


function _51(md) {
  return (
    md`## CSS Block (Additional supporting styles as required)`
  )
}

function _52(htl) {
  return (
    htl.html`<style>
hr {
    border: none; /* Remove default border */
    border-top: 2px dotted orange; /* Set the top border style, width, and color */
    width: 80%; /* Adjust the width of the line */
    margin: 20px auto; /* Center the line and add vertical spacing */
}
  </style>`
  )
}

export default function define(runtime, observer) {
  const main = runtime.module();
  function toString() { return this.url; }
  const fileAttachments = new Map([
    ["network-layout.json", { url: new URL("./files/5975fcdf011a5d29e82fa8e6cac12837b27695cf1032d6711637685c1591475b4b0d2bd1754db32a2b33866208ea513e4ccf01e9e2f02d2095a81d8a99ff59a0.json", import.meta.url), mimeType: "application/json", toString }]
  ]);
  main.builtin("FileAttachment", runtime.fileAttachments(name => fileAttachments.get(name)));
  main.variable(observer()).define(["md"], _1);
  main.variable(observer()).define(["md"], _2);
  main.variable(observer("unifiedChart")).define("unifiedChart", ["unifiedChartData", "unifiedChartConfig", "unifiedChartLayouts", "unifiedChartValidatedLayout", "d3", "localStorage", "unifiedLayoutStorageKey", "location"], _unifiedChart);
  main.variable(observer()).define(["md"], _4);
  main.variable(observer("viewof filters")).define("viewof filters", ["data", "html", "d3"], _filters);
  main.variable(observer("filters")).define("filters", ["Generators", "viewof filters"], (G, _) => G.input(_));
  main.variable(observer()).define(["md"], _6);
  main.variable(observer("sunburstChart")).define("sunburstChart", ["data", "filteredData", "d3", "categoryColors"], _sunburstChart);
  main.variable(observer()).define(["filteredData", "data", "md"], _8);
  main.variable(observer()).define(["htl"], _9);
  main.variable(observer()).define(["md"], _10);
  main.variable(observer("lifecycleChart")).define("lifecycleChart", ["lifecycleChartData", "lifecycleConfig", "d3", "data"], _lifecycleChart);
  main.variable(observer()).define(["htl"], _12);
  main.variable(observer()).define(["md"], _13);
  main.variable(observer("networkViz")).define("networkViz", ["positionedGraph", "validatedLayout", "networkConfig", "d3", "localStorage", "layoutStorageKey", "confirm", "location", "autoLayout", "providerColors"], _networkViz);
  main.variable(observer()).define(["htl"], _15);
  main.variable(observer("excludedDataSummary")).define("excludedDataSummary", ["data", "providerColors", "html"], _excludedDataSummary);
  main.variable(observer("viewof exportOptions")).define("viewof exportOptions", ["html", "filteredData", "filters"], _exportOptions);
  main.variable(observer("exportOptions")).define("exportOptions", ["Generators", "viewof exportOptions"], (G, _) => G.input(_));
  main.variable(observer("viewof table")).define("viewof table", ["Inputs", "filteredData"], _table);
  main.variable(observer("table")).define("table", ["Generators", "viewof table"], (G, _) => G.input(_));
  main.variable(observer()).define(["htl"], _19);
  main.variable(observer()).define(["md"], _20);
  main.variable(observer()).define(["htl"], _21);
  main.variable(observer()).define(["md"], _22);
  main.variable(observer()).define(["htl"], _23);
  main.variable(observer()).define(["md"], _24);
  main.variable(observer("embedAPI")).define("embedAPI", ["filteredData", "d3", "URLSearchParams"], _embedAPI);
  main.variable(observer("data")).define("data", ["d3"], _data);
  main.variable(observer("filteredData")).define("filteredData", ["data", "filters"], _filteredData);
  main.variable(observer("audit")).define("audit", ["globalThis"], _audit);
  main.variable(observer()).define(["md"], _29);
  main.variable(observer("colorSchemes")).define("colorSchemes", ["d3"], _colorSchemes);
  main.variable(observer("categoryColors")).define("categoryColors", ["colorSchemes"], _categoryColors);
  main.variable(observer("providerColors")).define("providerColors", ["colorSchemes"], _providerColors);
  main.variable(observer()).define(["md"], _33);
  main.variable(observer("networkConfig")).define("networkConfig", _networkConfig);
  main.variable(observer("networkGraph")).define("networkGraph", ["data"], _networkGraph);
  main.variable(observer("layoutStorageKey")).define("layoutStorageKey", _layoutStorageKey);
  main.variable(observer("defaultLayout")).define("defaultLayout", ["FileAttachment"], _defaultLayout);
  main.variable(observer("positionedGraph")).define("positionedGraph", ["networkGraph", "validatedLayout", "networkConfig", "d3"], _positionedGraph);
  main.variable(observer("autoLayout")).define("autoLayout", ["networkGraph", "networkConfig", "d3"], _autoLayout);
  main.variable(observer("validatedLayout")).define("validatedLayout", ["networkGraph", "localStorage", "layoutStorageKey", "defaultLayout"], _validatedLayout);
  main.variable(observer("savedLayout")).define("savedLayout", ["localStorage", "layoutStorageKey"], _savedLayout);
  main.variable(observer()).define(["md"], _42);
  main.variable(observer("unifiedChartConfig")).define("unifiedChartConfig", _unifiedChartConfig);
  main.variable(observer("unifiedLayoutStorageKey")).define("unifiedLayoutStorageKey", _unifiedLayoutStorageKey);
  main.variable(observer("unifiedChartData")).define("unifiedChartData", ["unifiedChartConfig", "providerColors", "data", "filteredData", "categoryColors", "d3"], _unifiedChartData);
  main.variable(observer("unifiedChartLayouts")).define("unifiedChartLayouts", ["unifiedChartConfig", "d3"], _unifiedChartLayouts);
  main.variable(observer("unifiedChartValidatedLayout")).define("unifiedChartValidatedLayout", ["unifiedChartData", "localStorage", "unifiedLayoutStorageKey", "unifiedChartLayouts"], _unifiedChartValidatedLayout);
  main.variable(observer()).define(["md"], _48);
  main.variable(observer("lifecycleConfig")).define("lifecycleConfig", _lifecycleConfig);
  main.variable(observer("lifecycleChartData")).define("lifecycleChartData", ["lifecycleConfig", "data"], _lifecycleChartData);
  main.variable(observer()).define(["md"], _51);
  main.variable(observer()).define(["htl"], _52);
  return main;
}
