function _1(md) {
  return (
    md`# LLM Safety Mechanisms Explorer

This project supports holistic analysis of Large Language Model safety mechanisms, using data from my [LLM Safety Mechanisms GitHub repository](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms). Please raise any issues/suggestions via GitHub.

## Why do we need it?
_Understanding which safety mechanisms are implemented across large language models currently requires piecing together information from scattered documentation, each using different terminology and varying levels of detail. This work will provides a structured, queryable view of safety technique coverage across major frontier models - not as a score or ranking, but as a coverage profile that assists researchers, practitioners, and policymakers make informed assessments based on their specific context._

## Current (& Planned) Activity
This project is under active development. Current priorities include:
* **Improving detection accuracy** — [_Underway_] Manual ground-truth labelling against source documentation is underway to empirically tune the semantic matching thresholds. The goal is reliable, automated linking of models to techniques with transparent confidence levels. Current efforts are to develop a manual tagging tool which works with the mapping data, while preserving linkages between techniques and extracted passages from source documentation.
* **Expanding evidence coverage** — [_Planned_] Identifying missing and additional documentation from additional providers and third-party analysis. I'm very conscious that the collection is incomplete, but first steps are to refine the end-to-end workflow to get it working well.
* **Reported Safety Incidents** - [_Planned_] Reported safety incidents linked to models, with a mechanism for public users to submit incidents as well as performing automated scans for them. Recent issues with Grok stand out as an excellent example, as do situations like ChatGPT encouraging risky/dangerous behaviours.
`
  )
}

