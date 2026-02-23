// Shared network graph interactions: marquee selection, multi-node drag, click-to-select
// Used by commentary-view.js and incidents-view.js

export function setupNetworkInteractions({
  d3, svg, g, nodes, nodeById, nodeGroups, linkElements, updateLinks,
  width, height, toolbar, status, showStatus,
  onLayoutModified, uniqueId
}) {
  const selectedNodes = new Set();
  let currentTransform = d3.zoomIdentity;
  let isDragging = false;

  // ── CSS styles ──
  svg.append("style").text(`
    .selected circle, .selected rect, .selected path { filter: drop-shadow(0 0 3px #0066cc); }
    .dragging { cursor: grabbing !important; }
  `);

  // ── Zoom (wheel/dblclick only, freeing mouse drag for marquee) ──
  const zoom = d3.zoom()
    .scaleExtent([0.3, 3])
    .filter((event) => event.type === "wheel" || event.type === "dblclick")
    .on("zoom", (event) => {
      currentTransform = event.transform;
      g.attr("transform", event.transform);
    });
  svg.call(zoom);

  // ── Background rect for marquee capture ──
  const bgRect = g.insert("rect", ":first-child")
    .attr("width", width * 4)
    .attr("height", height * 4)
    .attr("x", -width * 2)
    .attr("y", -height * 2)
    .attr("fill", "transparent");

  // ── Selection status in toolbar ──
  const selectionStatus = toolbar
    .append("span")
    .style("font-size", "11px")
    .style("color", "#666")
    .style("margin-left", "12px")
    .text("");

  function updateSelectionStatus() {
    selectionStatus.text(
      selectedNodes.size === 0 ? "" : `${selectedNodes.size} selected (Esc to clear)`
    );
  }

  // ── Clear button ──
  const buttonStyle = `
    padding: 5px 10px; font-size: 12px; border: 1px solid #ccc;
    border-radius: 4px; background: #fff; color: #333; cursor: pointer;
    transition: background 0.15s;
  `;

  toolbar.append("button")
    .attr("style", buttonStyle)
    .text("\u2298 Clear")
    .on("click", () => { clearSelection(); })
    .on("mouseover", function () { d3.select(this).style("background", "#f0f0f0"); })
    .on("mouseout", function () { d3.select(this).style("background", "#fff"); });

  // ── Selection visuals ──
  function updateSelectionVisuals() {
    nodeGroups.forEach((sel) => {
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
      nodeGroups.forEach((sel) => {
        sel.style("opacity", (d) => (selectedNodes.has(d.id) ? 1 : 0.3));
      });
    } else {
      linkElements.style("opacity", null);
      nodeGroups.forEach((sel) => {
        sel.style("opacity", 1);
      });
    }
  }

  function clearSelection() {
    selectedNodes.clear();
    updateSelectionVisuals();
    updateSelectionStatus();
  }

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
    .on(`mousemove.marquee-${uniqueId}`, function (event) {
      if (!isMarqueeSelecting || !marqueeStart) return;
      const [x, y] = d3.pointer(event, svg.node());
      const minX = Math.min(marqueeStart.x, x);
      const minY = Math.min(marqueeStart.y, y);
      marquee
        .attr("x", minX).attr("y", minY)
        .attr("width", Math.abs(x - marqueeStart.x))
        .attr("height", Math.abs(y - marqueeStart.y));
    })
    .on(`mouseup.marquee-${uniqueId}`, function (event) {
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

  // ── Background click clears selection ──
  bgRect.on("click", function (event) {
    if (!isMarqueeSelecting) {
      clearSelection();
    }
  });

  // ── Escape key clears selection ──
  d3.select("body").on(`keydown.${uniqueId}`, function (event) {
    if (event.key === "Escape") {
      clearSelection();
    }
  });

  // ── Click-to-select on nodes ──
  nodeGroups.forEach((sel) => {
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

  // ── Multi-node drag ──
  function setupDrag(selection) {
    let dragStartPositions = new Map();

    selection.call(
      d3.drag()
        .on("start", function (event, d) {
          isDragging = true;
          if (!selectedNodes.has(d.id)) {
            if (!event.sourceEvent.shiftKey) selectedNodes.clear();
            selectedNodes.add(d.id);
            updateSelectionVisuals();
            updateSelectionStatus();
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
              node.fx = node.x;
              node.fy = node.y;
            }
          });

          nodeGroups.forEach((sel) => {
            sel.filter((n) => selectedNodes.has(n.id))
              .attr("transform", (n) => `translate(${n.x},${n.y})`);
          });

          updateLinks();
          onLayoutModified();
        })
        .on("end", function () {
          d3.select(this).classed("dragging", false);
          dragStartPositions.clear();
          isDragging = false;
        })
    );
  }

  nodeGroups.forEach((sel) => setupDrag(sel));

  return {
    selectedNodes,
    updateSelectionVisuals,
    clearSelection,
    getCurrentTransform: () => currentTransform
  };
}
