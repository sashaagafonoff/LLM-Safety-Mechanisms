// Network visualization: Document-provider-model network graph
// Ported from Observable notebook cell: networkViz

import {NETWORK_LAYOUT_STORAGE_KEY} from "./network-data.js";

export function createNetworkViz(positionedGraph, validatedLayout, autoLayout, config, providerColors, d3) {
  const {
    nodes, providers, models, evidence, resolvedLinks, nodeById, orphanModels, orphanEvidence
  } = positionedGraph;

  const { source: layoutSource, stats: layoutStats } = validatedLayout;
  const {
    width, height, centerX, centerY, providerRadius, modelRadius, evidenceRadius,
    nodeRadius, evidenceRect, colors, linkColors
  } = config;

  const selectedNodes = new Set();

  const container = d3.create("div").style("position", "relative");

  // ── Toolbar ──
  const toolbar = container
    .append("div")
    .style("margin-bottom", "10px")
    .style("display", "flex").style("gap", "8px").style("flex-wrap", "wrap").style("align-items", "center");

  const buttonStyle = `
    padding: 6px 12px; font-size: 12px; border: 1px solid #ccc;
    border-radius: 4px; background: #fff; color: #333; cursor: pointer;
    transition: background 0.15s;
  `;

  function addButton(parent, label, onClick, insertPos) {
    const btn = insertPos ? parent.insert("button", insertPos) : parent.append("button");
    return btn
      .attr("style", buttonStyle).text(label).on("click", onClick)
      .on("mouseover", function () { d3.select(this).style("background", "#f0f0f0"); })
      .on("mouseout", function () { d3.select(this).style("background", "#fff"); });
  }

  const statusText = {
    saved: "\u2713 Using saved layout",
    attached: "\u2713 Using default layout",
    default: "Using radial layout"
  };

  const status = toolbar.append("span")
    .style("font-size", "11px")
    .style("color", layoutSource === "default" ? "#666" : "#2e7d32")
    .style("margin-left", "12px").style("min-width", "160px")
    .text(statusText[layoutSource]);

  const selectionStatus = toolbar.append("span")
    .style("font-size", "11px").style("color", "#666").style("margin-left", "12px").text("");

  let layoutModified = false;

  function showStatus(message, color, duration = 2000) {
    status.text(message).style("color", color);
    if (duration > 0) {
      setTimeout(() => {
        if (layoutModified) {
          status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
        } else {
          status.text(statusText[layoutSource])
            .style("color", layoutSource === "default" ? "#666" : "#2e7d32");
        }
      }, duration);
    }
  }

  function updateSelectionStatus() {
    selectionStatus.text(
      selectedNodes.size === 0 ? "" : `${selectedNodes.size} selected (drag background to select, Esc to clear)`
    );
  }

  // ── Toolbar buttons ──
  addButton(toolbar, "\uD83D\uDCBE Save Layout", function () {
    try {
      const layout = {};
      nodes.forEach((n) => { layout[n.id] = { x: n.x, y: n.y }; });
      localStorage.setItem(NETWORK_LAYOUT_STORAGE_KEY, JSON.stringify(layout));
      layoutModified = false;
      showStatus("\u2713 Layout saved!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("\u2717 Save failed: " + e.message, "#c9190b", 3000);
    }
  }, ":first-child");

  addButton(toolbar, "\u21BA Reset to Default", function () {
    if (confirm("Reset to default layout? This will clear your saved changes.")) {
      try {
        localStorage.removeItem(NETWORK_LAYOUT_STORAGE_KEY);
        location.reload();
      } catch (e) {
        showStatus("\u2717 Reset failed: " + e.message, "#c9190b", 3000);
      }
    }
  }, ":nth-child(2)");

  addButton(toolbar, "\u26A1 Auto Layout", function () {
    nodes.forEach((n) => {
      const pos = autoLayout[n.id];
      if (pos) { n.x = pos.x; n.y = pos.y; }
    });

    g.selectAll(".providers g, .models g, .evidence g").attr("transform", (d) => `translate(${d.x},${d.y})`);

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
        return a > Math.PI / 2 || a < -Math.PI / 2 ? -nodeRadius.provider - 6 : nodeRadius.provider + 6;
      })
      .attr("y", (d) => {
        if (d.labelAnchor) return 4;
        const a = d.angle;
        if (a > Math.PI / 4 && a < (3 * Math.PI) / 4) return nodeRadius.provider + 14;
        if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4) return -nodeRadius.provider - 6;
        return 4;
      });

    g.selectAll(".models g text")
      .attr("text-anchor", (d) => {
        if (d.labelAnchor) return d.labelAnchor;
        return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? "end" : "start";
      })
      .attr("x", (d) => {
        if (d.labelAnchor === "end") return -nodeRadius.model - 4;
        if (d.labelAnchor === "start") return nodeRadius.model + 4;
        return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? -nodeRadius.model - 4 : nodeRadius.model + 4;
      });

    g.selectAll(".evidence g text")
      .attr("text-anchor", (d) => {
        if (d.labelAnchor) return d.labelAnchor;
        return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? "end" : "start";
      })
      .attr("x", (d) => {
        if (d.labelAnchor === "end") return -evidenceRect.width / 2 - 6;
        if (d.labelAnchor === "start") return evidenceRect.width / 2 + 6;
        return d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? -evidenceRect.width / 2 - 6 : evidenceRect.width / 2 + 6;
      });

    updateLinks();
    layoutModified = true;
    showStatus("\u26A1 Auto layout applied (unsaved)", "#7c5e10", 3000);
  }, ":nth-child(3)");

  addButton(toolbar, "\uD83D\uDCE4 Export Layout", function () {
    try {
      const layout = {};
      nodes.forEach((n) => { layout[n.id] = { x: n.x, y: n.y }; });
      const blob = new Blob([JSON.stringify(layout, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "network-layout.json";
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showStatus("\u2713 Layout exported!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("\u2717 Export failed: " + e.message, "#c9190b", 3000);
    }
  }, ":nth-child(3)");

  const fileInput = toolbar.insert("input", ":nth-child(4)")
    .attr("type", "file").attr("accept", ".json").style("display", "none")
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
          localStorage.setItem(NETWORK_LAYOUT_STORAGE_KEY, JSON.stringify(layout));
          showStatus("\u2713 Imported! Reloading...", "#2e7d32", 1000);
          setTimeout(() => location.reload(), 1000);
        } catch (err) {
          showStatus("\u2717 Import failed: " + err.message, "#c9190b", 3000);
        }
      };
      reader.onerror = () => showStatus("\u2717 Could not read file", "#c9190b", 3000);
      reader.readAsText(file);
    });

  addButton(toolbar, "\uD83D\uDCE5 Import Layout", () => fileInput.node().click(), ":nth-child(5)");

  addButton(toolbar, "\u2298 Clear Selection", () => clearSelection(), ":nth-child(6)");

  // ── Status indicators ──
  if (orphanModels > 0 || orphanEvidence > 0) {
    toolbar.append("span")
      .style("font-size", "11px").style("color", "#c9190b").style("margin-left", "16px")
      .style("padding", "4px 8px").style("background", "#fee").style("border-radius", "4px")
      .style("border", "1px solid #fcc")
      .html(
        `\u26A0 Orphans: ${orphanModels > 0 ? `${orphanModels} model${orphanModels > 1 ? "s" : ""}` : ""}` +
        `${orphanModels > 0 && orphanEvidence > 0 ? ", " : ""}` +
        `${orphanEvidence > 0 ? `${orphanEvidence} doc${orphanEvidence > 1 ? "s" : ""}` : ""}`
      );
  }

  if (layoutStats.stale > 0 || layoutStats.newNodes > 0) {
    const parts = [];
    if (layoutStats.stale > 0) parts.push(`${layoutStats.stale} stale removed`);
    if (layoutStats.newNodes > 0) parts.push(`${layoutStats.newNodes} new (radial)`);
    toolbar.append("span")
      .style("font-size", "11px").style("color", "#7c5e10").style("margin-left", "8px")
      .style("padding", "4px 8px").style("background", "#fff8e1").style("border-radius", "4px")
      .style("border", "1px solid #ffe082")
      .html(`\u27F3 Layout sync: ${parts.join(", ")}`);
  }

  // ── SVG + Zoom ──
  const svg = container.append("svg")
    .attr("viewBox", [0, 0, width, height]).attr("width", width).attr("height", height)
    .style("background", "#fafafa");

  const g = svg.append("g");
  let currentTransform = d3.zoomIdentity;

  const zoom = d3.zoom().scaleExtent([0.3, 3])
    .filter((event) => event.type === "wheel" || event.type === "dblclick")
    .on("zoom", (event) => { currentTransform = event.transform; g.attr("transform", event.transform); });
  svg.call(zoom);

  // ── Marquee selection ──
  const marquee = svg.append("rect").attr("class", "marquee")
    .attr("fill", "rgba(0, 102, 204, 0.1)").attr("stroke", "#0066cc")
    .attr("stroke-width", 1).attr("stroke-dasharray", "4,2").style("display", "none");

  let marqueeStart = null;
  let isMarqueeSelecting = false;

  svg.on("mousedown", function (event) {
    if (event.target === svg.node() || (event.target.tagName === "rect" && event.target.classList.contains("marquee-bg"))) {
      const [x, y] = d3.pointer(event, svg.node());
      marqueeStart = { x, y };
      isMarqueeSelecting = true;
      marquee.attr("x", x).attr("y", y).attr("width", 0).attr("height", 0).style("display", "block");
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
    g.selectAll(".providers g, .models g, .evidence g").classed("marquee-hover",
      (d) => d.x >= mRect.x1 && d.x <= mRect.x2 && d.y >= mRect.y1 && d.y <= mRect.y2
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
        if (n.x >= mRect.x1 && n.x <= mRect.x2 && n.y >= mRect.y1 && n.y <= mRect.y2)
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
        .attr("cx", centerX).attr("cy", centerY).attr("r", r)
        .attr("fill", "none").attr("stroke", "#eee").attr("stroke-width", 1).attr("stroke-dasharray", "4,4");
    });
  }

  // ── Links ──
  const linkGroup = g.append("g").attr("class", "links");
  const linkElements = linkGroup.selectAll("line").data(resolvedLinks).join("line")
    .attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y)
    .attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y)
    .attr("stroke", (d) => linkColors[d.type])
    .attr("stroke-width", (d) => (d.type === "owns" ? 1.5 : 0.75))
    .attr("stroke-opacity", 0.4);

  function updateLinks() {
    linkElements.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
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
  const tooltip = d3.select("body").append("div").attr("class", "network-tooltip")
    .style("position", "absolute").style("visibility", "hidden")
    .style("background", "white").style("border", "1px solid #ddd").style("border-radius", "4px")
    .style("padding", "8px 12px").style("font-size", "11px").style("max-width", "350px")
    .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)").style("z-index", 1000).style("pointer-events", "auto");

  let tooltipTimeout = null;
  let isOverTooltip = false;
  let isOverNode = false;
  let isDragging = false;

  function hideTooltip() { tooltip.style("visibility", "hidden"); isOverNode = false; }

  function showTooltip(event, d) {
    if (isDragging) return;
    if (tooltipTimeout) { clearTimeout(tooltipTimeout); tooltipTimeout = null; }
    isOverNode = true;
    const orphanWarning = d.isOrphan
      ? `<div style="color:#c9190b; margin-top:4px; padding-top:4px; border-top:1px solid #eee;">\u26A0 Orphan: ${
          d.type === "model" ? "No documents reference this model" : "No models linked to this document"
        }</div>` : "";
    tooltip.style("visibility", "visible").html(
      `<strong>${d.label}</strong><br/>` +
      `<em>Type:</em> ${d.type}${d.docType ? ` (${d.docType})` : ""}<br/>` +
      `${d.providerName ? `<em>Provider:</em> ${d.providerName}<br/>` : ""}` +
      `${d.modelCount !== undefined ? `<em>Models covered:</em> ${d.modelCount}<br/>` : ""}` +
      `${d.url ? `<a href="${d.url}" target="_blank" style="color:#2563eb; text-decoration:underline;">View document \u2197</a>` : ""}` +
      orphanWarning
    ).style("top", event.pageY - 10 + "px").style("left", event.pageX + 15 + "px");
  }

  function scheduleHideTooltip() {
    if (tooltipTimeout) clearTimeout(tooltipTimeout);
    tooltipTimeout = setTimeout(() => {
      if (!isOverTooltip && !isOverNode) tooltip.style("visibility", "hidden");
    }, 300);
  }

  tooltip
    .on("mouseenter", function () { isOverTooltip = true; if (tooltipTimeout) { clearTimeout(tooltipTimeout); tooltipTimeout = null; } })
    .on("mouseleave", function () { isOverTooltip = false; scheduleHideTooltip(); });

  // ── Drag behavior ──
  function drag() {
    let dragStartPositions = new Map();
    return d3.drag()
      .on("start", function (event, d) {
        isDragging = true; hideTooltip();
        if (!selectedNodes.has(d.id)) { selectedNodes.clear(); selectedNodes.add(d.id); updateSelectionVisuals(); }
        dragStartPositions.clear();
        selectedNodes.forEach((id) => { const node = nodeById.get(id); if (node) dragStartPositions.set(id, { x: node.x, y: node.y }); });
        d3.select(this).raise().classed("dragging", true);
      })
      .on("drag", function (event, d) {
        const startPos = dragStartPositions.get(d.id);
        if (!startPos) return;
        const dx = event.x - startPos.x;
        const dy = event.y - startPos.y;
        selectedNodes.forEach((id) => {
          const node = nodeById.get(id); const nodeStart = dragStartPositions.get(id);
          if (node && nodeStart) { node.x = nodeStart.x + dx; node.y = nodeStart.y + dy; }
        });
        g.selectAll(".providers g, .models g, .evidence g")
          .filter((n) => selectedNodes.has(n.id))
          .attr("transform", (n) => `translate(${n.x},${n.y})`);
        updateLinks();
        if (!layoutModified) { layoutModified = true; status.text("\u26A0 Unsaved changes").style("color", "#c9190b"); }
      })
      .on("end", function () { d3.select(this).classed("dragging", false); dragStartPositions.clear(); isDragging = false; });
  }

  // ── Render provider nodes ──
  const providerNodes = g.append("g").attr("class", "providers").selectAll("g")
    .data(providers).join("g")
    .attr("transform", (d) => `translate(${d.x},${d.y})`).style("cursor", "grab").call(drag());

  providerNodes.append("circle").attr("r", nodeRadius.provider)
    .attr("fill", (d) => providerColors[d.providerName] || "#999").attr("stroke", "#fff").attr("stroke-width", 2);

  providerNodes.append("text").text((d) => d.label)
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
      return a > Math.PI / 2 || a < -Math.PI / 2 ? -nodeRadius.provider - 6 : nodeRadius.provider + 6;
    })
    .attr("y", (d) => {
      const a = d.angle;
      if (a > Math.PI / 4 && a < (3 * Math.PI) / 4) return nodeRadius.provider + 14;
      if (a > (-3 * Math.PI) / 4 && a < -Math.PI / 4) return -nodeRadius.provider - 6;
      return 4;
    })
    .style("font-size", "11px").style("font-weight", "bold").style("fill", "#333").style("pointer-events", "none");

  // ── Render model nodes ──
  const modelNodes = g.append("g").attr("class", "models").selectAll("g")
    .data(models).join("g")
    .attr("transform", (d) => `translate(${d.x},${d.y})`).style("cursor", "grab").call(drag());

  modelNodes.append("circle").attr("r", nodeRadius.model)
    .attr("fill", (d) => { const color = providerColors[d.providerName]; return color ? d3.color(color).brighter(0.5) : colors.model; })
    .attr("stroke", (d) => d.isOrphan ? "#c9190b" : providerColors[d.providerName] || "#fff")
    .attr("stroke-width", (d) => (d.isOrphan ? 3 : 1));

  modelNodes.append("text").text((d) => d.label)
    .attr("text-anchor", (d) => d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? "end" : "start")
    .attr("x", (d) => d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? -nodeRadius.model - 4 : nodeRadius.model + 4)
    .attr("y", 3)
    .style("font-size", "8px").style("fill", "#555").style("pointer-events", "none");

  // ── Render evidence nodes ──
  const evidenceNodes = g.append("g").attr("class", "evidence").selectAll("g")
    .data(evidence).join("g")
    .attr("transform", (d) => `translate(${d.x},${d.y})`).style("cursor", "grab").call(drag());

  evidenceNodes.append("rect")
    .attr("x", -evidenceRect.width / 2).attr("y", -evidenceRect.height / 2)
    .attr("width", evidenceRect.width).attr("height", evidenceRect.height)
    .attr("rx", 2).attr("ry", 2)
    .attr("fill", colors.evidence)
    .attr("stroke", (d) => d.isOrphan ? "#c9190b" : providerColors[d.providerName] || colors.evidenceBorder)
    .attr("stroke-width", (d) => (d.isOrphan ? 3 : 1.5));

  evidenceNodes.append("text")
    .text((d) => d.label.length > 35 ? d.label.substring(0, 33) + "..." : d.label)
    .attr("text-anchor", (d) => d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? "end" : "start")
    .attr("x", (d) => d.angle > Math.PI / 2 || d.angle < -Math.PI / 2 ? -evidenceRect.width / 2 - 6 : evidenceRect.width / 2 + 6)
    .attr("y", 3)
    .style("font-size", "7px").style("fill", "#666").style("pointer-events", "none");

  // ── Node interactions ──
  const allNodes = g.selectAll(".providers g, .models g, .evidence g");

  allNodes
    .on("mouseenter", function (event, d) { if (isDragging || isMarqueeSelecting) return; showTooltip(event, d); })
    .on("mousemove", function (event) { if (isDragging || isMarqueeSelecting) return; tooltip.style("top", event.pageY - 10 + "px").style("left", event.pageX + 15 + "px"); })
    .on("mouseleave", function () { isOverNode = false; if (!isDragging) scheduleHideTooltip(); })
    .on("mousedown", function (event) { hideTooltip(); event.stopPropagation(); });

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
