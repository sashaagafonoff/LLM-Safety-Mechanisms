// Third-party commentary network graph: Category → Technique → Commentary

import { setupNetworkInteractions } from "./network-interactions.js";

const COMMENTARY_LAYOUT_KEY = "commentary-view-layout-v1";

export function createCommentaryView(data, categoryColors, d3) {
  const commentary = data.raw.commentary || [];
  const techniques = data.raw.techniques;
  const categories = data.raw.categories || [];
  const techLookup = new Map(techniques.map((t) => [t.id, t]));
  const catLookup = new Map(categories.map((c) => [c.id, c]));

  if (commentary.length === 0) {
    const div = document.createElement("div");
    div.style.cssText = "padding: 20px; text-align: center; color: #999; background: #f8f9fa; border-radius: 8px;";
    div.innerHTML = `<p style="font-size: 16px; margin-bottom: 8px;">No third-party commentary entries yet.</p>
      <p style="font-size: 13px;">Add entries to <code>data/commentary.json</code> to populate this view.</p>`;
    return div;
  }

  const sentimentColors = {
    positive: "#16a34a",
    negative: "#dc2626",
    mixed: "#ca8a04",
    neutral: "#6b7280"
  };

  const typeBadgeColors = {
    academic_paper: { bg: "#e0e7ff", text: "#3730a3" },
    blog_post: { bg: "#fef3c7", text: "#92400e" },
    report: { bg: "#d1fae5", text: "#065f46" },
    news: { bg: "#f3e8ff", text: "#6b21a8" },
    audit: { bg: "#fce7f3", text: "#9d174d" }
  };

  // Build graph data
  const nodes = [];
  const links = [];
  const nodeById = new Map();

  // Find techniques referenced by commentary
  const referencedTechIds = new Set();
  for (const c of commentary) {
    for (const tid of c.techniqueIds || []) referencedTechIds.add(tid);
  }

  // Find categories for referenced techniques
  const referencedCatIds = new Set();
  for (const tid of referencedTechIds) {
    const tech = techLookup.get(tid);
    if (tech) referencedCatIds.add(tech.categoryId);
  }

  // Category nodes
  for (const catId of referencedCatIds) {
    const cat = catLookup.get(catId);
    if (!cat) continue;
    // Estimate text dimensions for rectangle sizing (refined after render)
    const estCharWidth = 7.5;
    const estW = cat.name.length * estCharWidth + 24;
    const estH = 30;
    const node = {
      id: `cat-${catId}`,
      type: "category",
      name: cat.name,
      color: categoryColors[cat.name] || "#999",
      rectW: estW,
      rectH: estH
    };
    nodes.push(node);
    nodeById.set(node.id, node);
  }

  // Technique nodes
  for (const tid of referencedTechIds) {
    const tech = techLookup.get(tid);
    if (!tech) continue;
    const cat = catLookup.get(tech.categoryId);
    const node = {
      id: `tech-${tid}`,
      type: "technique",
      name: tech.name,
      color: categoryColors[cat ? cat.name : ""] || "#888",
      categoryId: tech.categoryId
    };
    nodes.push(node);
    nodeById.set(node.id, node);

    const catNodeId = `cat-${tech.categoryId}`;
    if (nodeById.has(catNodeId)) {
      links.push({
        source: catNodeId,
        target: node.id,
        type: "category-technique",
        color: categoryColors[cat ? cat.name : ""] || "#ccc"
      });
    }
  }

  // Commentary nodes
  for (const c of commentary) {
    const node = {
      id: `comm-${c.id}`,
      type: "commentary",
      name: c.title.length > 30 ? c.title.substring(0, 28) + "\u2026" : c.title,
      fullTitle: c.title,
      author: c.author || "",
      organization: c.organization || "",
      url: c.url,
      date: c.date || "",
      summary: c.summary || "",
      entryType: c.type || "",
      sentiment: c.sentiment || "neutral",
      color: sentimentColors[c.sentiment] || sentimentColors.neutral,
      radius: 7
    };
    nodes.push(node);
    nodeById.set(node.id, node);

    for (const tid of c.techniqueIds || []) {
      const techNodeId = `tech-${tid}`;
      if (nodeById.has(techNodeId)) {
        links.push({
          source: techNodeId,
          target: node.id,
          type: "technique-commentary",
          color: "#ccc"
        });
      }
    }
  }

  // Load saved layout
  let savedPositions = null;
  let layoutSource = "default";
  try {
    const raw = localStorage.getItem(COMMENTARY_LAYOUT_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed.positions) {
        savedPositions = parsed.positions;
        layoutSource = "saved";
      }
    }
  } catch (e) { /* ignore */ }

  // Apply saved positions
  if (savedPositions) {
    nodes.forEach((n) => {
      const pos = savedPositions[n.id];
      if (pos) { n.x = pos.x; n.y = pos.y; n.fx = pos.x; n.fy = pos.y; }
    });
  }

  const width = 900;
  const height = 600;

  let forceSimulation = null;
  let layoutModified = false;

  const container = d3.create("div").style("position", "relative");

  // Stats bar
  container.append("div")
    .style("margin-bottom", "8px")
    .style("font-size", "13px")
    .style("color", "#666")
    .text(`${commentary.length} reference${commentary.length !== 1 ? "s" : ""} across ${referencedTechIds.size} technique${referencedTechIds.size !== 1 ? "s" : ""} in ${referencedCatIds.size} categor${referencedCatIds.size !== 1 ? "ies" : "y"}`);

  // Legend
  const legend = container.append("div")
    .style("display", "flex")
    .style("gap", "16px")
    .style("margin-bottom", "8px")
    .style("font-size", "11px")
    .style("color", "#666")
    .style("flex-wrap", "wrap");

  legend.append("span").html(`<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#888;margin-right:3px;vertical-align:middle;"></span> Category`);
  legend.append("span").html(`<span style="display:inline-block;width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:10px solid #888;margin-right:3px;vertical-align:middle;"></span> Technique`);

  [["positive", "Positive"], ["negative", "Negative"], ["mixed", "Mixed"], ["neutral", "Neutral"]].forEach(([key, label]) => {
    legend.append("span").html(
      `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${sentimentColors[key]};margin-right:3px;vertical-align:middle;"></span> ${label}`
    );
  });

  // ── Toolbar ──
  const toolbar = container.append("div")
    .style("margin-bottom", "8px")
    .style("display", "flex")
    .style("gap", "8px")
    .style("flex-wrap", "wrap")
    .style("align-items", "center");

  const buttonStyle = `
    padding: 5px 10px; font-size: 12px; border: 1px solid #ccc;
    border-radius: 4px; background: #fff; color: #333; cursor: pointer;
    transition: background 0.15s;
  `;

  function addButton(parent, label, onClick) {
    return parent.append("button")
      .attr("style", buttonStyle)
      .text(label)
      .on("click", onClick)
      .on("mouseover", function () { d3.select(this).style("background", "#f0f0f0"); })
      .on("mouseout", function () { d3.select(this).style("background", "#fff"); });
  }

  const status = toolbar.append("span")
    .style("font-size", "11px")
    .style("color", layoutSource === "saved" ? "#2e7d32" : "#666")
    .style("margin-left", "8px")
    .style("min-width", "140px")
    .text(layoutSource === "saved" ? "\u2713 Using saved layout" : "Using force layout");

  function showStatus(message, color, duration = 2000) {
    status.text(message).style("color", color);
    if (duration > 0) {
      setTimeout(() => {
        if (layoutModified) {
          status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
        } else {
          status.text(layoutSource === "saved" ? "\u2713 Using saved layout" : "Using force layout")
            .style("color", layoutSource === "saved" ? "#2e7d32" : "#666");
        }
      }, duration);
    }
  }

  // ── Layout algorithms ──
  function computeBalancedLayout() {
    const positions = {};

    // Build technique → commentary mapping
    const techToComm = new Map();
    const placedComm = new Set();
    for (const c of commentary) {
      for (const tid of c.techniqueIds || []) {
        if (!techToComm.has(tid)) techToComm.set(tid, []);
        techToComm.get(tid).push(`comm-${c.id}`);
      }
    }

    const catGroups = [];
    for (const catId of referencedCatIds) {
      const cat = catLookup.get(catId);
      if (!cat) continue;
      const techs = [...referencedTechIds].filter((tid) => {
        const t = techLookup.get(tid);
        return t && t.categoryId === catId;
      });
      catGroups.push({ catId, name: cat.name, techs });
    }

    const techBaseSpacing = 22;
    const commSpacingV = 14;
    const commSpacingH = 25;
    const maxPerSubCol = 3;
    const commOffset = 50;
    const catH = 32;
    const catGap = 30;

    // Row height for a technique = max of base spacing or its commentary cluster height
    function techRowHeight(tid) {
      const n = (techToComm.get(tid) || []).filter((id) => !placedComm.has(id)).length;
      if (n === 0) return techBaseSpacing;
      return Math.max(techBaseSpacing, Math.min(n, maxPerSubCol) * commSpacingV + 6);
    }

    function groupHeight(g) {
      return catH + g.techs.reduce((s, tid) => s + techRowHeight(tid), 0) + catGap;
    }

    // Balance columns by total height
    const sorted = [...catGroups].sort((a, b) => groupHeight(b) - groupHeight(a));
    const leftGroups = [], rightGroups = [];
    let leftTotal = 0, rightTotal = 0;

    for (const group of sorted) {
      const gh = groupHeight(group);
      if (leftTotal <= rightTotal) { leftGroups.push(group); leftTotal += gh; }
      else { rightGroups.push(group); rightTotal += gh; }
    }

    leftGroups.sort((a, b) => a.name.localeCompare(b.name));
    rightGroups.sort((a, b) => a.name.localeCompare(b.name));

    // Layout a column: category + techniques + commentary clustered near each technique
    function layoutCol(groups, catX, isLeft) {
      const totalH = groups.reduce((s, g) => s + groupHeight(g), 0);
      let y = Math.max(20, (height - totalH) / 2);
      const commDir = isLeft ? 1 : -1; // commentary extends toward center

      groups.forEach((group) => {
        positions[`cat-${group.catId}`] = { x: catX, y };
        let techY = y + catH;

        group.techs.forEach((tid) => {
          positions[`tech-${tid}`] = { x: catX, y: techY };

          const commIds = (techToComm.get(tid) || []).filter((id) => !placedComm.has(id));
          commIds.forEach((commId, i) => {
            const subCol = Math.floor(i / maxPerSubCol);
            const row = i % maxPerSubCol;
            positions[commId] = {
              x: catX + commDir * (commOffset + subCol * commSpacingH),
              y: techY + row * commSpacingV
            };
            placedComm.add(commId);
          });

          techY += techRowHeight(tid);
        });

        y += groupHeight(group);
      });
    }

    layoutCol(leftGroups, 130, true);
    layoutCol(rightGroups, width - 130, false);

    // Place any commentary not linked to a technique
    const unplaced = nodes.filter((n) => n.type === "commentary" && !placedComm.has(n.id));
    unplaced.forEach((n, i) => {
      positions[n.id] = { x: width / 2, y: 30 + i * commSpacingV };
    });

    // Scale to fit viewport if layout overflows
    const allPos = Object.values(positions);
    const margin = 25;
    const minY = Math.min(...allPos.map((p) => p.y));
    const maxY = Math.max(...allPos.map((p) => p.y));
    if (maxY - minY > height - margin * 2) {
      const scale = (height - margin * 2) / (maxY - minY);
      allPos.forEach((p) => { p.y = margin + (p.y - minY) * scale; });
    }
    const minX = Math.min(...allPos.map((p) => p.x));
    const maxX = Math.max(...allPos.map((p) => p.x));
    if (maxX - minX > width - margin * 2) {
      const scale = (width - margin * 2) / (maxX - minX);
      allPos.forEach((p) => { p.x = margin + (p.x - minX) * scale; });
    }

    return positions;
  }

  function computeSequentialLayout() {
    const positions = {};

    // Build technique → commentary mapping
    const techToComm = new Map();
    const placedComm = new Set();
    for (const c of commentary) {
      for (const tid of c.techniqueIds || []) {
        if (!techToComm.has(tid)) techToComm.set(tid, []);
        techToComm.get(tid).push(`comm-${c.id}`);
      }
    }

    const catGroups = [];
    for (const catId of referencedCatIds) {
      const cat = catLookup.get(catId);
      if (!cat) continue;
      const techs = [...referencedTechIds].filter((tid) => {
        const t = techLookup.get(tid);
        return t && t.categoryId === catId;
      });
      catGroups.push({ catId, name: cat.name, techs });
    }
    catGroups.sort((a, b) => a.name.localeCompare(b.name));

    const colX = { category: width * 0.08, technique: width * 0.28, commentary: width * 0.52 };
    const techBaseSpacing = 20;
    const commSpacingV = 13;
    const commSpacingH = 25;
    const maxPerSubCol = 3;
    const catGap = 25;

    function techRowHeight(tid) {
      const n = (techToComm.get(tid) || []).filter((id) => !placedComm.has(id)).length;
      if (n === 0) return techBaseSpacing;
      return Math.max(techBaseSpacing, Math.min(n, maxPerSubCol) * commSpacingV + 6);
    }

    let y = 30;

    catGroups.forEach((group) => {
      positions[`cat-${group.catId}`] = { x: colX.category, y };

      group.techs.forEach((tid) => {
        positions[`tech-${tid}`] = { x: colX.technique, y };

        const commIds = (techToComm.get(tid) || []).filter((id) => !placedComm.has(id));
        commIds.forEach((commId, i) => {
          const subCol = Math.floor(i / maxPerSubCol);
          const row = i % maxPerSubCol;
          positions[commId] = {
            x: colX.commentary + subCol * commSpacingH,
            y: y + row * commSpacingV
          };
          placedComm.add(commId);
        });

        y += techRowHeight(tid);
      });

      y += catGap;
    });

    // Unplaced commentary (not linked to any technique)
    const unplaced = nodes.filter((n) => n.type === "commentary" && !placedComm.has(n.id));
    unplaced.forEach((n, i) => {
      positions[n.id] = { x: colX.commentary, y: 30 + i * commSpacingV };
    });

    // Scale to fit viewport if layout overflows
    const allPos = Object.values(positions);
    const margin = 25;
    const minY = Math.min(...allPos.map((p) => p.y));
    const maxY = Math.max(...allPos.map((p) => p.y));
    if (maxY - minY > height - margin * 2) {
      const scale = (height - margin * 2) / (maxY - minY);
      allPos.forEach((p) => { p.y = margin + (p.y - minY) * scale; });
    }

    return positions;
  }

  function applyComputedLayout(positions) {
    stopForce();
    nodes.forEach((n) => {
      const pos = positions[n.id];
      if (pos) { n.x = pos.x; n.y = pos.y; n.fx = pos.x; n.fy = pos.y; }
    });
    catNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    techNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    commNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    updateLinks();
    layoutModified = true;
    status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
  }

  addButton(toolbar, "\uD83D\uDCBE Save Layout", function () {
    try {
      const positions = {};
      nodes.forEach((n) => { positions[n.id] = { x: n.x, y: n.y }; });
      localStorage.setItem(COMMENTARY_LAYOUT_KEY, JSON.stringify({ positions }));
      layoutModified = false;
      layoutSource = "saved";
      showStatus("\u2713 Layout saved!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("\u2717 Save failed: " + e.message, "#c9190b", 3000);
    }
  });

  addButton(toolbar, "\u229E Balanced", function () {
    applyComputedLayout(computeBalancedLayout());
    showStatus("\u229E Balanced layout applied (unsaved)", "#7c5e10", 3000);
  });

  addButton(toolbar, "\u2630 Sequential", function () {
    applyComputedLayout(computeSequentialLayout());
    showStatus("\u2630 Sequential layout applied (unsaved)", "#7c5e10", 3000);
  });

  const forceBtn = addButton(toolbar, "\u26A1 Force", function () {
    if (forceSimulation) {
      stopForce();
      showStatus("Force stopped", "#666", 2000);
    } else {
      startForce();
      showStatus("\u26A1 Force active", "#7c5e10", 0);
    }
  });

  addButton(toolbar, "\uD83D\uDCE4 Export", function () {
    try {
      const positions = {};
      nodes.forEach((n) => { positions[n.id] = { x: n.x, y: n.y }; });
      const blob = new Blob([JSON.stringify({ positions }, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "commentary-layout.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showStatus("\u2713 Layout exported!", "#2e7d32", 2000);
    } catch (e) {
      showStatus("\u2717 Export failed: " + e.message, "#c9190b", 3000);
    }
  });

  const fileInput = toolbar.append("input")
    .attr("type", "file").attr("accept", ".json").style("display", "none")
    .on("change", function () {
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          if (!imported.positions) throw new Error("Invalid layout: missing positions");
          localStorage.setItem(COMMENTARY_LAYOUT_KEY, JSON.stringify(imported));
          showStatus("\u2713 Imported! Reloading...", "#2e7d32", 1000);
          setTimeout(() => location.reload(), 1000);
        } catch (err) {
          showStatus("\u2717 Import failed: " + err.message, "#c9190b", 3000);
        }
      };
      reader.readAsText(file);
    });

  addButton(toolbar, "\uD83D\uDCE5 Import", () => fileInput.node().click());

  addButton(toolbar, "\u21BA Reset", function () {
    try {
      localStorage.removeItem(COMMENTARY_LAYOUT_KEY);
      location.reload();
    } catch (e) {
      showStatus("\u2717 Reset failed: " + e.message, "#c9190b", 3000);
    }
  });

  // ── SVG ──
  const svg = container.append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("width", width)
    .attr("height", height)
    .style("background", "#fafafa")
    .style("border-radius", "4px")
    .style("user-select", "none");

  const g = svg.append("g");

  // Links
  const linkGroup = g.append("g").attr("class", "links");
  const linkElements = linkGroup.selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke", (d) => d.color)
    .attr("stroke-opacity", 0.5)
    .attr("stroke-width", (d) => d.type === "category-technique" ? 2 : 1)
    .style("pointer-events", "none");

  function updateLinks() {
    linkElements
      .attr("x1", (d) => { const s = typeof d.source === "string" ? nodeById.get(d.source) : d.source; return s ? s.x : 0; })
      .attr("y1", (d) => { const s = typeof d.source === "string" ? nodeById.get(d.source) : d.source; return s ? s.y : 0; })
      .attr("x2", (d) => { const t = typeof d.target === "string" ? nodeById.get(d.target) : d.target; return t ? t.x : 0; })
      .attr("y2", (d) => { const t = typeof d.target === "string" ? nodeById.get(d.target) : d.target; return t ? t.y : 0; });
  }

  // Node groups
  const nodeGroup = g.append("g").attr("class", "nodes");

  // Category nodes — rectangles sized to fully contain text
  const catNodes = nodeGroup.selectAll(".cat-node")
    .data(nodes.filter((n) => n.type === "category"))
    .join("g")
    .attr("class", "cat-node")
    .style("cursor", "grab");

  catNodes.each(function (d) {
    const group = d3.select(this);
    // Create text first to measure
    const textEl = group.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .style("font-size", "12px")
      .style("font-weight", "bold")
      .style("fill", "white")
      .style("pointer-events", "none")
      .text(d.name);

    // Measure — use getBBox with fallback to character estimate
    let textW, textH;
    try {
      const bbox = textEl.node().getBBox();
      textW = bbox.width > 0 ? bbox.width : d.name.length * 7.5;
      textH = bbox.height > 0 ? bbox.height : 14;
    } catch (e) {
      textW = d.name.length * 7.5;
      textH = 14;
    }

    const padX = 14;
    const padY = 10;
    d.rectW = textW + padX * 2;
    d.rectH = textH + padY * 2;

    group.insert("rect", "text")
      .attr("x", -d.rectW / 2)
      .attr("y", -d.rectH / 2)
      .attr("width", d.rectW)
      .attr("height", d.rectH)
      .attr("rx", 6)
      .attr("ry", 6)
      .attr("fill", d.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);
  });

  // Technique nodes (triangles)
  const techNodes = nodeGroup.selectAll(".tech-node")
    .data(nodes.filter((n) => n.type === "technique"))
    .join("g")
    .attr("class", "tech-node")
    .style("cursor", "grab");

  techNodes.append("path")
    .attr("d", d3.symbol().type(d3.symbolTriangle).size(200))
    .attr("fill", (d) => d.color)
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5);

  techNodes.append("text")
    .attr("text-anchor", "middle")
    .attr("y", -12)
    .style("font-size", "9px")
    .style("fill", "#333")
    .style("pointer-events", "none")
    .text((d) => d.name);

  // Commentary nodes (circles)
  const commNodes = nodeGroup.selectAll(".comm-node")
    .data(nodes.filter((n) => n.type === "commentary"))
    .join("g")
    .attr("class", "comm-node")
    .style("cursor", "pointer");

  commNodes.append("circle")
    .attr("r", (d) => d.radius)
    .attr("fill", (d) => d.color)
    .attr("stroke", "#fff")
    .attr("stroke-width", 1);

  commNodes.append("text")
    .attr("x", 10)
    .attr("y", 3)
    .style("font-size", "8px")
    .style("fill", "#555")
    .style("pointer-events", "none")
    .text((d) => d.name);

  // ── Shared interactions (zoom, marquee, multi-drag, selection) ──
  const interactions = setupNetworkInteractions({
    d3, svg, g, nodes, nodeById,
    nodeGroups: [catNodes, techNodes, commNodes],
    linkElements, updateLinks, width, height,
    toolbar, status, showStatus,
    onLayoutModified: () => {
      layoutModified = true;
      status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
    },
    uniqueId: "commentary"
  });

  // ── Tooltip ──
  const tooltip = d3.select("body").append("div")
    .attr("class", "commentary-tooltip")
    .style("position", "absolute")
    .style("visibility", "hidden")
    .style("background", "rgba(0, 0, 0, 0.95)")
    .style("color", "white")
    .style("border-radius", "4px")
    .style("padding", "10px 14px")
    .style("font-size", "12px")
    .style("max-width", "400px")
    .style("box-shadow", "0 4px 6px rgba(0,0,0,0.3)")
    .style("border", "1px solid #333")
    .style("pointer-events", "auto")
    .style("z-index", 1000)
    .style("line-height", "1.5");

  let tooltipTimeout = null;
  let isOverTooltip = false;
  let isOverNode = false;

  function showTooltip(event, d) {
    if (tooltipTimeout) { clearTimeout(tooltipTimeout); tooltipTimeout = null; }
    isOverNode = true;

    if (d.type === "commentary") {
      const typeStyle = typeBadgeColors[d.entryType] || { bg: "#f3f4f6", text: "#374151" };
      const sentLabel = d.sentiment.charAt(0).toUpperCase() + d.sentiment.slice(1);
      const sentColor = sentimentColors[d.sentiment] || sentimentColors.neutral;
      tooltip.style("visibility", "visible").html(
        `<div style="font-weight:bold;font-size:13px;margin-bottom:6px;">${d.fullTitle}</div>` +
        `<div style="margin-bottom:4px;"><span style="display:inline-block;background:${typeStyle.bg};color:${typeStyle.text};padding:1px 6px;border-radius:3px;font-size:10px;">${(d.entryType || "").replace(/_/g, " ")}</span>` +
        ` <span style="color:${sentColor};font-size:11px;">[${sentLabel}]</span></div>` +
        (d.author ? `<div style="color:#aaa;font-size:11px;">${d.author}${d.organization ? ", " + d.organization : ""}${d.date ? " \u2014 " + d.date : ""}</div>` : "") +
        (d.summary ? `<div style="margin-top:6px;color:#ccc;font-size:11px;font-style:italic;">${d.summary}</div>` : "") +
        (d.url ? `<div style="margin-top:6px;"><a href="${d.url}" target="_blank" rel="noopener" style="color:#64b5f6;text-decoration:underline;font-size:11px;">View source \u2197</a></div>` : "")
      );
    } else if (d.type === "technique") {
      const tech = techLookup.get(d.id.replace("tech-", ""));
      const desc = tech ? (tech.description || "") : "";
      tooltip.style("visibility", "visible").html(
        `<div style="font-weight:bold;font-size:13px;">${d.name}</div>` +
        (desc ? `<div style="color:#ccc;font-size:11px;margin-top:4px;">${desc.substring(0, 150)}${desc.length > 150 ? "\u2026" : ""}</div>` : "")
      );
    } else if (d.type === "category") {
      tooltip.style("visibility", "visible").html(
        `<div style="font-weight:bold;font-size:13px;">${d.name}</div>` +
        `<div style="color:#aaa;font-size:11px;margin-top:2px;">Category</div>`
      );
    }

    tooltip.style("left", (event.pageX + 15) + "px").style("top", (event.pageY - 10) + "px");
  }

  function scheduleHide() {
    if (tooltipTimeout) clearTimeout(tooltipTimeout);
    tooltipTimeout = setTimeout(() => {
      if (!isOverTooltip && !isOverNode) tooltip.style("visibility", "hidden");
    }, 300);
  }

  tooltip
    .on("mouseenter", () => { isOverTooltip = true; if (tooltipTimeout) { clearTimeout(tooltipTimeout); tooltipTimeout = null; } })
    .on("mouseleave", () => { isOverTooltip = false; scheduleHide(); });

  [catNodes, techNodes, commNodes].forEach((sel) => {
    sel
      .on("mouseenter", (event, d) => showTooltip(event, d))
      .on("mousemove", (event) => tooltip.style("left", (event.pageX + 15) + "px").style("top", (event.pageY - 10) + "px"))
      .on("mouseleave", () => { isOverNode = false; scheduleHide(); });
  });

  // ── Force simulation ──
  function createSim() {
    return d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id)
        .distance((d) => d.type === "category-technique" ? 100 : 60)
        .strength((d) => d.type === "category-technique" ? 0.5 : 0.3))
      .force("charge", d3.forceManyBody().strength((d) => d.type === "category" ? -300 : d.type === "technique" ? -150 : -50))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d) => {
        if (d.type === "category") return Math.max(d.rectW, d.rectH) / 2 + 5;
        if (d.type === "technique") return 20;
        return 12;
      }))
      .force("x", d3.forceX(width / 2).strength(0.03))
      .force("y", d3.forceY(height / 2).strength(0.03));
  }

  function startForce() {
    stopForce();
    const selected = interactions.selectedNodes;
    if (selected.size > 0) {
      nodes.forEach((n) => {
        if (selected.has(n.id)) { n.fx = null; n.fy = null; }
      });
    } else {
      nodes.forEach((n) => { n.fx = null; n.fy = null; });
    }
    forceSimulation = createSim();
    forceSimulation.on("tick", () => {
      catNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      techNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      commNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      updateLinks();
    });
    forceSimulation.alpha(1).restart();
    forceBtn.style("background", "#e0e0e0");
    layoutModified = true;
  }

  function stopForce() {
    if (forceSimulation) {
      forceSimulation.stop();
      nodes.forEach((n) => { n.fx = n.x; n.fy = n.y; });
      forceSimulation = null;
    }
    forceBtn.style("background", "#fff");
  }

  // ── Initial layout ──
  if (savedPositions) {
    // Position nodes from saved state, no force needed
    catNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    techNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    commNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    updateLinks();
  } else {
    // Run force simulation for initial layout
    forceSimulation = createSim();
    forceSimulation.on("tick", () => {
      catNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      techNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      commNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      updateLinks();
    });
    // Auto-stop after settling
    forceSimulation.on("end", () => {
      nodes.forEach((n) => { n.fx = n.x; n.fy = n.y; });
      forceSimulation = null;
      forceBtn.style("background", "#fff");
    });
  }

  return container.node();
}
