function _1(md) {
  return (
    md`# LLM Safety Mechanisms Explorer

This interactive notebook provides comprehensive analysis of Large Language Model safety mechanisms, fetching live data from the [LLM Safety Mechanisms GitHub repository](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms).

## Features
- 🔍 Interactive filtering by provider, technique, and rating
- 📊 Custom comparison views and analytics
- 📁 Export data in multiple formats (JSON, CSV, Excel)
- 📚 Embedded documentation and methodology
- 🔗 Shareable visualization configurations
`
  )
}

function _sunburstChart(data, filteredData, d3) {
  const width = 928;
  const radius = width / 2;

  // Transform data to hierarchical format using actual categories
  const hierarchyData = {
    name: "Safety Mechanisms",
    children: []
  };

  // Group techniques by their actual category
  const techniquesByCategory = new Map();

  // Use the enriched techniques that have proper category information
  data.techniques.forEach((technique) => {
    const categoryName = technique.category_name || "Other";
    if (!techniquesByCategory.has(categoryName)) {
      techniquesByCategory.set(categoryName, []);
    }
    techniquesByCategory.get(categoryName).push(technique);
  });

  console.log("Categories found:", Array.from(techniquesByCategory.keys()));

  // Create hierarchy with categories as inner ring, techniques as outer ring
  Array.from(techniquesByCategory.entries()).forEach(
    ([categoryName, techniques]) => {
      const categoryNode = {
        name: categoryName,
        children: []
      };

      techniques.forEach((technique) => {
        // Find evidence for this technique
        const evidenceForTechnique = filteredData.filter(
          (d) => d.technique_id === technique.id
        );

        // Get providers implementing this technique
        const implementingProviders = [
          ...new Set(evidenceForTechnique.map((d) => d.provider_name))
        ];

        // Calculate average effectiveness
        const avgEffectiveness =
          evidenceForTechnique.length > 0
            ? evidenceForTechnique.reduce(
              (sum, d) => sum + d.effectiveness_score,
              0
            ) / evidenceForTechnique.length
            : 0;

        categoryNode.children.push({
          name: technique.name,
          value: 1, // Equal weight for all techniques
          providers: implementingProviders,
          providerCount: implementingProviders.length,
          evidenceCount: evidenceForTechnique.length,
          avgEffectiveness: avgEffectiveness,
          technique: technique,
          category: categoryName
        });
      });

      // Sort techniques alphabetically within each category
      categoryNode.children.sort((a, b) => a.name.localeCompare(b.name));

      if (categoryNode.children.length > 0) {
        hierarchyData.children.push(categoryNode);
      }
    }
  );

  // Sort categories alphabetically
  hierarchyData.children.sort((a, b) => a.name.localeCompare(b.name));

  console.log("Hierarchy data:", hierarchyData);

  const hierarchy = d3
    .hierarchy(hierarchyData)
    .sum((d) => d.value || 0) // Changed to 0 to not count parent nodes
    .sort((a, b) => a.data.name.localeCompare(b.data.name));

  const partition = d3.partition().size([2 * Math.PI, radius]);
  partition(hierarchy);

  // Adjust radius scaling for inner and outer rings
  const innerRadius = radius * 0.175;
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

  // Color scale based on actual categories
  const categoryNames = Array.from(techniquesByCategory.keys()).sort();
  const color = d3
    .scaleOrdinal()
    .domain(categoryNames)
    .range(d3.schemeTableau10);

  const svg = d3
    .create("svg")
    .attr("viewBox", [-width / 2, -width / 2, width, width])
    .style("font", "18px sans-serif");

  const g = svg.selectAll("g").data(hierarchy.descendants()).join("g");

  const path = g
    .append("path")
    .attr("fill", (d) => {
      if (d.depth === 0) return "#f0f0f0";
      // Get category color
      let node = d;
      while (node.depth > 1) node = node.parent;
      return color(node.data.name);
    })
    .attr("fill-opacity", (d) => {
      if (d.depth === 0) return 1; // Full opacity for center
      if (d.depth === 2) return 0.6; // 80% opacity for techniques
      return 1; // Full opacity for categories
    })
    .attr("stroke", "#fff")
    .attr("stroke-width", 1)
    .attr("d", arc)
    .style("cursor", (d) => (d.depth > 0 ? "pointer" : "default"));

  // Enhanced tooltips
  path.append("title").text((d) => {
    if (d.depth === 0) return "Safety Mechanisms Overview";

    if (d.depth === 1) {
      const techniqueCount = d.data.children.length;
      const totalEvidence = d.data.children.reduce(
        (sum, child) => sum + child.evidenceCount,
        0
      );
      return `Category: ${d.data.name}\n${techniqueCount} technique${techniqueCount !== 1 ? "s" : ""
        }\n${totalEvidence} evidence record${totalEvidence !== 1 ? "s" : ""}`;
    }

    if (d.depth === 2) {
      const providerList =
        d.data.providers.length > 0
          ? d.data.providers.join(", ")
          : "No implementations found";
      return `Technique: ${d.data.name}\nCategory: ${d.data.category
        }\nImplemented by ${d.data.providerCount} provider${d.data.providerCount !== 1 ? "s" : ""
        }\nEvidence records: ${d.data.evidenceCount
        }\nAvg. effectiveness: ${d.data.avgEffectiveness.toFixed(
          2
        )}\nProviders: ${providerList}`;
    }

    return d.data.name;
  });

  // Helper function to wrap text only if exceeds character limit
  function wrapText(text, maxChars) {
    if (text.length <= maxChars) {
      return [text];
    }

    const words = text.split(/\s+/);
    const lines = [];
    let currentLine = "";

    words.forEach((word) => {
      if (currentLine.length + word.length + 1 <= maxChars) {
        currentLine += (currentLine.length > 0 ? " " : "") + word;
      } else {
        if (currentLine.length > 0) {
          lines.push(currentLine);
        }
        currentLine = word;
      }
    });

    if (currentLine.length > 0) {
      lines.push(currentLine);
    }

    return lines;
  }

  // Add labels - render after paths for proper z-ordering
  g.append("g")
    .attr("class", "label")
    .style("pointer-events", "none")
    .attr("transform", (d) => {
      if (d.depth === 0) return "";

      const angle = (d.x0 + d.x1) / 2;
      const degrees = (angle * 180) / Math.PI - 90;

      let labelRadius;
      if (d.depth === 1) {
        // Category labels close to inner radius
        labelRadius = innerRadius + ringWidth * 0.495;
      } else {
        // Technique labels in middle of outer ring
        labelRadius = innerRadius + ringWidth * 1.1;
      }

      return `rotate(${degrees}) translate(${labelRadius},0)`;
    })
    .each(function (d) {
      if (d.depth === 0) return;

      const group = d3.select(this);
      const angle = (d.x0 + d.x1) / 2;
      const isRightSide = angle < Math.PI;

      const segmentAngle = d.x1 - d.x0;
      const minAngleForLabel = 0.1;

      if (segmentAngle > minAngleForLabel) {
        if (d.depth === 1) {
          // Category labels - single line with same rotation logic as techniques
          group
            .append("text")
            .attr("transform", angle >= Math.PI ? "rotate(180)" : "")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .style("font-size", "14px")
            .style("font-weight", "bold")
            .style("fill", "#333")
            .text(d.data.name);
        } else {
          // Technique labels - wrap only if > 25 chars
          const lines = wrapText(d.data.name, 28);

          lines.forEach((line, i) => {
            group
              .append("text")
              .attr("transform", angle >= Math.PI ? "rotate(180)" : "")
              .attr("text-anchor", isRightSide ? "start" : "end")
              .attr("dy", `${(i - lines.length / 2 + 0.5) * 1.1}em`)
              .attr("x", 0)
              .style("font-size", "12px")
              .style("fill", "#333")
              .text(line);
          });
        }
      }
    });

  // Add center text
  svg
    .append("text")
    .attr("text-anchor", "middle")
    .attr("dy", "-0.5em")
    .style("font-size", "16px")
    .style("font-weight", "bold")
    .style("fill", "#333")
    .text("Safety");

  svg
    .append("text")
    .attr("text-anchor", "middle")
    .attr("dy", "1em")
    .style("font-size", "16px")
    .style("font-weight", "bold")
    .style("fill", "#333")
    .text("Mechanisms");

  // Add legend
  const legend = svg
    .append("g")
    .attr("transform", `translate(${-width / 2 + 20}, ${-width / 2 + 20})`);

  categoryNames.forEach((category, i) => {
    const legendRow = legend
      .append("g")
      .attr("transform", `translate(0, ${i * 20})`);

    legendRow
      .append("rect")
      .attr("width", 15)
      .attr("height", 15)
      .attr("fill", color(category));

    legendRow
      .append("text")
      .attr("x", 20)
      .attr("y", 12)
      .style("font-size", "12px")
      .text(category);
  });

  return svg.node();
}


