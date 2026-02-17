// Sunburst chart: category/technique hierarchy visualization
// Ported from Observable notebook cell: sunburstChart

export function createSunburstChart(data, filteredData, categoryColors, d3) {
  const width = 928;
  const radius = width / 2;

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

  Array.from(techniquesByCategory.entries()).forEach(([categoryName, techniques]) => {
    const categoryNode = {
      name: categoryName,
      children: []
    };

    techniques.forEach((technique) => {
      const evidenceForTechnique = filteredData.filter((d) => d.technique === technique.name);

      const implementingProviders = [...new Set(evidenceForTechnique.map((d) => d.provider))];

      const scoreMap = { High: 3, Medium: 2, Low: 1, Unknown: 0 };
      const avgEffectiveness =
        evidenceForTechnique.length > 0
          ? evidenceForTechnique.reduce((sum, d) => sum + (scoreMap[d.confidence] || 0), 0) /
            evidenceForTechnique.length
          : 0;

      categoryNode.children.push({
        name: technique.name,
        value: 1,
        providers: implementingProviders,
        providerCount: implementingProviders.length,
        evidenceCount: evidenceForTechnique.length,
        avgEffectiveness: avgEffectiveness,
        technique: technique,
        category: categoryName
      });
    });

    categoryNode.children.sort((a, b) => a.name.localeCompare(b.name));

    if (categoryNode.children.length > 0) {
      hierarchyData.children.push(categoryNode);
    }
  });

  hierarchyData.children.sort((a, b) => a.name.localeCompare(b.name));

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
      const totalEvidence = d.data.children.reduce((sum, child) => sum + child.evidenceCount, 0);
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
        d.depth === 1 ? innerRadius + ringWidth * 0.55 : innerRadius + ringWidth * 1.05;
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
