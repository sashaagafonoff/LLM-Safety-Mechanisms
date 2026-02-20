// Third-party commentary network graph: Category → Technique → Commentary

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
    const node = {
      id: `cat-${catId}`,
      type: "category",
      name: cat.name,
      color: categoryColors[cat.name] || "#999",
      radius: 18
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
      categoryId: tech.categoryId,
      radius: 10
    };
    nodes.push(node);
    nodeById.set(node.id, node);

    // Category → Technique link
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

    // Technique → Commentary links (one per referenced technique)
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

  // Layout
  const width = 900;
  const height = 600;

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

  legend.append("span").html(`<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#888;margin-right:3px;vertical-align:middle;"></span> Category`);
  legend.append("span").html(`<span style="display:inline-block;width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:10px solid #888;margin-right:3px;vertical-align:middle;"></span> Technique`);

  [["positive", "Positive"], ["negative", "Negative"], ["mixed", "Mixed"], ["neutral", "Neutral"]].forEach(([key, label]) => {
    legend.append("span").html(
      `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${sentimentColors[key]};margin-right:3px;vertical-align:middle;"></span> ${label}`
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
    .attr("stroke-opacity", 0.5)
    .attr("stroke-width", (d) => d.type === "category-technique" ? 2 : 1);

  // Node groups
  const nodeGroup = g.append("g").attr("class", "nodes");

  // Category nodes (rounded rects)
  const catNodes = nodeGroup.selectAll(".cat-node")
    .data(nodes.filter((n) => n.type === "category"))
    .join("g")
    .attr("class", "cat-node")
    .style("cursor", "grab");

  catNodes.each(function (d) {
    const group = d3.select(this);
    const textEl = group.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .style("font-size", "11px")
      .style("font-weight", "bold")
      .style("fill", "white")
      .style("pointer-events", "none")
      .text(d.name);
    const bbox = textEl.node().getBBox();
    const pad = 8;
    d.rectW = bbox.width + pad * 2;
    d.rectH = bbox.height + pad * 2;
    group.insert("rect", "text")
      .attr("x", -d.rectW / 2)
      .attr("y", -d.rectH / 2)
      .attr("width", d.rectW)
      .attr("height", d.rectH)
      .attr("rx", 6)
      .attr("ry", 6)
      .attr("fill", d.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);
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

  // Tooltip
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

  // Force simulation
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id((d) => d.id)
      .distance((d) => d.type === "category-technique" ? 100 : 60)
      .strength((d) => d.type === "category-technique" ? 0.5 : 0.3))
    .force("charge", d3.forceManyBody().strength((d) => d.type === "category" ? -300 : d.type === "technique" ? -150 : -50))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius((d) => d.type === "category" ? 40 : d.type === "technique" ? 20 : 12))
    .force("x", d3.forceX(width / 2).strength(0.03))
    .force("y", d3.forceY(height / 2).strength(0.03));

  simulation.on("tick", () => {
    linkElements
      .attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
    catNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    techNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
    commNodes.attr("transform", (d) => `translate(${d.x},${d.y})`);
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

  catNodes.call(dragBehavior());
  techNodes.call(dragBehavior());
  commNodes.call(dragBehavior());

  return container.node();
}