function _filters(html, data, d3) {
  const form = html`<div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px;">
      
      <!-- Providers Section -->
      <div>
        <h4 style="margin-top: 0; color: #333;">Providers</h4>
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
          ${data.providers
      .sort((a, b) => a.name.localeCompare(b.name))
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
      
      <!-- Categories & Techniques Section -->
      <div>
        <h4 style="margin-top: 0; color: #333;">Categories & Techniques</h4>
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
          ${(() => {
      // Group techniques by category
      const techniquesByCategory = new Map();
      data.techniques.forEach((technique) => {
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
          const categoryColor = d3
            .scaleOrdinal(d3.schemeTableau10)
            .domain(Array.from(techniquesByCategory.keys()))(
              categoryName
            );
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
                        <input type="checkbox" name="techniques" value="${technique.id}" data-category="${categoryName}" style="margin-right: 8px;">
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
    
    <!-- Rating and Search -->
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Minimum Rating</label>
        <input name="rating" type="range" min="0" max="10" step="0.1" value="0" style="width: 100%;">
        <span style="font-size: 12px; color: #666;">Rating: <span id="rating-value">0</span></span>
      </div>
      
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Search</label>
        <input name="search" type="text" placeholder="Search evidence descriptions, summaries..." style="width: 100%; padding: 8px;">
      </div>
    </div>
    
    <!-- Clear All Button -->
    <div style="margin-top: 15px; text-align: center;">
      <button type="button" id="clear-all" style="padding: 10px 20px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Clear All Filters
      </button>
    </div>
    
    <!-- Selection Summary -->
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
  ratingInput.addEventListener("input", () => {
    ratingSpan.textContent = ratingInput.value;
    updateSummary();
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
    ratingSpan.textContent = "0";
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
      summaryParts.push(`Min Rating: ${minRating}`);
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
      techniques: getSelectedValues("techniques"),
      rating: parseFloat(ratingInput.value) || 0,
      search: form.querySelector('input[name="search"]').value || ""
    };
  });

  updateSummary();
  return form;
}


function _4(filteredData, filters, data, md) {
  return (
    md`## Summary Statistics

**Total Evidence Records:** ${filteredData.length.toLocaleString()} ${filters.categories?.length > 0 || filters.providers?.length > 0 || filters.techniques?.length > 0 || filters.rating > 0 || filters.search ? `(filtered from ${data.evidence.length.toLocaleString()})` : ''}

**Unique Categories:** ${new Set(filteredData.map(d => d.category_id)).size}  
**Unique Providers:** ${new Set(filteredData.map(d => d.provider_id)).size}  
**Unique Techniques:** ${new Set(filteredData.map(d => d.technique_id)).size}  
**Average Effectiveness:** ${(filteredData.reduce((sum, d) => sum + d.effectiveness_score, 0) / filteredData.length || 0).toFixed(2)}

${filteredData.length > 0 ? `
**Active Categories:** ${[...new Set(filteredData.map(d => d.category_name))].sort().join(', ')}

**Active Providers:** ${[...new Set(filteredData.map(d => d.provider_name))].sort().join(', ')}
` : '**No data matches current filters**'}

`
  )
}

function _unifiedChart(filteredData, d3) {
  const width = 800;
  const height = 900;

  // Layout configuration - transparent values for easy adjustment
  const layout = {
    techniqueSpacingY: 20, // Vertical spacing between techniques
    techniqueOffsetX: 0, // Horizontal offset for staggering
    categoryPadding: 15, // Padding inside category boxes
    categoryRadius: 8, // Border radius for category boxes
    categoryMinWidth: 120, // Minimum width for category boxes
    nodeMargins: {
      left: 80, // Increased to keep categories fully inside
      right: 80,
      top: 80,
      bottom: 120
    }
  };

  // Provider color scheme
  const providerColors = {
    OpenAI: "#AB68FF",
    Anthropic: "#6C5BB9",
    Google: "#EA4335",
    Microsoft: "#F35325",
    Meta: "#0064E0",
    Amazon: "#131A22",
    Cohere: "#F4CE0E",
    Mistral: "#9AB8D4",
    "Stability AI": "#FC8C84",
    "Hugging Face": "#FF9D00",
    Baidu: "#2529D8",
    Alibaba: "#FF6A00"
  };

  // Category colors - matching sunburst chart
  const categoryColors = {
    "Pre-training Safety": "#2E7D32",
    "Alignment Methods": "#1565C0",
    "Inference Safeguards": "#D32F2F",
    "Novel/Advanced Features": "#F57C00",
    Transparency: "#BE55B1",
    "Governance & Oversight": "#6A1B9A"
  };

  // State management
  let interactionMode = "MULTI";
  let disabledProviders = new Set();
  let disabledCategories = new Set();

  // Build data structure from filteredData
  function buildDataStructure() {
    const data = {};
    const selectedProviders = [
      ...new Set(filteredData.map((d) => d.provider_name))
    ];
    const selectedCategories = [
      ...new Set(filteredData.map((d) => d.category_name))
    ];

    // Build nested structure: data[provider][category][technique] = evidence_data
    filteredData.forEach((evidence) => {
      const provider = evidence.provider_name;
      const category = evidence.category_name;
      const technique = evidence.technique_name;

      if (!data[provider]) data[provider] = {};
      if (!data[provider][category]) data[provider][category] = {};
      if (!data[provider][category][technique]) {
        data[provider][category][technique] = [];
      }
      data[provider][category][technique].push(evidence);
    });

    // For techniques with multiple evidence entries, use the first one for display
    // but aggregate the data appropriately
    Object.keys(data).forEach((provider) => {
      Object.keys(data[provider]).forEach((category) => {
        Object.keys(data[provider][category]).forEach((technique) => {
          const evidenceList = data[provider][category][technique];
          if (evidenceList.length > 0) {
            // Use the first evidence entry but could aggregate ratings, etc.
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

  // Layout positions for categories (TL, TR, MR, BR, BL, ML)
  function getCategoryPosition(index, total) {
    const leftX = layout.nodeMargins.left;
    const rightX = width - layout.nodeMargins.right;
    const topY = layout.nodeMargins.top;
    const bottomY = height - layout.nodeMargins.bottom;
    const middleY = height / 2;

    const positions = [
      { x: leftX, y: topY }, // TL - top-left
      { x: rightX, y: topY }, // TR - top-right
      { x: rightX, y: middleY }, // MR - middle-right
      { x: rightX, y: bottomY }, // BR - bottom-right
      { x: leftX, y: bottomY }, // BL - bottom-left
      { x: leftX, y: middleY } // ML - middle-left
    ];
    return positions[index % positions.length];
  }

  // Measure text width properly
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

    // Add provider nodes - vertical line in center, 75% of height
    const providerX = width / 2;
    const providerStartY = height * 0.125;
    const providerEndY = height * 0.875;
    const providerSpacing =
      (providerEndY - providerStartY) / (selectedProviders.length - 1 || 1);

    selectedProviders.forEach((provider, i) => {
      const node = {
        id: `provider-${provider}`,
        name: provider,
        type: "provider",
        color: providerColors[provider] || "#999",
        x: providerX,
        y: providerStartY + i * providerSpacing,
        fx: providerX,
        fy: providerStartY + i * providerSpacing
      };
      nodes.push(node);
      nodeById.set(node.id, node);
    });

    // Add category nodes and techniques
    selectedCategories.forEach((category, catIndex) => {
      const pos = getCategoryPosition(catIndex, selectedCategories.length);

      // Calculate text width properly
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
        height: 35 // Fixed height for categories
      };
      nodes.push(categoryNode);
      nodeById.set(categoryNode.id, categoryNode);

      const categoryColor = categoryColors[category] || "#666";
      const techniqueColor = lightenColor(categoryColor, 40);
      const techniques = [];

      // Collect techniques for this category
      selectedProviders.forEach((provider) => {
        if (data[provider]?.[category]) {
          Object.keys(data[provider][category]).forEach((technique) => {
            if (!techniques.find((t) => t.name === technique)) {
              techniques.push({ name: technique });
            }
          });
        }
      });

      // Layout techniques with staggered pattern
      techniques.forEach((technique, i) => {
        const techId = `technique-${category}-${technique.name}`;

        // Stagger left and right
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

        // Link category to technique
        links.push({
          source: `category-${category}`,
          target: techId,
          type: "category-technique",
          color: darkenColor(categoryColor, 40)
        });

        // Link providers to technique
        selectedProviders.forEach((provider) => {
          if (data[provider]?.[category]?.[technique.name]) {
            links.push({
              source: `provider-${provider}`,
              target: techId,
              type: "provider-technique",
              color: darkenColor(providerColors[provider] || "#999", 40),
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

  // Add styles
  svg.append("style").text(`
    .link-tooltip {
      position: absolute;
      text-align: left;
      padding: 10px;
      font: 12px sans-serif;
      background: rgba(0, 0, 0, 0.9);
      color: white;
      border-radius: 4px;
      pointer-events: none;
      max-width: 400px;
    }
    .link-tooltip a {
      color: #64b5f6;
      text-decoration: underline;
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

  // Container for main visualization with zoom/pan
  const g = svg.append("g").attr("class", "main-container");

  // Enable zoom/pan
  const zoom = d3
    .zoom()
    .scaleExtent([0.3, 3])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  // Selection area for multi-select mode
  const selectionRect = g
    .append("rect")
    .attr("class", "selection")
    .attr("fill", "rgba(100, 100, 255, 0.1)")
    .attr("stroke", "rgba(100, 100, 255, 0.5)")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "3,3")
    .style("display", "none");

  // Function to rebuild the entire chart when data changes
  function rebuildChart() {
    const newDataStructure = buildDataStructure();
    data = newDataStructure.data;
    selectedProviders = newDataStructure.selectedProviders;
    selectedCategories = newDataStructure.selectedCategories;

    const newGraph = buildGraph();
    nodes = newGraph.nodes;
    links = newGraph.links;
    nodeById = newGraph.nodeById;

    // Clear existing elements
    linkContainer.selectAll("*").remove();
    nodeContainer.selectAll("*").remove();
    providerLegend.selectAll("*").remove();
    categoryLegend.selectAll("*").remove();

    // Rebuild all elements
    buildVisualization();
  }
  // Store references immediately after creation
  function storeReferences(link, techniqueNodes, categoryNodes, providerNodes) {
    window.currentLink = link;
    window.currentTechniqueNodes = techniqueNodes;
    window.currentCategoryNodes = categoryNodes;
    window.currentProviderNodes = providerNodes;
  }
  function buildVisualization() {
    // Draw links (bottom layer)
    const link = linkContainer
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => d.color)
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => (d.type === "category-technique" ? 2 : 1))
      .style("cursor", "pointer");

    // Draw nodes with proper z-order
    // Technique nodes (bottom)
    const techniqueNodes = nodeContainer
      .selectAll(".technique-node")
      .data(nodes.filter((n) => n.type === "technique"))
      .join("g")
      .attr("class", "technique-node node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`);

    // Category nodes (middle) - now as rounded rectangles
    const categoryNodes = nodeContainer
      .selectAll(".category-node")
      .data(nodes.filter((n) => n.type === "category"))
      .join("g")
      .attr("class", "category-node node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`);

    // Provider nodes (top)
    const providerNodes = nodeContainer
      .selectAll(".provider-node")
      .data(nodes.filter((n) => n.type === "provider"))
      .join("g")
      .attr("class", "provider-node node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`);

    // Store references immediately
    storeReferences(link, techniqueNodes, categoryNodes, providerNodes);

    // Draw shapes for each node type
    // Providers - circles
    providerNodes
      .append("circle")
      .attr("r", 10)
      .attr("fill", (d) => d.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // Categories - rounded rectangles with text inside
    categoryNodes.each(function (d) {
      const group = d3.select(this);

      // Draw rounded rectangle
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

      // Add text inside rectangle
      group
        .append("text")
        .attr("class", "category-label")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .text(d.name);
    });

    // Techniques - triangles
    techniqueNodes
      .append("path")
      .attr("d", d3.symbol().type(d3.symbolTriangle).size(150))
      .attr("fill", (d) => d.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // Add labels for providers and techniques only
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

    // Setup node interactions
    setupNodeInteraction(providerNodes);
    setupNodeInteraction(categoryNodes);
    setupNodeInteraction(techniqueNodes);

    // Setup link interactions
    setupLinkInteraction(link);

    // Rebuild legends
    buildLegends();

    // Update all positions and states - now that references are stored
    updateLinks();
    updateVisualization();
  }

  // Draw links (bottom layer)
  const linkContainer = g.append("g").attr("class", "links");

  // Draw nodes with proper z-order
  const nodeContainer = g.append("g").attr("class", "nodes");

  // Controls
  const controls = svg.append("g").attr("transform", `translate(20, 20)`);

  // Mode toggle button
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

  // Reset button
  const resetButton = controls
    .append("g")
    .attr("transform", "translate(90, 0)")
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
    g.attr("transform", d3.zoomIdentity);
    disabledProviders.clear();
    disabledCategories.clear();
    selectedNodes.clear();
    rebuildChart();
  });

  // Legends (inside zoomable container)
  const providerLegend = g
    .append("g")
    .attr("class", "provider-legend")
    .attr("transform", `translate(${width / 2 - 80}, 15)`);

  const categoryLegend = g
    .append("g")
    .attr("class", "category-legend")
    .attr(
      "transform",
      `translate(${width / 2 - 80}, ${height - selectedCategories.length * 20 - 45
      })`
    );

  function buildLegends() {
    // Provider legend
    const providerLegendBg = providerLegend
      .append("rect")
      .attr("class", "legend-container")
      .attr("width", 160)
      .attr("height", 35 + selectedProviders.length * 20)
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

    providerItems
      .append("circle")
      .attr("r", 6)
      .attr("fill", (d) => providerColors[d] || "#999");

    providerItems
      .append("text")
      .attr("x", 12)
      .attr("y", 4)
      .attr("font-size", "12px")
      .text((d) => d);

    providerItems.on("click", function (event, provider) {
      if (disabledProviders.has(provider)) {
        disabledProviders.delete(provider);
      } else {
        disabledProviders.add(provider);
      }
      updateVisualization();
    });

    // Category legend
    categoryLegend.attr(
      "transform",
      `translate(${width / 2 - 80}, ${height - selectedCategories.length * 20 - 45
      })`
    );

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
      if (disabledCategories.has(category)) {
        disabledCategories.delete(category);
      } else {
        disabledCategories.add(category);
      }
      updateVisualization();
    });

    // Make legends draggable
    makeDraggable(providerLegend.style("cursor", "move"));
    makeDraggable(categoryLegend.style("cursor", "move"));
  }

  // Make legends draggable
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

  // Selection state
  const selectedNodes = new Set();
  let selectedLink = null;
  let persistentTooltip = null;

  // Multi-select drag behavior
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

      if (!event.shiftKey && !event.ctrlKey && !event.metaKey) {
        selectedNodes.clear();
      }

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

  // Node interaction
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
        ) {
          return;
        }

        if (event.ctrlKey || event.shiftKey || event.metaKey) {
          if (selectedNodes.has(d.id)) {
            selectedNodes.delete(d.id);
          } else {
            selectedNodes.add(d.id);
          }
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

              if (selectedNodes.has(d.id)) {
                nodes.forEach((node) => {
                  if (selectedNodes.has(node.id)) {
                    node.dragStartX = event.x - node.x;
                    node.dragStartY = event.y - node.y;
                  }
                });
              }
            }
          })
          .on("drag", function (event, d) {
            if (
              interactionMode === "MULTI" &&
              !disabledProviders.has(d.name) &&
              !disabledCategories.has(d.name) &&
              !disabledCategories.has(d.category)
            ) {
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
                  if (nodeGroup) {
                    nodeGroup
                      .filter((n) => selectedNodes.has(n.id))
                      .attr("transform", (n) => `translate(${n.x},${n.y})`);
                  }
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
          })
          .on("end", function () {
            setTimeout(() => {
              preventClear = false;
            }, 100);
          })
      );
  }

  // Link interaction
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

  // Helper functions
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
      if (nodeGroup) {
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
      }
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
          ) {
            return 0.1;
          }
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
        const sourceId = typeof d.source === "string" ? d.source : d.source.id;
        const targetId = typeof d.target === "string" ? d.target : d.target.id;
        return selectedNodes.has(sourceId) || selectedNodes.has(targetId)
          ? 0.6
          : 0.1;
      });
    }
  }

  function updateLinks() {
    if (window.currentLink) {
      window.currentLink
        .attr("x1", (d) => {
          try {
            const source =
              typeof d.source === "string" ? nodeById.get(d.source) : d.source;
            return source?.x || 0;
          } catch (e) {
            return 0;
          }
        })
        .attr("y1", (d) => {
          try {
            const source =
              typeof d.source === "string" ? nodeById.get(d.source) : d.source;
            return source?.y || 0;
          } catch (e) {
            return 0;
          }
        })
        .attr("x2", (d) => {
          try {
            const target =
              typeof d.target === "string" ? nodeById.get(d.target) : d.target;
            return target?.x || 0;
          } catch (e) {
            return 0;
          }
        })
        .attr("y2", (d) => {
          try {
            const target =
              typeof d.target === "string" ? nodeById.get(d.target) : d.target;
            return target?.y || 0;
          } catch (e) {
            return 0;
          }
        });
    }
  }

  function updateVisualization() {
    const providerItems = providerLegend.selectAll(".provider-legend-item");
    const categoryItems = categoryLegend.selectAll(".category-legend-item");

    if (providerItems.size() > 0) {
      providerItems.classed("disabled", (d) => disabledProviders.has(d));
    }
    if (categoryItems.size() > 0) {
      categoryItems.classed("disabled", (d) => disabledCategories.has(d));
    }
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
      // Format source URLs
      let urlsHtml = "N/A";
      if (d.data.sourceUrls && d.data.sourceUrls.length > 0) {
        urlsHtml = d.data.sourceUrls
          .map((urlObj) => {
            if (typeof urlObj === "object" && urlObj.url) {
              return `<a href="${urlObj.url}" target="_blank">${urlObj.title || urlObj.url
                }</a>`;
            }
            return `<a href="${urlObj}" target="_blank">${urlObj}</a>`;
          })
          .join("<br>");
      }

      content = `
        <h4 style="margin: 0 0 5px 0; color: #ffa726;">${source.name} → ${target.name
        }</h4>
        <p style="margin: 3px 0;"><strong>Rating:</strong> ${d.data.rating || "N/A"
        }</p>
        <p style="margin: 3px 0;"><strong>Summary:</strong> ${d.data.summary || "No summary available"
        }</p>
        <p style="margin: 3px 0;"><strong>URL(s):</strong> ${urlsHtml}</p>
        <p style="margin: 3px 0;"><strong>Last Updated:</strong> ${d.data.lastReviewed || d.data.lastUpdated || "Unknown"
        }</p>
      `;
    } else {
      content = `<h4 style="margin: 0; color: #ffa726;">${source.name} → ${target.name}</h4>`;
    }

    tooltip.html(content);
    tooltip.transition().duration(200).style("opacity", 0.95);

    return persistent ? tooltip : null;
  }

  function hideLinkTooltip() {
    if (!persistentTooltip) {
      d3.selectAll(".link-tooltip").remove();
    }
  }

  // Clear selections on background click
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

  // Initial setup
  svg.call(zoom);
  svg.style("cursor", "crosshair");
  buildVisualization();

  // Listen for changes to filteredData - more robust detection
  let lastDataSignature = JSON.stringify(filteredData?.map((d) => d.id).sort());

  const dataWatcher = () => {
    try {
      rebuildChart();
    } catch (error) {
      console.warn("Chart rebuild failed:", error);
      // Fallback: try again after a short delay
      setTimeout(() => {
        try {
          rebuildChart();
        } catch (e) {
          console.error("Chart rebuild failed twice:", e);
        }
      }, 100);
    }
  };

  const checkDataChanges = () => {
    try {
      if (!filteredData || !Array.isArray(filteredData)) return;

      const currentSignature = JSON.stringify(
        filteredData.map((d) => d.id).sort()
      );
      if (currentSignature !== lastDataSignature) {
        lastDataSignature = currentSignature;
        dataWatcher();
      }
    } catch (error) {
      console.warn("Data change detection error:", error);
    }
  };

  // Check for data changes every 100ms
  const dataChangeInterval = setInterval(checkDataChanges, 100);
  // Clean up interval when chart is disposed
  svg.node().addEventListener("DOMNodeRemoved", () => {
    clearInterval(dataChangeInterval);
  });

  return svg.node();
}


