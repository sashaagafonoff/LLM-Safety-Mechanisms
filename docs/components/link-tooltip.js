// Shared link tooltip module for network chart views.
// Provides hover tooltips on links, click-to-persist, and draggable persistent tooltips.
//
// Usage:
//   import { setupLinkTooltips } from "./link-tooltip.js";
//   const linkTooltips = setupLinkTooltips({
//     d3, linkGroup, linkElements, links, nodeById,
//     buildTooltipHtml: (d) => `<h4>...</h4>`,
//     uniqueId: "my-chart"
//   });
//   // In updateLinks(), also call: linkTooltips.updateHitAreas();

export function setupLinkTooltips({ d3, svg, linkGroup, linkElements, links, nodeById, buildTooltipHtml, uniqueId }) {
  let persistentTooltip = null;
  let selectedLinkElement = null;

  // Hit-area lines overlaying visible links for pointer interaction
  const linkHitAreas = linkGroup
    .selectAll(`.link-hit-area-${uniqueId}`)
    .data(links)
    .join("line")
    .attr("class", `link-hit-area-${uniqueId}`)
    .attr("stroke", "transparent")
    .attr("stroke-width", 12)
    .style("pointer-events", "stroke")
    .style("cursor", "pointer")
    .on("mouseenter", function (event, d) {
      if (persistentTooltip) return;
      linkElements.filter((l) => l === d)
        .attr("stroke-opacity", 0.9)
        .attr("stroke-width", 2.5);
      showTooltip(event, d);
    })
    .on("mousemove", function (event) {
      if (persistentTooltip) return;
      d3.selectAll(`.link-tooltip-${uniqueId}`)
        .style("left", event.pageX + 10 + "px")
        .style("top", event.pageY - 28 + "px");
    })
    .on("mouseleave", function (event, d) {
      if (persistentTooltip) return;
      linkElements.filter((l) => l === d)
        .attr("stroke-opacity", (l) => l._origOpacity || 0.5)
        .attr("stroke-width", (l) => l._origWidth || 1);
      hideTooltip();
    })
    .on("click", function (event, d) {
      event.stopPropagation();
      if (persistentTooltip) {
        dismiss();
        return;
      }
      selectedLinkElement = linkElements.filter((l) => l === d);
      selectedLinkElement.attr("stroke-opacity", 1).attr("stroke-width", 3);
      persistentTooltip = showTooltip(event, d, true);
      makeDraggable(persistentTooltip);
    });

  // Store original link styles for restoration
  linkElements.each(function (d) {
    d._origOpacity = parseFloat(d3.select(this).attr("stroke-opacity")) || 0.5;
    d._origWidth = parseFloat(d3.select(this).attr("stroke-width")) || 1;
  });

  // Dismiss persistent tooltip on SVG background click
  if (svg) {
    const prevClick = svg.on("click");
    svg.on("click", function (event) {
      if (persistentTooltip) dismiss();
      if (prevClick) prevClick.call(this, event);
    });
  }

  function showTooltip(event, d, persistent = false) {
    hideTooltip();
    const html = buildTooltipHtml(d);
    if (!html) return null;

    const dragHandle = persistent
      ? `<div class="tooltip-drag-handle" style="cursor:grab;padding:2px 0 6px;margin-bottom:6px;border-bottom:1px solid #444;display:flex;justify-content:space-between;align-items:center;"><span style="color:#888;font-size:10px;">Drag to move</span><span style="color:#888;font-size:10px;">Click chart to dismiss</span></div>`
      : "";

    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", `link-tooltip-${uniqueId}`)
      .style("position", "absolute")
      .style("text-align", "left")
      .style("padding", "10px")
      .style("font", "12px sans-serif")
      .style("background", "rgba(0, 0, 0, 0.95)")
      .style("color", "white")
      .style("border-radius", "4px")
      .style("max-width", "400px")
      .style("box-shadow", "0 4px 6px rgba(0,0,0,0.3)")
      .style("border", persistent ? "1px solid #555" : "1px solid #333")
      .style("pointer-events", persistent ? "auto" : "none")
      .style("z-index", 1000)
      .style("left", event.pageX + 10 + "px")
      .style("top", event.pageY - 28 + "px")
      .style("opacity", 0)
      .html(dragHandle + html);

    tooltip.transition().duration(200).style("opacity", 0.95);
    return persistent ? tooltip : null;
  }

  function hideTooltip() {
    if (!persistentTooltip) d3.selectAll(`.link-tooltip-${uniqueId}`).remove();
  }

  function dismiss() {
    if (persistentTooltip) {
      d3.select("body").on(`mousemove.tooltipDrag-${uniqueId}`, null).on(`mouseup.tooltipDrag-${uniqueId}`, null);
      persistentTooltip.remove();
      persistentTooltip = null;
    }
    if (selectedLinkElement) {
      selectedLinkElement
        .attr("stroke-opacity", (d) => d._origOpacity || 0.5)
        .attr("stroke-width", (d) => d._origWidth || 1);
      selectedLinkElement = null;
    }
    d3.selectAll(`.link-tooltip-${uniqueId}`).remove();
  }

  function makeDraggable(tooltipEl) {
    if (!tooltipEl) return;
    const node = tooltipEl.node();
    let dragOffsetX = 0, dragOffsetY = 0, isDraggingTooltip = false;

    const header = tooltipEl.select(".tooltip-drag-handle");
    const target = header.empty() ? tooltipEl : header;
    target.style("cursor", "grab");

    target.on("mousedown.drag", function (event) {
      event.preventDefault();
      event.stopPropagation();
      isDraggingTooltip = true;
      const rect = node.getBoundingClientRect();
      dragOffsetX = event.clientX - rect.left;
      dragOffsetY = event.clientY - rect.top;
      target.style("cursor", "grabbing");
    });

    d3.select("body")
      .on(`mousemove.tooltipDrag-${uniqueId}`, function (event) {
        if (!isDraggingTooltip) return;
        node.style.left = (event.clientX - dragOffsetX + window.scrollX) + "px";
        node.style.top = (event.clientY - dragOffsetY + window.scrollY) + "px";
      })
      .on(`mouseup.tooltipDrag-${uniqueId}`, function () {
        if (isDraggingTooltip) {
          isDraggingTooltip = false;
          target.style("cursor", "grab");
        }
      });
  }

  function updateHitAreas() {
    const resolve = (ref) => typeof ref === "string" ? nodeById.get(ref) : ref;
    linkHitAreas
      .attr("x1", (d) => { const s = resolve(d.source); return s ? s.x : 0; })
      .attr("y1", (d) => { const s = resolve(d.source); return s ? s.y : 0; })
      .attr("x2", (d) => { const t = resolve(d.target); return t ? t.x : 0; })
      .attr("y2", (d) => { const t = resolve(d.target); return t ? t.y : 0; });
  }

  return { dismiss, updateHitAreas, isPersistent: () => !!persistentTooltip };
}
