// Coverage heatmap: provider × technique matrix
// Ported from Python generate_dashboard.py: create_coverage_heatmap

export function createCoverageHeatmap(data, filteredData, categoryColors, providerColors, d3) {
  // --- Build provider-technique matrix from filtered data ---
  const providerTechniques = new Map();

  filteredData.forEach((d) => {
    if (!d.provider || !d.technique) return;
    if (!providerTechniques.has(d.provider)) providerTechniques.set(d.provider, new Map());
    const techMap = providerTechniques.get(d.provider);
    if (!techMap.has(d.technique)) techMap.set(d.technique, []);
    techMap.get(d.technique).push(d);
  });

  // Provider order: by count desc, then alphabetical
  const providerOrder = [...providerTechniques.keys()].sort((a, b) => {
    const countA = filteredData.filter((d) => d.provider === a).length;
    const countB = filteredData.filter((d) => d.provider === b).length;
    return countB - countA || a.localeCompare(b);
  });

  if (providerOrder.length === 0) {
    const empty = d3.create("div")
      .style("padding", "40px")
      .style("text-align", "center")
      .style("color", "#999");
    empty.append("p").text("No data matches current filters.");
    return empty.node();
  }

  // Sort techniques by category then name
  const catLookup = new Map(data.raw.categories.map((c) => [c.id, c.name]));
  const techDefById = new Map(data.raw.techniques.map((t) => [t.name, t]));
  const techDefs = data.raw.techniques
    .filter((t) => t.status !== "aspirational")
    .sort((a, b) => {
      const catA = catLookup.get(a.categoryId) || "";
      const catB = catLookup.get(b.categoryId) || "";
      return catA.localeCompare(catB) || a.name.localeCompare(b.name);
    });

  // Only include techniques that appear in filtered data
  const activeTechNames = new Set(filteredData.map((d) => d.technique));
  const sortedTechniques = techDefs.filter((t) => activeTechNames.has(t.name));

  // Build matrix: rows = techniques, cols = providers
  const matrix = sortedTechniques.map((tech) => {
    return providerOrder.map((prov) => {
      const techMap = providerTechniques.get(prov);
      const records = techMap ? techMap.get(tech.name) || [] : [];
      if (records.length === 0) return 0;
      if (records.some((r) => r.confidence === "High")) return 3;
      if (records.some((r) => r.confidence === "Medium")) return 2;
      return 1;
    });
  });

  // --- Dimensions ---
  const cellW = 64;
  const cellH = 20;
  const labelW = 280;
  const headerH = 120;
  const catColW = 12;
  const legendH = 40;
  const width = labelW + catColW + providerOrder.length * cellW + 30;
  const height = headerH + sortedTechniques.length * cellH + legendH + 10;

  const colorScale = [
    "#f0f0f0", // 0 - no detection
    "#ff6b6b", // 1 - low
    "#ffd93d", // 2 - medium
    "#4ecdc4"  // 3 - high
  ];

  const ratingText = ["\u2014", "Low", "Med", "High"];

  // --- SVG ---
  const svg = d3.create("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("width", width)
    .attr("height", height)
    .style("font-family", "system-ui, sans-serif")
    .style("overflow", "visible");

  // --- Detail panel state ---
  let activePanel = null;
  let selectedCell = null;
  let isPinned = false;
  let hoverCell = null;

  function removePanel() {
    if (activePanel) {
      activePanel.remove();
      activePanel = null;
    }
    d3.selectAll(".heatmap-detail-panel").remove();
  }

  function dismissAll() {
    removePanel();
    if (selectedCell) {
      selectedCell.attr("stroke", "#fff").attr("stroke-width", 1);
      selectedCell = null;
    }
    isPinned = false;
  }

  function buildPanelHtml(prov, tech, records) {
    const techDef = techDefById.get(tech.name);
    const catName = catLookup.get(tech.categoryId) || "Uncategorized";
    const catColor = categoryColors[catName] || "#999";

    const confidences = records.map((r) => r.confidence || "Unknown");
    let bestConf = "Unknown";
    if (confidences.includes("High")) bestConf = "High";
    else if (confidences.includes("Medium")) bestConf = "Medium";
    else if (confidences.includes("Low")) bestConf = "Low";

    const seenSources = new Set();
    const sourceItems = [];
    records.forEach((r) => {
      const key = r.source_uri || r.source;
      if (seenSources.has(key)) return;
      seenSources.add(key);
      if (r.source_uri && r.source_uri !== "<missing>") {
        sourceItems.push(`<a href="${r.source_uri}" target="_blank" style="color:#64b5f6;text-decoration:none;">${r.source || "View Source"}</a>`);
      } else if (r.source) {
        sourceItems.push(`<span style="color:#ccc;">${r.source}</span>`);
      }
    });

    const allEvidence = records.flatMap((r) => r.evidence || []);
    // Evidence items are objects with .text — extract and deduplicate
    const evidenceTexts = [...new Set(
      allEvidence
        .filter((e) => e && (typeof e === "string" || (e.active !== false && e.text)))
        .map((e) => typeof e === "string" ? e : e.text)
    )];
    let evidenceHtml = "";
    if (evidenceTexts.length > 0) {
      const snippets = evidenceTexts.slice(0, 5).map((txt) => {
        const display = txt.length > 200 ? txt.substring(0, 199) + "\u2026" : txt;
        return `<div style="font-style:italic;color:#ddd;line-height:1.4;margin-bottom:6px;padding-left:8px;border-left:2px solid #555;">\u201C${display}\u201D</div>`;
      });
      const moreCount = evidenceTexts.length > 5 ? ` <span style="color:#888;">+${evidenceTexts.length - 5} more</span>` : "";
      evidenceHtml =
        `<p style="margin:10px 0 6px 0;font-weight:bold;font-size:12px;">Evidence (${evidenceTexts.length}):${moreCount}</p>` +
        snippets.join("");
    }

    const models = [...new Set(records.map((r) => r.model).filter(Boolean))];
    const modelHtml = models.length > 0
      ? `<p style="margin:6px 0;font-size:12px;"><strong>Model(s):</strong> ${models.join(", ")}</p>`
      : "";

    return (
      `<div class="heatmap-drag-handle" style="cursor:grab;margin:-14px -16px 8px -16px;padding:10px 16px 6px 16px;border-bottom:1px solid #444;user-select:none;">` +
      `<h4 style="margin:0;font-size:14px;">` +
        `<span style="color:${providerColors[prov] || "#ffa726"}">${prov}</span>` +
        ` \u2192 ` +
        `<span style="color:#fff;">${tech.name}</span>` +
        `<span style="float:right;color:#666;font-size:10px;font-weight:normal;margin-top:2px;">\u2630 drag</span>` +
      `</h4>` +
      `</div>` +
      `<div style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;margin-bottom:8px;` +
        `background:${catColor};color:#fff;opacity:0.9;">${catName}</div>` +
      (techDef && techDef.description
        ? `<p style="margin:6px 0;color:#aaa;font-size:11px;">${techDef.description}</p>`
        : "") +
      `<p style="margin:8px 0 4px 0;font-size:12px;"><strong>Confidence:</strong> ` +
        `<span style="color:${bestConf === "High" ? "#4ecdc4" : bestConf === "Medium" ? "#ffd93d" : "#ff6b6b"};font-weight:bold;">${bestConf}</span>` +
        ` <span style="color:#888;">(${records.length} record${records.length > 1 ? "s" : ""})</span></p>` +
      modelHtml +
      (sourceItems.length > 0
        ? `<p style="margin:8px 0 4px 0;font-size:12px;"><strong>Source${sourceItems.length > 1 ? "s" : ""}:</strong></p>` +
          `<div style="margin-left:8px;">${sourceItems.map((s) => `<div style="margin-bottom:3px;">\u2022 ${s}</div>`).join("")}</div>`
        : "") +
      evidenceHtml
    );
  }

  function showPanel(event, prov, tech, records, pinned) {
    removePanel();

    const panel = d3.select("body").append("div")
      .attr("class", "heatmap-detail-panel")
      .style("position", "absolute")
      .style("text-align", "left")
      .style("padding", "14px 16px")
      .style("font", "12px/1.5 system-ui, sans-serif")
      .style("background", "rgba(0, 0, 0, 0.95)")
      .style("color", "white")
      .style("border-radius", "6px")
      .style("max-width", "440px")
      .style("min-width", "300px")
      .style("box-shadow", "0 4px 12px rgba(0,0,0,0.4)")
      .style("border", "1px solid #444")
      .style("pointer-events", pinned ? "auto" : "none")
      .style("z-index", 1000)
      .style("left", (event.pageX + 14) + "px")
      .style("top", (event.pageY - 20) + "px")
      .style("opacity", 0);

    let html = buildPanelHtml(prov, tech, records);
    if (pinned) {
      html += `<div style="margin-top:10px;padding-top:8px;border-top:1px solid #444;color:#666;font-size:10px;text-align:right;">Click elsewhere to close</div>`;
    }
    panel.html(html);
    panel.transition().duration(150).style("opacity", 0.97);

    // Reposition if off-screen
    requestAnimationFrame(() => {
      const node = panel.node();
      if (!node) return;
      const box = node.getBoundingClientRect();
      if (box.right > window.innerWidth - 10) {
        panel.style("left", Math.max(10, event.pageX - box.width - 14) + "px");
      }
      if (box.bottom > window.innerHeight - 10) {
        panel.style("top", Math.max(10, event.pageY - box.height - 14) + "px");
      }
    });

    // Make pinned panels draggable via the header handle
    if (pinned) {
      const handle = panel.select(".heatmap-drag-handle");
      let dragOffsetX = 0, dragOffsetY = 0, dragging = false;

      handle.on("mousedown", function (e) {
        e.preventDefault();
        e.stopPropagation();
        dragging = true;
        const panelNode = panel.node();
        const rect = panelNode.getBoundingClientRect();
        dragOffsetX = e.clientX - rect.left;
        dragOffsetY = e.clientY - rect.top;
        handle.style("cursor", "grabbing");

        function onMove(e2) {
          if (!dragging) return;
          panel
            .style("left", (e2.pageX - dragOffsetX) + "px")
            .style("top", (e2.pageY - dragOffsetY) + "px");
        }
        function onUp() {
          dragging = false;
          handle.style("cursor", "grab");
          document.removeEventListener("mousemove", onMove);
          document.removeEventListener("mouseup", onUp);
        }
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
      });
    }

    activePanel = panel;
  }

  // Dismiss pinned panel on background click
  d3.select("body").on("click.heatmap-dismiss", function (event) {
    if (isPinned && activePanel && !event.target.closest(".heatmap-detail-panel")) {
      dismissAll();
    }
  });

  // --- Provider header labels (rotated) ---
  const headerG = svg.append("g")
    .attr("transform", `translate(${labelW + catColW}, ${headerH})`);

  headerG.selectAll("text")
    .data(providerOrder)
    .join("text")
    .attr("x", (_, i) => i * cellW + cellW / 2)
    .attr("y", -6)
    .attr("text-anchor", "start")
    .attr("transform", (_, i) => `rotate(-45, ${i * cellW + cellW / 2}, -6)`)
    .attr("font-size", 11)
    .attr("font-weight", 600)
    .attr("fill", (d) => providerColors[d] || "#333")
    .text((d) => d);

  // --- Category color strip ---
  const catStripG = svg.append("g")
    .attr("transform", `translate(${labelW}, ${headerH})`);

  let prevCatId = null;
  sortedTechniques.forEach((tech, i) => {
    const catColor = categoryColors[catLookup.get(tech.categoryId)] || "#ccc";
    catStripG.append("rect")
      .attr("x", 0)
      .attr("y", i * cellH)
      .attr("width", catColW)
      .attr("height", cellH)
      .attr("fill", catColor)
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.5);

    if (prevCatId !== null && prevCatId !== tech.categoryId) {
      catStripG.append("line")
        .attr("x1", -labelW)
        .attr("x2", catColW + providerOrder.length * cellW)
        .attr("y1", i * cellH)
        .attr("y2", i * cellH)
        .attr("stroke", "#999")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "2,2");
    }
    prevCatId = tech.categoryId;
  });

  // --- Technique labels ---
  const labelG = svg.append("g")
    .attr("transform", `translate(0, ${headerH})`);

  labelG.selectAll("text")
    .data(sortedTechniques)
    .join("text")
    .attr("x", labelW - 6)
    .attr("y", (_, i) => i * cellH + cellH / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", "end")
    .attr("font-size", 11)
    .attr("fill", "#333")
    .text((d) => d.name.length > 38 ? d.name.slice(0, 36) + "\u2026" : d.name);

  // --- Heatmap cells ---
  const cellG = svg.append("g")
    .attr("transform", `translate(${labelW + catColW}, ${headerH})`);

  sortedTechniques.forEach((tech, row) => {
    providerOrder.forEach((prov, col) => {
      const val = matrix[row][col];
      const g = cellG.append("g")
        .attr("transform", `translate(${col * cellW}, ${row * cellH})`);

      g.append("rect")
        .attr("width", cellW)
        .attr("height", cellH)
        .attr("fill", colorScale[val])
        .attr("stroke", "#fff")
        .attr("stroke-width", 1)
        .style("cursor", val > 0 ? "pointer" : "default")
        .on("mouseenter", function (event) {
          if (isPinned) return; // suppress hovers while pinned
          if (val === 0) return;
          d3.select(this).attr("stroke", "#333").attr("stroke-width", 2);
          hoverCell = d3.select(this);

          const techMap = providerTechniques.get(prov);
          const records = techMap ? techMap.get(tech.name) || [] : [];
          showPanel(event, prov, tech, records, false);
        })
        .on("mouseleave", function () {
          if (isPinned) return;
          if (hoverCell && hoverCell.node() === this) {
            d3.select(this).attr("stroke", "#fff").attr("stroke-width", 1);
            hoverCell = null;
          }
          removePanel();
        })
        .on("click", function (event) {
          if (val === 0) return;
          event.stopPropagation();

          // If already pinned on this cell, dismiss
          if (isPinned && selectedCell && selectedCell.node() === this) {
            dismissAll();
            return;
          }

          // Clear previous pin state
          if (selectedCell) {
            selectedCell.attr("stroke", "#fff").attr("stroke-width", 1);
          }

          const techMap = providerTechniques.get(prov);
          const records = techMap ? techMap.get(tech.name) || [] : [];

          selectedCell = d3.select(this);
          selectedCell.attr("stroke", "#333").attr("stroke-width", 2);
          isPinned = true;
          showPanel(event, prov, tech, records, true);
        });

      if (val > 0) {
        g.append("text")
          .attr("x", cellW / 2)
          .attr("y", cellH / 2)
          .attr("dy", "0.35em")
          .attr("text-anchor", "middle")
          .attr("font-size", 9)
          .attr("fill", val === 1 ? "#fff" : "#333")
          .attr("pointer-events", "none")
          .text(ratingText[val]);
      }
    });
  });

  // --- Legend ---
  const legendG = svg.append("g")
    .attr("transform", `translate(${labelW + catColW}, ${headerH + sortedTechniques.length * cellH + 16})`);

  const legendItems = [
    { label: "No detection", color: colorScale[0] },
    { label: "Low", color: colorScale[1] },
    { label: "Medium", color: colorScale[2] },
    { label: "High", color: colorScale[3] }
  ];

  legendItems.forEach((item, i) => {
    const x = i * 110;
    legendG.append("rect")
      .attr("x", x)
      .attr("y", 0)
      .attr("width", 14)
      .attr("height", 14)
      .attr("fill", item.color)
      .attr("stroke", "#ccc")
      .attr("stroke-width", 0.5)
      .attr("rx", 2);
    legendG.append("text")
      .attr("x", x + 18)
      .attr("y", 7)
      .attr("dy", "0.35em")
      .attr("font-size", 11)
      .attr("fill", "#666")
      .text(item.label);
  });

  // --- Container ---
  const container = d3.create("div")
    .style("position", "relative")
    .style("overflow-x", "auto");

  container.node().appendChild(svg.node());

  return container.node();
}