async function _data() {
  const baseUrl =
    "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data/";

  try {
    const [evidence, techniques, providers, models, categories] =
      await Promise.all([
        fetch(`${baseUrl}evidence.json`).then((d) => d.json()),
        fetch(`${baseUrl}techniques.json`).then((d) => d.json()),
        fetch(`${baseUrl}providers.json`).then((d) => d.json()),
        fetch(`${baseUrl}models.json`).then((d) => d.json()),
        fetch(`${baseUrl}categories.json`).then((d) => d.json())
      ]);

    // Create lookup maps
    const providerMap = new Map(providers.map((p) => [p.id, p]));
    const categoryMap = new Map(categories.map((c) => [c.id, c]));
    const modelMap = new Map(models.map((m) => [m.id, m]));

    const convertRatingToScore = (rating) => {
      if (typeof rating === "number") return rating;
      if (typeof rating === "string") {
        const lower = rating.toLowerCase();
        switch (lower) {
          case "high":
            return 8;
          case "medium-high":
            return 7;
          case "medium":
            return 5;
          case "medium-low":
            return 3;
          case "low":
            return 2;
          case "very-low":
            return 1;
          default:
            return 0;
        }
      }
      return 0;
    };

    // Enrich techniques with category information
    const enrichedTechniques = techniques.map((technique) => {
      const categoryId =
        technique.categoryId || technique.category_id || technique.category;
      const category = categoryMap.get(categoryId);

      return {
        ...technique,
        category_id: categoryId,
        category_name: category?.name || category?.title || "Other",
        category_obj: category
      };
    });

    const techniqueMap = new Map(enrichedTechniques.map((t) => [t.id, t]));

    // Track exclusions
    const exclusions = {
      missingProvider: [],
      missingTechnique: [],
      missingCategory: [],
      missingModel: [],
      emptyModelIds: []
    };

    const validEvidence = [];

    evidence.forEach((item, index) => {
      const providerId = item.providerId || item.provider_id || item.provider;
      const techniqueId =
        item.techniqueId || item.technique_id || item.technique;

      // Handle modelIds - check if array exists and has content
      let modelId = null;
      let hasValidModel = false;

      if (Array.isArray(item.modelIds) && item.modelIds.length > 0) {
        modelId = item.modelIds[0];
        hasValidModel = true;
      } else if (item.model_id || item.modelId || item.model) {
        modelId = item.model_id || item.modelId || item.model;
        hasValidModel = true;
      } else {
        // No model specified - track but don't exclude
        exclusions.emptyModelIds.push({ ...item, _index: index });
        modelId = null;
        hasValidModel = false;
      }

      const provider = providerMap.get(providerId);
      const technique = techniqueMap.get(techniqueId);
      const model = hasValidModel ? modelMap.get(modelId) : null;

      // Check for missing references (only exclude for missing provider/technique)
      let isValid = true;

      if (!provider) {
        exclusions.missingProvider.push({
          ...item,
          _providerId: providerId,
          _index: index
        });
        isValid = false;
      }

      if (!technique) {
        exclusions.missingTechnique.push({
          ...item,
          _techniqueId: techniqueId,
          _index: index
        });
        isValid = false;
      }

      // For models, track missing but don't exclude from dataset
      if (hasValidModel && !model) {
        exclusions.missingModel.push({
          ...item,
          _modelId: modelId,
          _index: index
        });
      }

      // Category validation through technique
      const categoryId = technique?.category_id;
      const category = categoryMap.get(categoryId);
      if (!category && technique) {
        exclusions.missingCategory.push({
          ...item,
          _categoryId: categoryId,
          _index: index
        });
        isValid = false;
      }

      // Only exclude for missing provider/technique/category, not missing models
      if (isValid) {
        const rating =
          item.rating ||
          item.effectiveness_rating ||
          item.effectiveness ||
          item.score;
        const effectivenessScore = convertRatingToScore(rating);

        const processed = {
          ...item,
          // IDs
          provider_id: providerId,
          technique_id: techniqueId,
          model_id: modelId,
          category_id: categoryId,
          // Names
          provider_name: provider.name,
          technique_name: technique.name,
          model_name:
            model?.name ||
            (hasValidModel
              ? `Unknown Model (${modelId})`
              : "No Model Specified"),
          category_name: category.name,
          // Score and date
          effectiveness_score: effectivenessScore,
          original_rating: rating,
          date_added: item.date_added ? new Date(item.date_added) : new Date(),
          has_valid_model: hasValidModel,
          _index: index
        };

        validEvidence.push(processed);
      }
    });

    console.log("=== DATA VALIDATION SUMMARY ===");
    console.log("Total evidence items:", evidence.length);
    console.log("Valid evidence items:", validEvidence.length);
    console.log("Empty model IDs (included):", exclusions.emptyModelIds.length);
    console.log("Missing models (included):", exclusions.missingModel.length);
    console.log(
      "Missing providers (excluded):",
      exclusions.missingProvider.length
    );
    console.log(
      "Missing techniques (excluded):",
      exclusions.missingTechnique.length
    );

    return {
      evidence: validEvidence,
      techniques: enrichedTechniques,
      providers,
      models,
      categories,
      exclusions,
      lastUpdated: new Date()
    };
  } catch (error) {
    console.error("Error fetching data:", error);
    return {
      evidence: [],
      techniques: [],
      providers: [],
      models: [],
      categories: [],
      exclusions: {
        missingProvider: [],
        missingTechnique: [],
        missingCategory: [],
        missingModel: [],
        emptyModelIds: []
      },
      error: error.message
    };
  }
}


