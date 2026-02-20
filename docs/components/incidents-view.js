// Incident register network graph: Provider → Incident

export function createIncidentsView(data, providerColors, d3) {
  const incidents = data.raw.incidents || [];
  const techLookup = new Map(data.raw.techniques.map((t) => [t.id, t]));
  const providerLookup = new Map((data.raw.providers || []).map((p) => [p.id, p]));
  const riskLookup = new Map((data.raw.risk_areas || []).map((r) => [r.id, r]));

  if (incidents.length === 0) {
    const div = document.createElement("div");
    div.style.cssText = "padding: 20px; text-align: center; color: #999; background: #f8f9fa; border-radius: 8px;";
    div.innerHTML = `<p style="font-size: 16px; margin-bottom: 8px;">No incidents recorded yet.</p>
      <p style="font-size: 13px;">Add entries to <code>data/incidents.json</code> to populate this view.</p>`;
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

  // Build graph
  const nodes = [];
  const links = [];
  const nodeById = new Map();

  // Provider nodes (only those with incidents)
  const incidentProviderIds = new Set();
  for (const inc of incidents) {
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

  // Incident nodes
  for (const inc of incidents) {
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
      color: severityColors[inc.severity] || severityColors.low,
      radius: inc.severity === "critical" ? 12 : inc.severity === "high" ? 10 : 8
    };
    nodes.push(node);
    nodeById.set(node.id, node);

    // Provider → Incident links
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

  const width = 900;
  const height = 550;

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

  const svg = container.append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("width", width)
    .attr("height", height)
    .style("background", "#fafafa")
    .style("border-radius", "4px");

  const g = svg.append("g");

  // Zoom
  const zoomBehavior = d3.zoom()
    .scaleExtent([0.3, 3])
    .on("zoom", (event) => { g.attr("transform", event.transform); });
  svg.call(zoomBehavior);

  // Links
  const linkGroup = g.append("g").attr("class", "links");
  const linkElements = linkGroup.selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke", (d) => d.color)
    .attr("stroke-opacity", 0.4)
    .attr("stroke-width", 1.5);

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

  // Tooltip
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
        sourcesHtml
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

  // Force simulation
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id((d) => d.id)
      .distance(80)
      .strength(0.4))
    .force("charge", d3.forceManyBody().strength((d) => d.type === "provider" ? -400 : -80))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius((d) => d.type === "provider" ? 35 : 18))
    .force("x", d3.forceX(width / 2).strength(0.04))
    .force("y", d3.forceY(height / 2).strength(0.04));

  simulation.on("tick", () => {
    linkElements
      .attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
    provNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    incNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });

  // Drag
  function dragBehavior() {
    return d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }

  provNodes.call(dragBehavior());
  incNodes.call(dragBehavior());

  return container.node();
}