function _2(md) {
  return (
    md`## Safety Mechanisms by Category
This chart provides a visual overview of the safety mechanisms documented in this project. I'm planning to extend this so that it drills down into collections by provider/model for each category/technique.`
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


function _4(filteredData, data, md) {
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
` : '**No data matches current filters**'}
\``
  )
}

function _5(md) {
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


function _10(md) {
  return (
    md`## Provider-Technique Relationships
* Pinch/scroll to zoom.
* Default state is multi (click and drag to multi-select objects)
* Click Multi button to switch to Drag mode if you want to drag the canvas
* Multi-select on touch screens requires touching in two locations, effectively creating a rectangular selection area over the objects
* Legends are draggable so you can place them anywhere you want
* Legend members are clickable to hide/show in the chart. Simplifies without needing to scroll down to filter
* Click Force button to let the network distribute based on linkages. I'm still refining the weights on this to make it *actually* useful :-) `
  )
}

function _unifiedChart(providerColors, filteredData, categoryColors, d3) {
  const width = 900;
  const height = 800;

  // Layout configuration
  const layout = {
    techniqueSpacingY: 20,
    techniqueOffsetX: 0,
    categoryPadding: 15,
    categoryRadius: 8,
    categoryMinWidth: 120,
    providerSpacing: 30,
    nodeMargins: {
      left: 80,
      right: 80,
      top: 80,
      bottom: 120
    }
  };

  // State management
  let interactionMode = "MULTI";
  let disabledProviders = new Set();
  let disabledCategories = new Set();

  // --- NEW: Robust Color Lookup Helper ---
  // Fixes the issue where 'amazon' (data) doesn't match 'Amazon' (color scheme)
  function getProviderColor(providerName) {
    if (!providerName) return "#999";

    // 1. Try exact match
    if (providerColors[providerName]) return providerColors[providerName];

    // 2. Try looking for a case-insensitive match in the keys
    const keys = Object.keys(providerColors);
    const match = keys.find(
      (k) => k.toLowerCase() === providerName.toLowerCase()
    );

    return match ? providerColors[match] : "#999";
  }

  // Build data structure from filteredData
  function buildDataStructure() {
    const data = {};

    const selectedProviders = [...new Set(filteredData.map((d) => d.provider))];
    const selectedCategories = [
      ...new Set(filteredData.map((d) => d.category))
    ];

    filteredData.forEach((evidence) => {
      const provider = evidence.provider;
      const category = evidence.category;
      const technique = evidence.technique;

      if (!data[provider]) data[provider] = {};
      if (!data[provider][category]) data[provider][category] = {};
      if (!data[provider][category][technique]) {
        data[provider][category][technique] = [];
      }

      const compatEvidence = {
        ...evidence,
        evidenceText: Array.isArray(evidence.evidence)
          ? evidence.evidence[0]
          : evidence.evidence
      };

      data[provider][category][technique].push(compatEvidence);
    });

    Object.keys(data).forEach((provider) => {
      Object.keys(data[provider]).forEach((category) => {
        Object.keys(data[provider][category]).forEach((technique) => {
          const evidenceList = data[provider][category][technique];
          if (evidenceList.length > 0) {
            data[provider][category][technique] = evidenceList[0];
          }
        });
      });
    });

    return { data, selectedProviders, selectedCategories };
  }

  let { data, selectedProviders, selectedCategories } = buildDataStructure();

  // Helper functions for color manipulation
  function darkenColor(hex, amount = 40) {
    const num = parseInt(hex.slice(1), 16);
    const r = Math.max(0, (num >> 16) - amount);
    const g = Math.max(0, ((num >> 8) & 0x00ff) - amount);
    const b = Math.max(0, (num & 0x0000ff) - amount);
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
  }

  function lightenColor(hex, amount = 40) {
    const num = parseInt(hex.slice(1), 16);
    const r = Math.min(255, (num >> 16) + amount);
    const g = Math.min(255, ((num >> 8) & 0x00ff) + amount);
    const b = Math.min(255, (num & 0x0000ff) + amount);
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
  }

  function getCategoryPosition(index, total) {
    const leftCategories = 4;
    const isLeft = index < leftCategories;

    const categoryData = selectedCategories.map((cat) => {
      const techniques = [];
      selectedProviders.forEach((provider) => {
        if (data[provider]?.[cat]) {
          Object.keys(data[provider][cat]).forEach((technique) => {
            if (!techniques.find((t) => t.name === technique)) {
              techniques.push({ name: technique });
            }
          });
        }
      });
      return {
        name: cat,
        techniqueCount: techniques.length,
        height: 35 + 20 + techniques.length * layout.techniqueSpacingY + 40
      };
    });

    if (isLeft) {
      let yPos = -height / 2 + layout.nodeMargins.top + 20;
      for (let i = 0; i < index; i++) {
        yPos += categoryData[i].height;
      }
      return {
        x: -width / 2 + layout.nodeMargins.left + layout.categoryMinWidth / 2,
        y: yPos
      };
    } else {
      let yPos = -height / 2 + layout.nodeMargins.top + 20;
      for (let i = 4; i < index; i++) {
        yPos += categoryData[i].height;
      }
      return {
        x: width / 2 - layout.nodeMargins.right - layout.categoryMinWidth / 2,
        y: yPos
      };
    }
  }

  function measureText(text, fontSize = "14px", fontWeight = "bold") {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    context.font = `${fontWeight} ${fontSize} sans-serif`;
    return context.measureText(text).width;
  }

  // Build nodes and links
  function buildGraph() {
    const nodes = [];
    const links = [];
    const nodeById = new Map();

    const providerStartY =
      -(selectedProviders.length * layout.providerSpacing) / 2;
    selectedProviders.forEach((provider, i) => {
      const providerNode = {
        id: `provider-${provider}`,
        name: provider,
        type: "provider",
        // UPDATED: Use helper
        color: getProviderColor(provider),
        x: 0,
        y: providerStartY + i * layout.providerSpacing,
        fx: 0,
        fy: providerStartY + i * layout.providerSpacing
      };
      nodes.push(providerNode);
      nodeById.set(providerNode.id, providerNode);
    });

    selectedCategories.forEach((category, catIndex) => {
      const pos = getCategoryPosition(catIndex, selectedCategories.length);
      const textWidth = measureText(category);
      const nodeWidth = Math.max(
        textWidth + layout.categoryPadding * 2,
        layout.categoryMinWidth
      );

      const categoryNode = {
        id: `category-${category}`,
        name: category,
        type: "category",
        color: categoryColors[category] || "#666",
        x: pos.x,
        y: pos.y,
        fx: pos.x,
        fy: pos.y,
        width: nodeWidth,
        height: 35
      };
      nodes.push(categoryNode);
      nodeById.set(categoryNode.id, categoryNode);

      const categoryColor = categoryColors[category] || "#666";
      const techniqueColor = lightenColor(categoryColor, 40);
      const techniques = [];

      selectedProviders.forEach((provider) => {
        if (data[provider]?.[category]) {
          Object.keys(data[provider][category]).forEach((technique) => {
            if (!techniques.find((t) => t.name === technique)) {
              techniques.push({ name: technique });
            }
          });
        }
      });

      techniques.forEach((technique, i) => {
        const techId = `technique-${category}-${technique.name}`;
        const staggerOffset =
          i % 2 === 0 ? -layout.techniqueOffsetX : layout.techniqueOffsetX;

        const node = {
          id: techId,
          name: technique.name,
          type: "technique",
          category: category,
          color: techniqueColor,
          x: categoryNode.x + staggerOffset,
          y:
            categoryNode.y +
            categoryNode.height / 2 +
            20 +
            i * layout.techniqueSpacingY,
          fx: categoryNode.x + staggerOffset,
          fy:
            categoryNode.y +
            categoryNode.height / 2 +
            20 +
            i * layout.techniqueSpacingY
        };
        nodes.push(node);
        nodeById.set(techId, node);

        links.push({
          source: `category-${category}`,
          target: techId,
          type: "category-technique",
          color: darkenColor(categoryColor, 40)
        });

        selectedProviders.forEach((provider) => {
          if (data[provider]?.[category]?.[technique.name]) {
            links.push({
              source: `provider-${provider}`,
              target: techId,
              type: "provider-technique",
              // UPDATED: Use helper
              color: d3
                .color(getProviderColor(provider))
                .darker(0.4)
                .toString(),
              data: data[provider][category][technique.name]
            });
          }
        });
      });
    });

    return { nodes, links, nodeById };
  }

  let { nodes, links, nodeById } = buildGraph();

  // Create SVG
  const svg = d3
    .create("svg")
    .attr("viewBox", [0, 0, width, height])
    .style("font", "12px sans-serif")
    .style("user-select", "none");

  // Styles (unchanged)
  svg.append("style").text(`
    .link-tooltip {
      position: absolute;
      text-align: left;
      padding: 10px;
      font: 12px sans-serif;
      background: rgba(0, 0, 0, 0.95);
      color: white;
      border-radius: 4px;
      pointer-events: none;
      max-width: 400px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
      border: 1px solid #333;
    }
    .link-tooltip a {
      color: #64b5f6;
      text-decoration: underline;
      pointer-events: auto;
    }
    .node-label {
      fill: black;
      font-size: 12px;
      pointer-events: none;
      user-select: none;
    }
    .category-label {
      fill: white;
      font-size: 14px;
      font-weight: bold;
      pointer-events: none;
      user-select: none;
    }
    .label-bg {
      fill: white;
      fill-opacity: 0.6;
      rx: 3;
      ry: 3;
    }
    .control-button {
      fill: #f0f0f0;
      stroke: #333;
      cursor: pointer;
    }
    .control-button:hover {
      fill: #e0e0e0;
    }
    .control-text {
      fill: #333;
      font-size: 14px;
      font-weight: bold;
      text-anchor: middle;
      pointer-events: none;
      user-select: none;
    }
    .legend-container {
      fill: #e0e0e0;
      fill-opacity: 0.6;
      stroke: #999;
      stroke-width: 1;
      rx: 8;
      ry: 8;
    }
    .legend-item {
      cursor: pointer;
    }
    .legend-item.disabled {
      opacity: 0.3;
    }
    .legend-title {
      font-weight: bold;
      font-size: 14px;
      user-select: none;
      text-anchor: middle;
    }
  `);

  const g = svg.append("g").attr("class", "main-container");

  const zoom = d3
    .zoom()
    .scaleExtent([0.3, 3])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  const selectionRect = g
    .append("rect")
    .attr("class", "selection")
    .attr("fill", "rgba(100, 100, 255, 0.1)")
    .attr("stroke", "rgba(100, 100, 255, 0.5)")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "3,3")
    .style("display", "none");

  function rebuildChart() {
    const newDataStructure = buildDataStructure();
    data = newDataStructure.data;
    selectedProviders = newDataStructure.selectedProviders;
    selectedCategories = newDataStructure.selectedCategories;

    const newGraph = buildGraph();
    nodes = newGraph.nodes;
    links = newGraph.links;
    nodeById = newGraph.nodeById;

    linkContainer.selectAll("*").remove();
    nodeContainer.selectAll("*").remove();
    providerLegend.selectAll("*").remove();
    categoryLegend.selectAll("*").remove();

    buildVisualization();
  }

  function storeReferences(link, techniqueNodes, categoryNodes, providerNodes) {
    window.currentLink = link;
    window.currentTechniqueNodes = techniqueNodes;
    window.currentCategoryNodes = categoryNodes;
    window.currentProviderNodes = providerNodes;
  }

  function buildVisualization() {
    const link = linkContainer
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => d.color)
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => (d.type === "category-technique" ? 2 : 1))
      .style("cursor", "pointer");

    const techniqueNodes = nodeContainer
      .selectAll(".technique-node")
      .data(nodes.filter((n) => n.type === "technique"))
      .join("g")
      .attr("class", "technique-node node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`);

    const categoryNodes = nodeContainer
      .selectAll(".category-node")
      .data(nodes.filter((n) => n.type === "category"))
      .join("g")
      .attr("class", "category-node node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`);

    const providerNodes = nodeContainer
      .selectAll(".provider-node")
      .data(nodes.filter((n) => n.type === "provider"))
      .join("g")
      .attr("class", "provider-node node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`);

    storeReferences(link, techniqueNodes, categoryNodes, providerNodes);

    providerNodes
      .append("circle")
      .attr("r", 10)
      .attr("fill", (d) => d.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    categoryNodes.each(function (d) {
      const group = d3.select(this);
      group
        .append("rect")
        .attr("width", d.width)
        .attr("height", d.height)
        .attr("x", -d.width / 2)
        .attr("y", -d.height / 2)
        .attr("rx", layout.categoryRadius)
        .attr("ry", layout.categoryRadius)
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

    techniqueNodes
      .append("path")
      .attr("d", d3.symbol().type(d3.symbolTriangle).size(150))
      .attr("fill", (d) => categoryColors[d.category] || "#666")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    function addLabel(selection) {
      const labelGroup = selection.append("g").attr("class", "label-group");
      const text = labelGroup
        .append("text")
        .attr("class", "node-label")
        .attr("x", 15)
        .attr("y", 5)
        .text((d) => d.name);

      selection.each(function (d) {
        const textNode = d3.select(this).select("text.node-label").node();
        if (textNode) {
          const bbox = textNode.getBBox();
          d3.select(this)
            .select(".label-group")
            .insert("rect", "text")
            .attr("class", "label-bg")
            .attr("x", bbox.x - 2)
            .attr("y", bbox.y - 2)
            .attr("width", bbox.width + 4)
            .attr("height", bbox.height + 4);
        }
      });
    }

    addLabel(providerNodes);
    addLabel(techniqueNodes);

    setupNodeInteraction(providerNodes);
    setupNodeInteraction(categoryNodes);
    setupNodeInteraction(techniqueNodes);
    setupLinkInteraction(link);
    buildLegends();
    updateLinks();
    updateVisualization();
  }

  const linkContainer = g.append("g").attr("class", "links");
  const nodeContainer = g.append("g").attr("class", "nodes");
  const controls = svg.append("g").attr("transform", `translate(20, 20)`);

  const modeButton = controls.append("g").style("cursor", "pointer");
  modeButton
    .append("rect")
    .attr("class", "control-button")
    .attr("width", 80)
    .attr("height", 30)
    .attr("rx", 5);

  const modeText = modeButton
    .append("text")
    .attr("class", "control-text")
    .attr("x", 40)
    .attr("y", 20)
    .text("MULTI");

  modeButton.on("click", () => {
    interactionMode = interactionMode === "DRAG" ? "MULTI" : "DRAG";
    modeText.text(interactionMode);
    if (interactionMode === "DRAG") {
      svg.style("cursor", "grab");
    } else {
      svg.style("cursor", "crosshair");
    }
  });

  let forceSimulation = null;
  let forceActive = false;
  const forceButton = controls
    .append("g")
    .attr("transform", "translate(90, 0)")
    .style("cursor", "pointer");
  forceButton
    .append("rect")
    .attr("class", "control-button")
    .attr("width", 80)
    .attr("height", 30)
    .attr("rx", 5);
  const forceButtonText = forceButton
    .append("text")
    .attr("class", "control-text")
    .attr("x", 40)
    .attr("y", 20)
    .text("FORCE");

  forceButton.on("click", () => {
    forceActive = !forceActive;
    forceButton
      .select("rect")
      .style("fill", forceActive ? "#d0d0d0" : "#f0f0f0");
    if (forceActive) {
      nodes.forEach((node) => {
        if (node.type === "provider" || node.type === "technique") {
          node.fx = null;
          node.fy = null;
        }
      });
      forceSimulation = d3
        .forceSimulation(nodes)
        .force(
          "link",
          d3
            .forceLink(links)
            .id((d) => d.id)
            .distance((d) => (d.type === "provider-technique" ? 120 : 30))
            .strength((d) => (d.type === "provider-technique" ? 0.3 : 0.7))
        )
        .force(
          "charge",
          d3.forceManyBody().strength((d) => {
            if (d.type === "provider") return -80;
            if (d.type === "technique") return -30;
            return 0;
          })
        )
        .force(
          "collide",
          d3.forceCollide().radius((d) => {
            if (d.type === "provider") return 25;
            if (d.type === "technique") return 12;
            return 10;
          })
        )
        .alphaDecay(0.02)
        .velocityDecay(0.4)
        .on("tick", () => {
          if (window.currentProviderNodes)
            window.currentProviderNodes
              .filter((d) => d.type === "provider")
              .attr("transform", (d) => `translate(${d.x},${d.y})`);
          if (window.currentTechniqueNodes)
            window.currentTechniqueNodes
              .filter((d) => d.type === "technique")
              .attr("transform", (d) => `translate(${d.x},${d.y})`);
          if (window.currentLink) {
            window.currentLink
              .attr("x1", (d) => {
                const s =
                  typeof d.source === "object"
                    ? d.source
                    : nodeById.get(d.source);
                return s ? s.x : 0;
              })
              .attr("y1", (d) => {
                const s =
                  typeof d.source === "object"
                    ? d.source
                    : nodeById.get(d.source);
                return s ? s.y : 0;
              })
              .attr("x2", (d) => {
                const t =
                  typeof d.target === "object"
                    ? d.target
                    : nodeById.get(d.target);
                return t ? t.x : 0;
              })
              .attr("y2", (d) => {
                const t =
                  typeof d.target === "object"
                    ? d.target
                    : nodeById.get(d.target);
                return t ? t.y : 0;
              });
          }
        });
      forceSimulation.alpha(1).restart();
    } else {
      if (forceSimulation) {
        forceSimulation.stop();
        forceSimulation = null;
        nodes.forEach((node) => {
          if (node.type === "provider" || node.type === "technique") {
            node.fx = node.x;
            node.fy = node.y;
          }
        });
      }
    }
  });

  const resetButton = controls
    .append("g")
    .attr("transform", "translate(180, 0)")
    .style("cursor", "pointer");
  resetButton
    .append("rect")
    .attr("class", "control-button")
    .attr("width", 80)
    .attr("height", 30)
    .attr("rx", 5);
  resetButton
    .append("text")
    .attr("class", "control-text")
    .attr("x", 40)
    .attr("y", 20)
    .text("RESET");

  resetButton.on("click", () => {
    if (forceSimulation) {
      forceSimulation.stop();
      forceSimulation = null;
      forceActive = false;
      forceButton.select("rect").style("fill", "#f0f0f0");
    }
    svg.call(
      zoom.transform,
      d3.zoomIdentity.scale(0.8).translate(width * 0.5, height * 0.5)
    );
    disabledProviders.clear();
    disabledCategories.clear();
    selectedNodes.clear();
    rebuildChart();
  });

  const providerLegend = g
    .append("g")
    .attr("class", "provider-legend")
    .attr("transform", "translate(0, 350)");
  const categoryLegend = g
    .append("g")
    .attr("class", "category-legend")
    .attr("transform", "translate(250, 270)");

  function buildLegends() {
    providerLegend.attr("transform", "translate(0, 200)");
    categoryLegend.attr("transform", "translate(180, 320)");

    const providerLegendBg = providerLegend
      .append("rect")
      .attr("class", "legend-container")
      .attr("width", 160)
      .attr("height", 35 + Math.min(selectedProviders.length) * 20)
      .attr("x", -10)
      .attr("y", -10);
    providerLegend
      .append("text")
      .attr("class", "legend-title")
      .attr("x", 70)
      .attr("y", 10)
      .text("Providers");

    const providerItems = providerLegend
      .selectAll(".provider-legend-item")
      .data(selectedProviders)
      .join("g")
      .attr("class", "legend-item provider-legend-item")
      .attr("transform", (d, i) => `translate(0, ${30 + i * 20})`);

    // UPDATED: Use helper
    providerItems
      .append("circle")
      .attr("r", 6)
      .attr("fill", (d) => getProviderColor(d));
    providerItems
      .append("text")
      .attr("x", 12)
      .attr("y", 4)
      .attr("font-size", "12px")
      .text((d) => d);

    providerItems.on("click", function (event, provider) {
      if (disabledProviders.has(provider)) disabledProviders.delete(provider);
      else disabledProviders.add(provider);
      updateVisualization();
    });

    const categoryLegendBg = categoryLegend
      .append("rect")
      .attr("class", "legend-container")
      .attr("width", 160)
      .attr("height", 35 + selectedCategories.length * 20)
      .attr("x", -10)
      .attr("y", -10);
    categoryLegend
      .append("text")
      .attr("class", "legend-title")
      .attr("x", 70)
      .attr("y", 10)
      .text("Categories");

    const categoryItems = categoryLegend
      .selectAll(".category-legend-item")
      .data(selectedCategories)
      .join("g")
      .attr("class", "legend-item category-legend-item")
      .attr("transform", (d, i) => `translate(0, ${30 + i * 20})`);
    categoryItems
      .append("rect")
      .attr("width", 12)
      .attr("height", 12)
      .attr("x", -6)
      .attr("y", -6)
      .attr("fill", (d) => categoryColors[d] || "#666");
    categoryItems
      .append("text")
      .attr("x", 12)
      .attr("y", 4)
      .attr("font-size", "12px")
      .text((d) => d);
    categoryItems.on("click", function (event, category) {
      if (disabledCategories.has(category)) disabledCategories.delete(category);
      else disabledCategories.add(category);
      updateVisualization();
    });

    makeDraggable(providerLegend.style("cursor", "move"));
    makeDraggable(categoryLegend.style("cursor", "move"));
  }

  function makeDraggable(selection) {
    selection.call(
      d3.drag().on("drag", function (event) {
        const currentTransform = d3.select(this).attr("transform");
        const match = currentTransform.match(/translate\(([^,]+),([^)]+)\)/);
        if (match) {
          const newX = parseFloat(match[1]) + event.dx;
          const newY = parseFloat(match[2]) + event.dy;
          d3.select(this).attr("transform", `translate(${newX},${newY})`);
        }
      })
    );
  }

  const selectedNodes = new Set();
  let selectedLink = null;
  let persistentTooltip = null;
  let selectionStart = null;
  let isSelecting = false;
  let preventClear = false;

  svg.on("pointerdown", function (event) {
    if (interactionMode === "MULTI" && event.target === this) {
      isSelecting = true;
      preventClear = true;
      selectionStart = d3.pointer(event, g.node());
      selectionRect
        .attr("x", selectionStart[0])
        .attr("y", selectionStart[1])
        .attr("width", 0)
        .attr("height", 0)
        .style("display", "block");
      event.preventDefault();
      event.stopPropagation();
    }
  });

  svg.on("pointermove", function (event) {
    if (isSelecting && selectionStart && interactionMode === "MULTI") {
      const current = d3.pointer(event, g.node());
      const x = Math.min(selectionStart[0], current[0]);
      const y = Math.min(selectionStart[1], current[1]);
      const width = Math.abs(current[0] - selectionStart[0]);
      const height = Math.abs(current[1] - selectionStart[1]);
      selectionRect
        .attr("x", x)
        .attr("y", y)
        .attr("width", width)
        .attr("height", height);
      const tempSelection = new Set();
      nodes.forEach((node) => {
        if (
          node.x >= x &&
          node.x <= x + width &&
          node.y >= y &&
          node.y <= y + height &&
          !disabledProviders.has(node.name) &&
          !disabledCategories.has(node.name) &&
          !disabledCategories.has(node.category)
        ) {
          tempSelection.add(node.id);
        }
      });
      updateSelectionVisual(tempSelection);
    }
  });

  svg.on("pointerup", function (event) {
    if (isSelecting && selectionStart) {
      const current = d3.pointer(event, g.node());
      const x = Math.min(selectionStart[0], current[0]);
      const y = Math.min(selectionStart[1], current[1]);
      const width = Math.abs(current[0] - selectionStart[0]);
      const height = Math.abs(current[1] - selectionStart[1]);
      if (!event.shiftKey && !event.ctrlKey && !event.metaKey)
        selectedNodes.clear();
      nodes.forEach((node) => {
        if (
          node.x >= x &&
          node.x <= x + width &&
          node.y >= y &&
          node.y <= y + height &&
          !disabledProviders.has(node.name) &&
          !disabledCategories.has(node.name) &&
          !disabledCategories.has(node.category)
        ) {
          selectedNodes.add(node.id);
        }
      });
      selectionStart = null;
      isSelecting = false;
      selectionRect.style("display", "none");
      updateSelection();
      setTimeout(() => {
        preventClear = false;
      }, 100);
    }
  });

  function setupNodeInteraction(selection) {
    selection
      .style("cursor", "pointer")
      .on("click", function (event, d) {
        event.stopPropagation();
        preventClear = true;
        if (
          disabledProviders.has(d.name) ||
          disabledCategories.has(d.name) ||
          disabledCategories.has(d.category)
        )
          return;
        if (event.ctrlKey || event.shiftKey || event.metaKey) {
          if (selectedNodes.has(d.id)) selectedNodes.delete(d.id);
          else selectedNodes.add(d.id);
        } else {
          selectedNodes.clear();
          selectedNodes.add(d.id);
        }
        updateSelection();
        setTimeout(() => {
          preventClear = false;
        }, 100);
      })
      .call(
        d3
          .drag()
          .on("start", function (event, d) {
            if (
              interactionMode === "MULTI" &&
              !disabledProviders.has(d.name) &&
              !disabledCategories.has(d.name) &&
              !disabledCategories.has(d.category)
            ) {
              preventClear = true;
              d.dragStartX = event.x - d.x;
              d.dragStartY = event.y - d.y;
              if (selectedNodes.has(d.id))
                nodes.forEach((node) => {
                  if (selectedNodes.has(node.id)) {
                    node.dragStartX = event.x - node.x;
                    node.dragStartY = event.y - node.y;
                  }
                });
            }
          })
          .on("drag", function (event, d) {
            if (
              interactionMode === "MULTI" &&
              !disabledProviders.has(d.name) &&
              !disabledCategories.has(d.name) &&
              !disabledCategories.has(d.category)
            ) {
              if (forceActive && forceSimulation && d.type === "provider") {
                d.x = event.x;
                d.y = event.y;
                d.fx = event.x;
                d.fy = event.y;
                d3.select(this).attr("transform", `translate(${d.x},${d.y})`);
                updateLinks();
                forceSimulation.alpha(0.1).restart();
              } else {
                if (selectedNodes.has(d.id)) {
                  nodes.forEach((node) => {
                    if (selectedNodes.has(node.id)) {
                      node.x = event.x - node.dragStartX;
                      node.y = event.y - node.dragStartY;
                      node.fx = node.x;
                      node.fy = node.y;
                    }
                  });
                  [
                    window.currentTechniqueNodes,
                    window.currentCategoryNodes,
                    window.currentProviderNodes
                  ].forEach((nodeGroup) => {
                    if (nodeGroup)
                      nodeGroup
                        .filter((n) => selectedNodes.has(n.id))
                        .attr("transform", (n) => `translate(${n.x},${n.y})`);
                  });
                } else {
                  d.x = event.x;
                  d.y = event.y;
                  d.fx = d.x;
                  d.fy = d.y;
                  d3.select(this).attr("transform", `translate(${d.x},${d.y})`);
                }
                updateLinks();
              }
            }
          })
          .on("end", function (event, d) {
            if (forceActive && forceSimulation && d.type === "provider") {
              d.fx = null;
              d.fy = null;
              forceSimulation.alpha(0.3).restart();
            }
            setTimeout(() => {
              preventClear = false;
            }, 100);
          })
      );
  }

  function setupLinkInteraction(link) {
    link
      .on("pointerover", function (event, d) {
        if (!persistentTooltip && !isDisabledLink(d)) {
          d3.select(this).attr("stroke-width", (d) =>
            d.type === "category-technique" ? 4 : 3
          );
          showLinkTooltip(event, d);
        }
      })
      .on("pointerout", function (event, d) {
        if (!persistentTooltip && !isDisabledLink(d)) {
          d3.select(this).attr("stroke-width", (d) =>
            d.type === "category-technique" ? 2 : 1
          );
          hideLinkTooltip();
        }
      })
      .on("click", function (event, d) {
        if (isDisabledLink(d)) return;
        event.stopPropagation();
        preventClear = true;
        if (persistentTooltip && selectedLink) {
          selectedLink.attr("stroke-width", (d) =>
            d.type === "category-technique" ? 2 : 1
          );
          persistentTooltip.remove();
          persistentTooltip = null;
          selectedLink = null;
        }
        selectedLink = d3.select(this);
        selectedLink.attr("stroke-width", (d) =>
          d.type === "category-technique" ? 4 : 3
        );
        persistentTooltip = showLinkTooltip(event, d, true);
        setTimeout(() => {
          preventClear = false;
        }, 100);
      });
  }

  function isDisabledLink(d) {
    const source =
      typeof d.source === "string" ? nodeById.get(d.source) : d.source;
    const target =
      typeof d.target === "string" ? nodeById.get(d.target) : d.target;
    return (
      disabledProviders.has(source.name) ||
      disabledCategories.has(source.name) ||
      disabledCategories.has(target.name) ||
      disabledCategories.has(target.category)
    );
  }

  function updateSelectionVisual(tempSelection) {
    [
      window.currentProviderNodes,
      window.currentCategoryNodes,
      window.currentTechniqueNodes
    ].forEach((nodeGroup) => {
      if (nodeGroup)
        nodeGroup
          .select("circle, rect, path")
          .attr("stroke", (d) =>
            tempSelection.has(d.id) || selectedNodes.has(d.id)
              ? "#ff7f0e"
              : "#fff"
          )
          .attr("stroke-width", (d) =>
            tempSelection.has(d.id) || selectedNodes.has(d.id) ? 3 : 2
          );
    });
  }

  function updateSelection() {
    [
      window.currentProviderNodes,
      window.currentCategoryNodes,
      window.currentTechniqueNodes
    ].forEach((nodeGroup) => {
      if (nodeGroup) {
        nodeGroup.style("opacity", function (d) {
          if (
            disabledProviders.has(d.name) ||
            disabledCategories.has(d.name) ||
            disabledCategories.has(d.category)
          )
            return 0.1;
          return selectedNodes.size === 0 || selectedNodes.has(d.id) ? 1 : 0.3;
        });
        nodeGroup
          .select("circle, rect, path")
          .attr("stroke", (d) => (selectedNodes.has(d.id) ? "#ff7f0e" : "#fff"))
          .attr("stroke-width", (d) => (selectedNodes.has(d.id) ? 3 : 2));
      }
    });
    if (window.currentLink) {
      window.currentLink.style("opacity", function (d) {
        if (isDisabledLink(d)) return 0.1;
        if (selectedNodes.size === 0) return 0.6;
        const s = typeof d.source === "string" ? d.source : d.source.id;
        const t = typeof d.target === "string" ? d.target : d.target.id;
        return selectedNodes.has(s) || selectedNodes.has(t) ? 0.6 : 0.1;
      });
    }
  }

  function updateLinks() {
    if (window.currentLink) {
      window.currentLink
        .attr("x1", (d) => {
          try {
            const s =
              typeof d.source === "string" ? nodeById.get(d.source) : d.source;
            return s?.x || 0;
          } catch (e) {
            return 0;
          }
        })
        .attr("y1", (d) => {
          try {
            const s =
              typeof d.source === "string" ? nodeById.get(d.source) : d.source;
            return s?.y || 0;
          } catch (e) {
            return 0;
          }
        })
        .attr("x2", (d) => {
          try {
            const t =
              typeof d.target === "string" ? nodeById.get(d.target) : d.target;
            return t?.x || 0;
          } catch (e) {
            return 0;
          }
        })
        .attr("y2", (d) => {
          try {
            const t =
              typeof d.target === "string" ? nodeById.get(d.target) : d.target;
            return t?.y || 0;
          } catch (e) {
            return 0;
          }
        });
    }
  }

  function updateVisualization() {
    const providerItems = providerLegend.selectAll(".provider-legend-item");
    const categoryItems = categoryLegend.selectAll(".category-legend-item");
    if (providerItems.size() > 0)
      providerItems.classed("disabled", (d) => disabledProviders.has(d));
    if (categoryItems.size() > 0)
      categoryItems.classed("disabled", (d) => disabledCategories.has(d));
    updateSelection();
  }

  function showLinkTooltip(event, d, persistent = false) {
    hideLinkTooltip();
    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "link-tooltip")
      .style("opacity", 0)
      .style("left", event.pageX + 10 + "px")
      .style("top", event.pageY - 28 + "px");
    let content = "";
    const source =
      typeof d.source === "string" ? nodeById.get(d.source) : d.source;
    const target =
      typeof d.target === "string" ? nodeById.get(d.target) : d.target;

    if (d.type === "provider-technique" && d.data) {
      const sourceHtml = d.data.source_uri
        ? `<a href="${d.data.source_uri
        }" target="_blank" style="color: #64b5f6;">${d.data.source || "View Source"
        }</a>`
        : d.data.source || "Unknown Source";
      const modelHtml = d.data.model || "N/A";
      const rawEvidence = d.data.evidenceText || "";
      const truncatedEvidence =
        rawEvidence.length > 250
          ? rawEvidence.substring(0, 249) + "..."
          : rawEvidence;
      const confidenceHtml = d.data.confidence || "Unknown";
      content = `<h4 style="margin: 0 0 8px 0; color: #ffa726; font-size: 14px;">${source.name} → ${target.name}</h4><p style="margin: 4px 0;"><strong>Source:</strong> ${sourceHtml}</p><p style="margin: 4px 0;"><strong>Model(s):</strong> ${modelHtml}</p><p style="margin: 6px 0 4px 0;"><strong>Evidence:</strong></p><div style="font-style: italic; color: #ddd; margin-bottom: 8px; line-height: 1.4;">"${truncatedEvidence}"</div><div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid #555;"><strong>Confidence:</strong> ${confidenceHtml}</div>`;
    } else {
      content = `<h4 style="margin: 0; color: #ffa726;">${source.name} → ${target.name}</h4>`;
    }
    tooltip.html(content);
    tooltip.transition().duration(200).style("opacity", 0.95);
    return persistent ? tooltip : null;
  }

  function hideLinkTooltip() {
    if (!persistentTooltip) d3.selectAll(".link-tooltip").remove();
  }

  svg.on("click", () => {
    if (!preventClear && !isSelecting) {
      selectedNodes.clear();
      updateSelection();
      if (persistentTooltip && selectedLink) {
        selectedLink.attr("stroke-width", (d) =>
          d.type === "category-technique" ? 2 : 1
        );
        persistentTooltip.remove();
        persistentTooltip = null;
        selectedLink = null;
      }
    }
  });

  svg.call(zoom);
  svg.call(
    zoom.transform,
    d3.zoomIdentity.scale(0.8).translate(width * 0.5, height * 0.5)
  );
  svg.style("cursor", "crosshair");
  buildVisualization();

  let lastDataSignature = JSON.stringify(filteredData?.map((d) => d.id).sort());
  const checkDataChanges = () => {
    try {
      if (!filteredData || !Array.isArray(filteredData)) return;
      const currentSignature = JSON.stringify(
        filteredData.map((d) => d.id).sort()
      );
      if (currentSignature !== lastDataSignature) {
        lastDataSignature = currentSignature;
        rebuildChart();
      }
    } catch (e) {
      console.warn("Data change detection error:", e);
    }
  };
  const dataChangeInterval = setInterval(checkDataChanges, 100);
  svg.node().addEventListener("DOMNodeRemoved", () => {
    clearInterval(dataChangeInterval);
  });

  return svg.node();
}


function _12(md) {
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

  const form = html`<div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 20px; font-family: sans-serif;">
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px;">
      
      <div>
        <h4 style="margin-top: 0; color: #333;">Providers</h4>
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
          ${uniqueProviders
      .map(
        (provider) =>
          `<label style="display: block; margin-bottom: 8px; cursor: pointer;">
              <input type="checkbox" name="providers" value="${provider.id}" style="margin-right: 8px;">
              <span style="font-size: 14px;">${provider.name}</span>
            </label>`
      )
      .join("")}
        </div>
        <div style="margin-top: 10px;">
          <button type="button" id="select-all-providers" style="font-size: 12px; padding: 4px 8px; margin-right: 5px;">Select All</button>
          <button type="button" id="clear-providers" style="font-size: 12px; padding: 4px 8px;">Clear All</button>
        </div>
      </div>
      
      <div>
        <h4 style="margin-top: 0; color: #333;">Categories & Techniques</h4>
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
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
                <div style="margin-bottom: 15px; border-left: 4px solid ${categoryColor}; padding-left: 10px;">
                  <label style="display: block; font-weight: bold; cursor: pointer; margin-bottom: 8px;">
                    <input type="checkbox" name="categories" value="${categoryName}" id="${categoryId}" style="margin-right: 8px;">
                    <span style="color: ${categoryColor}; font-size: 14px;">${categoryName}</span>
                    <span style="color: #666; font-size: 12px; font-weight: normal;"> (${techniques.length
            })</span>
                  </label>
                  <div style="margin-left: 20px;">
                    ${techniques
              .sort((a, b) => a.name.localeCompare(b.name))
              .map(
                (technique) =>
                  `<label style="display: block; margin-bottom: 4px; cursor: pointer;">
                        <input type="checkbox" name="techniques" value="${technique.name}" data-category="${categoryName}" style="margin-right: 8px;">
                        <span style="font-size: 13px; color: #555;">${technique.name}</span>
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
        <div style="margin-top: 10px;">
          <button type="button" id="select-all-categories" style="font-size: 12px; padding: 4px 8px; margin-right: 5px;">Select All Categories</button>
          <button type="button" id="clear-categories" style="font-size: 12px; padding: 4px 8px;">Clear All</button>
        </div>
      </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Minimum Confidence</label>
        <input name="rating" type="range" min="0" max="3" step="1" value="0" style="width: 100%;">
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888;">
             <span>All</span><span>Low</span><span>Med</span><span>High</span>
        </div>
        <span style="font-size: 12px; color: #666;">Current: <span id="rating-value">All</span></span>
      </div>
      
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Search</label>
        <input name="search" type="text" placeholder="Search evidence descriptions, summaries..." style="width: 100%; padding: 8px;">
      </div>
    </div>
    
    <div style="margin-top: 15px; text-align: center;">
      <button type="button" id="clear-all" style="padding: 10px 20px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Clear All Filters
      </button>
    </div>
    
    <div style="margin-top: 15px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 10px;">
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


function _table(Inputs, filteredData) {
  return (
    Inputs.table(
      filteredData.map((d) => {
        // Extract first evidence snippet if array, handle missing data
        const rawEvidence = Array.isArray(d.evidence) ? d.evidence[0] : d.evidence;
        const cleanEvidence = rawEvidence
          ? rawEvidence.toString()
          : "No evidence available";

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
          ? d.evidence.join(" | ")
          : d.evidence || "";
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


function _17(md) {
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

function _18(md) {
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
  const [evidence, techniques, categories, techniqueMap, models, providers] =
    await Promise.all([
      d3.json(`${BASE_URL}/evidence.json`).then((d) => d.sources || d),
      d3.json(`${BASE_URL}/techniques.json`),
      d3.json(`${BASE_URL}/categories.json`),
      d3.json(`${BASE_URL}/model_technique_map.json`),
      d3
        .json(`${BASE_URL}/models.json`)
        .then((d) => d.models || d)
        .catch(() => []),
      d3.json(`${BASE_URL}/providers.json`).catch(() => [])
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
    raw: { evidence, techniques, categories, techniqueMap, models, providers },
    enrichedModels,
    flatPairs,
    categories,
    techniques
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


function _networkConfig() {
  return (
    {
      width: 1000,
      height: 900,
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
        documents: "#ccc"
      }
    }
  )
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

function _savedLayout(localStorage, layoutStorageKey) {
  try {
    const saved = localStorage.getItem(layoutStorageKey);
    return saved ? JSON.parse(saved) : null;
  } catch (e) {
    return null;
  }
}


function _31(htl) {
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
  main.variable(observer("sunburstChart")).define("sunburstChart", ["data", "filteredData", "d3", "categoryColors"], _sunburstChart);
  main.variable(observer()).define(["filteredData", "data", "md"], _4);
  main.variable(observer()).define(["md"], _5);
  main.variable(observer("networkViz")).define("networkViz", ["positionedGraph", "validatedLayout", "networkConfig", "d3", "localStorage", "layoutStorageKey", "confirm", "location", "autoLayout", "providerColors"], _networkViz);
  main.variable(observer("autoLayout")).define("autoLayout", ["networkGraph", "networkConfig", "d3"], _autoLayout);
  main.variable(observer("validatedLayout")).define("validatedLayout", ["networkGraph", "localStorage", "layoutStorageKey", "defaultLayout"], _validatedLayout);
  main.variable(observer("positionedGraph")).define("positionedGraph", ["networkGraph", "validatedLayout", "networkConfig", "d3"], _positionedGraph);
  main.variable(observer()).define(["md"], _10);
  main.variable(observer("unifiedChart")).define("unifiedChart", ["providerColors", "filteredData", "categoryColors", "d3"], _unifiedChart);
  main.variable(observer()).define(["md"], _12);
  main.variable(observer("viewof filters")).define("viewof filters", ["data", "html", "d3"], _filters);
  main.variable(observer("filters")).define("filters", ["Generators", "viewof filters"], (G, _) => G.input(_));
  main.variable(observer("viewof table")).define("viewof table", ["Inputs", "filteredData"], _table);
  main.variable(observer("table")).define("table", ["Generators", "viewof table"], (G, _) => G.input(_));
  main.variable(observer("viewof exportOptions")).define("viewof exportOptions", ["html", "filteredData", "filters"], _exportOptions);
  main.variable(observer("exportOptions")).define("exportOptions", ["Generators", "viewof exportOptions"], (G, _) => G.input(_));
  main.variable(observer("excludedDataSummary")).define("excludedDataSummary", ["data", "providerColors", "html"], _excludedDataSummary);
  main.variable(observer()).define(["md"], _17);
  main.variable(observer()).define(["md"], _18);
  main.variable(observer("embedAPI")).define("embedAPI", ["filteredData", "d3", "URLSearchParams"], _embedAPI);
  main.variable(observer("data")).define("data", ["d3"], _data);
  main.variable(observer("filteredData")).define("filteredData", ["data", "filters"], _filteredData);
  main.variable(observer("audit")).define("audit", ["globalThis"], _audit);
  main.variable(observer("colorSchemes")).define("colorSchemes", ["d3"], _colorSchemes);
  main.variable(observer("categoryColors")).define("categoryColors", ["colorSchemes"], _categoryColors);
  main.variable(observer("providerColors")).define("providerColors", ["colorSchemes"], _providerColors);
  main.variable(observer("networkGraph")).define("networkGraph", ["data"], _networkGraph);
  main.variable(observer("networkConfig")).define("networkConfig", _networkConfig);
  main.variable(observer("layoutStorageKey")).define("layoutStorageKey", _layoutStorageKey);
  main.variable(observer("defaultLayout")).define("defaultLayout", ["FileAttachment"], _defaultLayout);
  main.variable(observer("savedLayout")).define("savedLayout", ["localStorage", "layoutStorageKey"], _savedLayout);
  main.variable(observer()).define(["htl"], _31);
  return main;
}