function _filteredData(data, filters) {
  let filtered = [...data.evidence];

  console.log("Initial data count:", filtered.length);
  console.log("Current filters:", filters);

  try {
    // Provider filter
    if (filters && filters.providers && filters.providers.length > 0) {
      filtered = filtered.filter((d) =>
        filters.providers.includes(d.provider_id)
      );
      console.log("After provider filter:", filtered.length);
    }

    // Category filter (if categories are selected, show only those categories)
    if (filters && filters.categories && filters.categories.length > 0) {
      filtered = filtered.filter((d) =>
        filters.categories.includes(d.category_name)
      );
      console.log("After category filter:", filtered.length);
    }

    // Technique filter (if techniques are selected, show only those techniques)
    if (filters && filters.techniques && filters.techniques.length > 0) {
      filtered = filtered.filter((d) =>
        filters.techniques.includes(d.technique_id)
      );
      console.log("After technique filter:", filtered.length);
    }

    // Rating filter
    if (filters && filters.rating && filters.rating > 0) {
      filtered = filtered.filter(
        (d) => d.effectiveness_score >= filters.rating
      );
      console.log("After rating filter:", filtered.length);
    }

    // Search filter
    if (filters && filters.search && filters.search !== "") {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          (d.summary && d.summary.toLowerCase().includes(searchTerm)) ||
          (d.description && d.description.toLowerCase().includes(searchTerm)) ||
          (d.provider_name &&
            d.provider_name.toLowerCase().includes(searchTerm)) ||
          (d.technique_name &&
            d.technique_name.toLowerCase().includes(searchTerm)) ||
          (d.category_name &&
            d.category_name.toLowerCase().includes(searchTerm)) ||
          (d.notes && d.notes.toLowerCase().includes(searchTerm))
      );
      console.log("After search filter:", filtered.length);
    }

    console.log("Final filtered count:", filtered.length);
    return filtered;
  } catch (error) {
    console.error("Error in filtering:", error);
    return data.evidence;
  }
}


