// Incident register network graph: Provider → Incident

import { setupNetworkInteractions } from "./network-interactions.js";
import { setupLinkTooltips } from "./link-tooltip.js";

const INCIDENTS_LAYOUT_KEY = "incidents-view-layout-v1";

export function createIncidentsView(data, providerColors, d3) {
  const incidents = data.raw.incidents || [];
  const techLookup = new Map(data.raw.techniques.map((t) => [t.id, t]));
  const providerLookup = new Map((data.raw.providers || []).map((p) => [p.id, p]));
  const riskLookup = new Map((data.raw.risk_areas || []).map((r) => [r.id, r]));

  if (incidents.length === 0) {
    const div = document.createElement("div");
    div.style.cssText = "padding: 20px; text-align: center; color: #999; background: #f8f9fa; border-radius: 8px;";
    div.innerHTML = `<p style="font-size: 16px; margin-bottom: 8px;">No incidents recorded yet.</p>
      <p style="font-size: 13px;">Run <code>python scripts/ingest_aiid.py</code> to populate from the <a href="https://incidentdatabase.ai/">AI Incident Database</a>.</p>`;
    return div;
  }

  const severityColors = {
    critical: "#dc2626",
    high: "#ea580c",
    medium: "#ca8a04",
    low: "#64748b"
  };

  const severityBg = {
    critical: { bg: "#fef2f2", border: "#fca5a5" },
    high: { bg: "#fff7ed", border: "#fdba74" },
    medium: { bg: "#fefce8", border: "#fde047" },
    low: { bg: "#f8fafc", border: "#cbd5e1" }
  };

  const statusLabels = {
    confirmed: { bg: "#fee2e2", text: "#991b1b" },
    alleged: { bg: "#fef3c7", text: "#92400e" },
    disputed: { bg: "#e0e7ff", text: "#3730a3" },
    resolved: { bg: "#d1fae5", text: "#065f46" }
  };

  // Severity stats
  const bySeverity = {};
  for (const inc of incidents) {
    bySeverity[inc.severity] = (bySeverity[inc.severity] || 0) + 1;
  }

  // Filter to LLM-related incidents linked to known providers
  const linkedIncidents = incidents.filter(
    (inc) => (inc.providerIds || []).length > 0 && inc.isLLMRelated !== false
  );

  // Build graph
  const nodes = [];
  const links = [];
  const nodeById = new Map();

  const incidentProviderIds = new Set();
  for (const inc of linkedIncidents) {
    for (const pid of inc.providerIds || []) incidentProviderIds.add(pid);
  }

  for (const pid of incidentProviderIds) {
    const prov = providerLookup.get(pid);
    const node = {
      id: `prov-${pid}`,
      type: "provider",
      name: prov ? prov.name : pid,
      color: providerColors[prov ? prov.name : pid] || "#999",
      radius: 22
    };
    nodes.push(node);
    nodeById.set(node.id, node);
  }

  for (const inc of linkedIncidents) {
    const techNames = (inc.techniqueIds || []).map((id) => {
      const t = techLookup.get(id);
      return t ? t.name : id;
    });
    const riskNames = (inc.riskAreaIds || []).map((id) => {
      const r = riskLookup.get(id);
      return r ? r.name : id;
    });
    const provNames = (inc.providerIds || []).map((id) => {
      const p = providerLookup.get(id);
      return p ? p.name : id;
    });

    const node = {
      id: `inc-${inc.id}`,
      type: "incident",
      name: inc.title.length > 25 ? inc.title.substring(0, 23) + "\u2026" : inc.title,
      fullTitle: inc.title,
      date: inc.date || "",
      description: inc.description || "",
      severity: inc.severity,
      status: inc.status || "alleged",
      providerNames: provNames,
      techNames,
      riskNames,
      sources: inc.sources || [],
      aiidUrl: inc.aiidUrl || "",
      color: severityColors[inc.severity] || severityColors.low,
      radius: inc.severity === "critical" ? 12 : inc.severity === "high" ? 10 : 8
    };
    nodes.push(node);
    nodeById.set(node.id, node);

    for (const pid of inc.providerIds || []) {
      const provNodeId = `prov-${pid}`;
      if (nodeById.has(provNodeId)) {
        const prov = providerLookup.get(pid);
        links.push({
          source: provNodeId,
          target: node.id,
          color: providerColors[prov ? prov.name : pid] || "#ccc"
        });
      }
    }
  }

  // Load saved layout
  let savedPositions = null;
  let layoutSource = "default";
  try {
    const raw = localStorage.getItem(INCIDENTS_LAYOUT_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed.positions) {
        savedPositions = parsed.positions;
        layoutSource = "saved";
      }
    }
  } catch (e) { /* ignore */ }

  if (savedPositions) {
    nodes.forEach((n) => {
      const pos = savedPositions[n.id];
      if (pos) { n.x = pos.x; n.y = pos.y; n.fx = pos.x; n.fy = pos.y; }
    });
  }

  const width = 900;
  const height = 550;

  let forceSimulation = null;
  let layoutModified = false;

  const container = d3.create("div").style("position", "relative");

  // Severity summary bar
  const statsBar = container.append("div")
    .style("display", "flex")
    .style("gap", "12px")
    .style("margin-bottom", "10px")
    .style("flex-wrap", "wrap");

  ["critical", "high", "medium", "low"].forEach((sev) => {
    const count = bySeverity[sev] || 0;
    const bg = severityBg[sev] || severityBg.low;
    statsBar.append("div")
      .style("background", bg.bg)
      .style("border", `1px solid ${bg.border}`)
      .style("padding", "6px 14px")
      .style("border-radius", "6px")
      .style("min-width", "90px")
      .style("text-align", "center")
      .html(`<div style="font-size:18px;font-weight:bold;color:${severityColors[sev]};">${count}</div><div style="font-size:11px;color:#666;text-transform:capitalize;">${sev}</div>`);
  });

  // Legend
  const legend = container.append("div")
    .style("display", "flex")
    .style("gap", "14px")
    .style("margin-bottom", "8px")
    .style("font-size", "11px")
    .style("color", "#666")
    .style("flex-wrap", "wrap");

  legend.append("span").html(`<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#888;margin-right:3px;vertical-align:middle;"></span> Provider`);
  [["critical", "Critical"], ["high", "High"], ["medium", "Medium"], ["low", "Low"]].forEach(([key, label]) => {
    legend.append("span").html(
      `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${severityColors[key]};margin-right:3px;vertical-align:middle;"></span> ${label}`
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
    const provEntries = nodes.filter((n) => n.type === "provider");
    const incEntries = nodes.filter((n) => n.type === "incident");

    // Providers in a circle
    const cx = width / 2, cy = height / 2;
    const provR = Math.min(width, height) * 0.18;

    provEntries.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / provEntries.length - Math.PI / 2;
      positions[n.id] = {
        x: cx + provR * Math.cos(angle),
        y: cy + provR * Math.sin(angle)
      };
    });

    // Group incidents by primary provider
    const incByProv = new Map();
    for (const inc of incEntries) {
      const linkedProvs = links
        .filter((l) => {
          const tid = typeof l.target === "string" ? l.target : l.target.id;
          return tid === inc.id;
        })
        .map((l) => typeof l.source === "string" ? l.source : l.source.id);
      const primary = linkedProvs[0] || provEntries[0]?.id;
      if (!incByProv.has(primary)) incByProv.set(primary, []);
      incByProv.get(primary).push(inc);
    }

    // Fan incidents outward from each provider in multiple rings
    const ringCapacity = 12;
    const ringGap = 30;
    const baseIncR = 80;
    for (const [provId, incs] of incByProv) {
      const provPos = positions[provId];
      if (!provPos) continue;
      const baseAngle = Math.atan2(provPos.y - cy, provPos.x - cx);

      incs.forEach((inc, i) => {
        const ring = Math.floor(i / ringCapacity);
        const idxInRing = i % ringCapacity;
        const countInRing = Math.min(ringCapacity, incs.length - ring * ringCapacity);
        const r = baseIncR + ring * ringGap;
        const fanSpread = Math.min(Math.PI * 0.7, countInRing * 0.15);
        const a = baseAngle - fanSpread / 2 + (countInRing > 1 ? (fanSpread * idxInRing) / (countInRing - 1) : 0);
        positions[inc.id] = {
          x: provPos.x + r * Math.cos(a),
          y: provPos.y + r * Math.sin(a)
        };
      });
    }

    // Scale to fit viewport if layout overflows
    const allPos = Object.values(positions);
    const margin = 30;
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
    const provEntries = nodes.filter((n) => n.type === "provider");

    // Group incidents by primary provider
    const incByProv = new Map();
    for (const inc of nodes.filter((n) => n.type === "incident")) {
      const linkedProvs = links
        .filter((l) => {
          const tid = typeof l.target === "string" ? l.target : l.target.id;
          return tid === inc.id;
        })
        .map((l) => typeof l.source === "string" ? l.source : l.source.id);
      const primary = linkedProvs[0] || provEntries[0]?.id || "unknown";
      if (!incByProv.has(primary)) incByProv.set(primary, []);
      incByProv.get(primary).push(inc);
    }

    // Build blocks: each provider + its incidents
    const incSpacing = 16;
    const provHeaderGap = 35;
    const blockGap = 30;
    const blocks = provEntries.map((prov) => {
      const incs = incByProv.get(prov.id) || [];
      const blockH = provHeaderGap + incs.length * incSpacing;
      return { prov, incs, blockH };
    });

    // Distribute blocks across columns (greedy bin-packing by height)
    const totalH = blocks.reduce((s, b) => s + b.blockH + blockGap, 0);
    const numCols = Math.max(1, Math.ceil(totalH / (height - 40)));
    const cols = Array.from({ length: numCols }, () => ({ blocks: [], height: 0 }));

    const sortedBlocks = [...blocks].sort((a, b) => b.blockH - a.blockH);
    for (const block of sortedBlocks) {
      const shortest = cols.reduce((min, col) => col.height < min.height ? col : min, cols[0]);
      shortest.blocks.push(block);
      shortest.height += block.blockH + blockGap;
    }

    // Sort within columns alphabetically for readability
    cols.forEach((col) => col.blocks.sort((a, b) => a.prov.name.localeCompare(b.prov.name)));

    // Position blocks in multi-column grid
    const colWidth = (width - 60) / numCols;
    const incOffsetX = 35;

    cols.forEach((col, colIdx) => {
      const colX = 30 + colIdx * colWidth + colWidth / 3;
      let y = 25;

      col.blocks.forEach((block) => {
        positions[block.prov.id] = { x: colX, y };

        block.incs.forEach((inc, i) => {
          positions[inc.id] = {
            x: colX + incOffsetX,
            y: y + provHeaderGap + i * incSpacing
          };
        });

        y += block.blockH + blockGap;
      });
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
    provNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    incNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    updateLinks();
    layoutModified = true;
    status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
  }

  addButton(toolbar, "\uD83D\uDCBE Save Layout", function () {
    try {
      const positions = {};
      nodes.forEach((n) => { positions[n.id] = { x: n.x, y: n.y }; });
      localStorage.setItem(INCIDENTS_LAYOUT_KEY, JSON.stringify({ positions }));
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
      a.download = "incidents-layout.json";
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
          localStorage.setItem(INCIDENTS_LAYOUT_KEY, JSON.stringify(imported));
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
      localStorage.removeItem(INCIDENTS_LAYOUT_KEY);
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
    .attr("stroke-opacity", 0.4)
    .attr("stroke-width", 1.5)
    .style("pointer-events", "none");

  function updateLinks() {
    linkElements
      .attr("x1", (d) => { const s = typeof d.source === "string" ? nodeById.get(d.source) : d.source; return s ? s.x : 0; })
      .attr("y1", (d) => { const s = typeof d.source === "string" ? nodeById.get(d.source) : d.source; return s ? s.y : 0; })
      .attr("x2", (d) => { const t = typeof d.target === "string" ? nodeById.get(d.target) : d.target; return t ? t.x : 0; })
      .attr("y2", (d) => { const t = typeof d.target === "string" ? nodeById.get(d.target) : d.target; return t ? t.y : 0; });
    if (linkTooltips) linkTooltips.updateHitAreas();
  }

  // Link tooltips
  const linkTooltips = setupLinkTooltips({
    d3, svg, linkGroup, linkElements, links, nodeById,
    uniqueId: "incidents",
    buildTooltipHtml: (d) => {
      const source = typeof d.source === "string" ? nodeById.get(d.source) : d.source;
      const target = typeof d.target === "string" ? nodeById.get(d.target) : d.target;
      if (!source || !target) return null;
      const provNode = source.type === "provider" ? source : target;
      const incNode = source.type === "incident" ? source : target;
      const sevColor = severityColors[incNode.severity] || "#666";
      const statStyle = statusLabels[incNode.status] || statusLabels.alleged;
      return `<h4 style="margin:0 0 6px;color:#ffa726;font-size:13px;">${provNode.name} \u2192 Incident</h4>` +
        `<div style="font-size:12px;font-weight:bold;margin-bottom:4px;">${incNode.fullTitle || incNode.name}</div>` +
        `<div style="margin-bottom:4px;">` +
        `<span style="color:${sevColor};font-weight:bold;text-transform:capitalize;">${incNode.severity || "unknown"}</span>` +
        `<span style="display:inline-block;background:${statStyle.bg};color:${statStyle.text};padding:1px 6px;border-radius:3px;font-size:10px;margin-left:6px;text-transform:capitalize;">${incNode.status}</span>` +
        (incNode.date ? ` <span style="color:#999;font-size:11px;margin-left:6px;">${incNode.date}</span>` : "") +
        `</div>` +
        (incNode.techNames && incNode.techNames.length > 0 ? `<div style="font-size:11px;color:#aaa;margin-bottom:2px;"><strong style="color:#ccc;">Techniques:</strong> ${incNode.techNames.join(", ")}</div>` : "") +
        (incNode.riskNames && incNode.riskNames.length > 0 ? `<div style="font-size:11px;color:#aaa;"><strong style="color:#ccc;">Risk areas:</strong> ${incNode.riskNames.join(", ")}</div>` : "");
    }
  });

  // Node groups
  const nodeGroup = g.append("g").attr("class", "nodes");

  // Provider nodes
  const provNodes = nodeGroup.selectAll(".prov-node")
    .data(nodes.filter((n) => n.type === "provider"))
    .join("g")
    .attr("class", "prov-node")
    .style("cursor", "grab");

  provNodes.append("circle")
    .attr("r", (d) => d.radius)
    .attr("fill", (d) => d.color)
    .attr("stroke", "#fff")
    .attr("stroke-width", 2);

  provNodes.append("text")
    .attr("text-anchor", "middle")
    .attr("dy", -28)
    .style("font-size", "11px")
    .style("font-weight", "bold")
    .style("fill", "#333")
    .style("pointer-events", "none")
    .text((d) => d.name);

  // Incident nodes
  const incNodes = nodeGroup.selectAll(".inc-node")
    .data(nodes.filter((n) => n.type === "incident"))
    .join("g")
    .attr("class", "inc-node")
    .style("cursor", "pointer");

  incNodes.append("circle")
    .attr("r", (d) => d.radius)
    .attr("fill", (d) => d.color)
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5);

  incNodes.append("text")
    .attr("x", (d) => d.radius + 4)
    .attr("y", 3)
    .style("font-size", "8px")
    .style("fill", "#555")
    .style("pointer-events", "none")
    .text((d) => d.name);

  // ── Shared interactions (zoom, marquee, multi-drag, selection) ──
  const interactions = setupNetworkInteractions({
    d3, svg, g, nodes, nodeById,
    nodeGroups: [provNodes, incNodes],
    linkElements, updateLinks, width, height,
    toolbar, status, showStatus,
    onLayoutModified: () => {
      layoutModified = true;
      status.text("\u26A0 Unsaved changes").style("color", "#c9190b");
    },
    uniqueId: "incidents"
  });

  // ── Tooltip ──
  const tooltip = d3.select("body").append("div")
    .attr("class", "incidents-tooltip")
    .style("position", "absolute")
    .style("visibility", "hidden")
    .style("background", "rgba(0, 0, 0, 0.95)")
    .style("color", "white")
    .style("border-radius", "4px")
    .style("padding", "12px 14px")
    .style("font-size", "12px")
    .style("max-width", "420px")
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

    if (d.type === "incident") {
      const sevColor = severityColors[d.severity] || "#666";
      const statStyle = statusLabels[d.status] || statusLabels.alleged;

      let sourcesHtml = "";
      if (d.sources.length > 0) {
        sourcesHtml = `<div style="margin-top:6px;"><strong>Sources:</strong><ul style="margin:4px 0 0 0;padding-left:16px;">` +
          d.sources.map((s) => `<li><a href="${s.url}" target="_blank" rel="noopener" style="color:#64b5f6;text-decoration:underline;">${s.title || s.url}</a></li>`).join("") +
          `</ul></div>`;
      }

      tooltip.style("visibility", "visible").html(
        `<div style="font-weight:bold;font-size:13px;margin-bottom:6px;">${d.fullTitle}</div>` +
        `<div style="margin-bottom:6px;">` +
        `<span style="color:${sevColor};font-weight:bold;text-transform:capitalize;">${d.severity}</span>` +
        ` <span style="display:inline-block;background:${statStyle.bg};color:${statStyle.text};padding:1px 6px;border-radius:3px;font-size:10px;margin-left:6px;text-transform:capitalize;">${d.status}</span>` +
        (d.date ? ` <span style="color:#999;font-size:11px;margin-left:6px;">${d.date}</span>` : "") +
        `</div>` +
        (d.description ? `<div style="color:#ccc;font-size:11px;margin-bottom:6px;">${d.description.substring(0, 200)}${d.description.length > 200 ? "\u2026" : ""}</div>` : "") +
        (d.techNames.length > 0 ? `<div style="margin-bottom:4px;"><strong>Techniques:</strong> <span style="color:#aaa;font-size:11px;">${d.techNames.join(", ")}</span></div>` : "") +
        (d.riskNames.length > 0 ? `<div style="margin-bottom:4px;"><strong>Risk areas:</strong> <span style="color:#aaa;font-size:11px;">${d.riskNames.join(", ")}</span></div>` : "") +
        sourcesHtml +
        (d.aiidUrl ? `<div style="margin-top:6px;"><a href="${d.aiidUrl}" target="_blank" rel="noopener" style="color:#64b5f6;font-size:11px;">View on AIID \u2197</a></div>` : "")
      );
    } else if (d.type === "provider") {
      const incCount = links.filter((l) => {
        const sid = typeof l.source === "string" ? l.source : l.source.id;
        return sid === d.id;
      }).length;
      tooltip.style("visibility", "visible").html(
        `<div style="font-weight:bold;font-size:13px;">${d.name}</div>` +
        `<div style="color:#aaa;font-size:11px;margin-top:2px;">${incCount} incident${incCount !== 1 ? "s" : ""}</div>`
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

  [provNodes, incNodes].forEach((sel) => {
    sel
      .on("mouseenter", (event, d) => showTooltip(event, d))
      .on("mousemove", (event) => tooltip.style("left", (event.pageX + 15) + "px").style("top", (event.pageY - 10) + "px"))
      .on("mouseleave", () => { isOverNode = false; scheduleHide(); });
  });

  // ── Force simulation ──
  function createSim() {
    return d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id)
        .distance(80)
        .strength(0.4))
      .force("charge", d3.forceManyBody().strength((d) => d.type === "provider" ? -400 : -80))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d) => d.type === "provider" ? 35 : 18))
      .force("x", d3.forceX(width / 2).strength(0.12))
      .force("y", d3.forceY(height / 2).strength(0.12));
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
      const pad = 30;
      nodes.forEach((n) => {
        if (n.fx == null) {
          n.x = Math.max(pad, Math.min(width - pad, n.x));
          n.y = Math.max(pad, Math.min(height - pad, n.y));
        }
      });
      provNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      incNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
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
    provNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    incNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    updateLinks();
  } else {
    forceSimulation = createSim();
    forceSimulation.on("tick", () => {
      const pad = 30;
      nodes.forEach((n) => {
        n.x = Math.max(pad, Math.min(width - pad, n.x));
        n.y = Math.max(pad, Math.min(height - pad, n.y));
      });
      provNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      incNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
      updateLinks();
    });
    forceSimulation.on("end", () => {
      nodes.forEach((n) => { n.fx = n.x; n.fy = n.y; });
      forceSimulation = null;
      forceBtn.style("background", "#fff");
    });
  }

  return container.node();
}