function _8(Plot, filteredData) {
  return (
    Plot.plot({
      title: "Effectiveness Rating Distribution",
      width: 800,
      height: 400,
      x: {
        label: "Effectiveness Rating",
        domain: [0, 10]
      },
      y: {
        label: "Count"
      },
      marks: [
        Plot.rectY(
          filteredData,
          Plot.binX({ y: "count" }, { x: "effectiveness_score", fill: "steelblue" })
        ),
        Plot.ruleY([0])
      ]
    })
  )
}

function _9(Plot, d3, filteredData) {
  return (
    Plot.plot({
      title: "Safety Mechanisms by Provider",
      width: 1200,
      height: 400,
      x: {
        label: "Provider"
      },
      y: {
        label: "Number of Mechanisms"
      },
      marks: [
        Plot.barY(
          d3.rollup(
            filteredData,
            (v) => v.length,
            (d) => d.provider_name
          ),
          { x: ([provider]) => provider, y: ([, count]) => count, fill: "orange" }
        ),
        Plot.ruleY([0])
      ]
    })
  )
}

function _10(Plot, d3, filteredData) {
  return (
    Plot.plot({
      title: "Average Effectiveness by Technique",
      width: 800,
      height: 500,
      x: {
        label: "Average Effectiveness Rating"
      },
      y: {
        label: "Technique"
      },
      marks: [
        Plot.barX(
          d3.rollup(
            filteredData,
            (v) => d3.mean(v, (d) => d.effectiveness_score),
            (d) => d.technique_name
          ),
          {
            x: ([, avg]) => avg,
            y: ([technique]) => technique,
            fill: "green",
            sort: { y: "x", reverse: true }
          }
        ),
        Plot.ruleX([0])
      ]
    })
  )
}

function _table(Inputs, filteredData) {
  return (
    Inputs.table(
      filteredData.map((d) => ({
        Category: d.category_name,
        Provider: d.provider_name,
        Technique: d.technique_name,
        Model: d.model_name,
        Score: d.effectiveness_score,
        Description:
          d.summary?.substring(0, 100) + (d.summary?.length > 100 ? "..." : "") ||
          d.description?.substring(0, 100) +
          (d.description?.length > 100 ? "..." : "") ||
          "No description",
        "Date Added": d.date_added.toLocaleDateString()
      })),
      {
        columns: [
          "Category",
          "Provider",
          "Technique",
          "Model",
          "Score",
          "Description",
          "Date Added"
        ]
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
    const headers = [
      "Provider",
      "Technique",
      "Model",
      "Rating",
      "Description",
      "Date Added"
    ];
    const csvData = [
      headers.join(","),
      ...filteredData.map((d) =>
        [
          d.provider_name,
          d.technique_name,
          d.model_name,
          d.effectiveness_score,
          `"${d.description?.replace(/"/g, '""') || ""}"`,
          d.date_added.toISOString()
        ].join(",")
      )
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
      filters: {
        provider: filters.provider,
        technique: filters.technique,
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


function _excludedDataSummary(data, html) {
  const exclusions = data.exclusions;

  return html`<div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
    <h3 style="color: #856404; margin-top: 0;">📊 Data Quality Report</h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #28a745;">${data.evidence.length
    }</div>
        <div style="font-size: 14px; color: #666;">Valid Records</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${exclusions.missingProvider.length
    }</div>
        <div style="font-size: 14px; color: #666;">Missing Providers</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${exclusions.missingTechnique.length
    }</div>
        <div style="font-size: 14px; color: #666;">Missing Techniques</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${exclusions.missingModel.length
    }</div>
        <div style="font-size: 14px; color: #666;">Missing Models</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${exclusions.missingCategory.length
    }</div>
        <div style="font-size: 14px; color: #666;">Missing Categories</div>
      </div>
    </div>
    
    ${exclusions.missingProvider.length > 0
      ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">🏢 Missing Providers (${exclusions.missingProvider.length
      })</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <strong>Provider IDs to add:</strong><br>
          ${[
        ...new Set(
          exclusions.missingProvider.map((item) => item._providerId)
        )
      ]
        .map(
          (id) =>
            `<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px; border-radius: 2px;">${id}</code>`
        )
        .join(" ")}
        </div>
      </details>
    `
      : ""
    }
    
    ${exclusions.missingTechnique.length > 0
      ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">⚙️ Missing Techniques (${exclusions.missingTechnique.length
      })</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <strong>Technique IDs to add:</strong><br>
          ${[
        ...new Set(
          exclusions.missingTechnique.map((item) => item._techniqueId)
        )
      ]
        .map(
          (id) =>
            `<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px; border-radius: 2px;">${id}</code>`
        )
        .join(" ")}
        </div>
      </details>
    `
      : ""
    }
    
    ${exclusions.missingModel.length > 0
      ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">🤖 Missing Models (${exclusions.missingModel.length
      })</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <strong>Model IDs to add:</strong><br>
          ${[...new Set(exclusions.missingModel.map((item) => item._modelId))]
        .map(
          (id) =>
            `<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px; border-radius: 2px;">${id}</code>`
        )
        .join(" ")}
        </div>
      </details>
    `
      : ""
    }
    
    ${exclusions.missingCategory.length > 0
      ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">📂 Missing Categories (${exclusions.missingCategory.length
      })</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <strong>Category IDs to add:</strong><br>
          ${[
        ...new Set(
          exclusions.missingCategory.map((item) => item._categoryId)
        )
      ]
        .map(
          (id) =>
            `<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px; border-radius: 2px;">${id}</code>`
        )
        .join(" ")}
        </div>
      </details>
    `
      : ""
    }
    
    <div style="font-size: 14px; color: #856404; font-style: italic;">
      💡 <strong>Next Steps:</strong> Add the missing IDs to their respective JSON files to include all evidence in the dataset.
    </div>
  </div>`;
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


function _15(data, md) {
  return (
    md`## Documentation

### Data Sources
This notebook fetches live data from the following GitHub repository endpoints:
- **Evidence**: \\\`evidence.json\\\` - Contains safety mechanism implementations and their effectiveness ratings
- **Techniques**: \\\`techniques.json\\\` - Catalog of safety techniques and methodologies  
- **Providers**: \\\`providers.json\\\` - LLM provider information and metadata
- **Models**: \\\`models.json\\\` - Model specifications and capabilities

### Methodology
- **Effectiveness Ratings**: Numerical scores from 0-10 indicating the effectiveness of safety mechanisms
- **Data Processing**: Real-time data fetching with automatic enrichment and cross-referencing
- **Filtering**: Multi-dimensional filtering across providers, techniques, ratings, and free-text search

### Usage Examples

#### Basic Filtering
1. Select a provider from the dropdown to focus on specific implementations
2. Choose a technique type to analyze particular safety approaches
3. Adjust the minimum rating slider to filter by effectiveness threshold
4. Use the search box for free-text filtering across descriptions

#### Advanced Analytics
- **Distribution Analysis**: Examine the spread of effectiveness ratings
- **Provider Comparison**: Compare safety mechanism adoption across providers
- **Technique Effectiveness**: Identify the most effective safety approaches

#### Data Export
- **JSON Export**: Full structured data with all fields and metadata
- **CSV Export**: Tabular format suitable for spreadsheet analysis
- **Configuration Export**: Save current filter settings for reproducibility

### API Integration
The notebook exposes an embedding API for integration with other applications:

\\\`\\\`\\\`javascript
// Get processed chart data
const chartData = embedAPI.getChartData('distribution');

// Generate shareable URL
const shareURL = embedAPI.generateShareableURL(filters);

// Get summary statistics
const stats = embedAPI.getSummaryStats();
\\\`\\\`\\\`

### Technical Notes
- Data refreshes automatically on notebook reload
- All visualizations are responsive and interactive
- Export functions generate timestamped files
- Shareable configurations preserve filter states

Last updated: ${data.lastUpdated.toLocaleString()}

---

**Repository**: [LLM Safety Mechanisms](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms)  
**License**: MIT  
**Maintainer**: Observable Notebook Community`
  )
}

export default function define(runtime, observer) {
  const main = runtime.module();
  main.variable(observer()).define(["md"], _1);
  main.variable(observer("sunburstChart")).define("sunburstChart", ["data", "filteredData", "d3"], _sunburstChart);
  main.variable(observer("viewof filters")).define("viewof filters", ["html", "data", "d3"], _filters);
  main.variable(observer("filters")).define("filters", ["Generators", "viewof filters"], (G, _) => G.input(_));
  main.variable(observer()).define(["filteredData", "filters", "data", "md"], _4);
  main.variable(observer("unifiedChart")).define("unifiedChart", ["filteredData", "d3"], _unifiedChart);
  main.variable(observer("data")).define("data", _data);
  main.variable(observer("filteredData")).define("filteredData", ["data", "filters"], _filteredData);
  main.variable(observer()).define(["Plot", "filteredData"], _8);
  main.variable(observer()).define(["Plot", "d3", "filteredData"], _9);
  main.variable(observer()).define(["Plot", "d3", "filteredData"], _10);
  main.variable(observer("viewof table")).define("viewof table", ["Inputs", "filteredData"], _table);
  main.variable(observer("table")).define("table", ["Generators", "viewof table"], (G, _) => G.input(_));
  main.variable(observer("viewof exportOptions")).define("viewof exportOptions", ["html", "filteredData", "filters"], _exportOptions);
  main.variable(observer("exportOptions")).define("exportOptions", ["Generators", "viewof exportOptions"], (G, _) => G.input(_));
  main.variable(observer("excludedDataSummary")).define("excludedDataSummary", ["data", "html"], _excludedDataSummary);
  main.variable(observer("embedAPI")).define("embedAPI", ["filteredData", "d3", "URLSearchParams"], _embedAPI);
  main.variable(observer()).define(["data", "md"], _15);
  return main;
}
