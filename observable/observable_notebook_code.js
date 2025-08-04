function _1(md){return(
md`# LLM Safety Mechanisms Explorer

This interactive notebook provides comprehensive analysis of Large Language Model safety mechanisms, fetching live data from the [LLM Safety Mechanisms GitHub repository](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms).

## Features
- 🔍 Interactive filtering by provider, technique, and rating
- 📊 Custom comparison views and analytics
- 📁 Export data in multiple formats (JSON, CSV, Excel)
- 📚 Embedded documentation and methodology
- 🔗 Shareable visualization configurations
`
)}

function _sunburstChart(data,filteredData,d3)
{
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
      return `Category: ${d.data.name}\n${techniqueCount} technique${
        techniqueCount !== 1 ? "s" : ""
      }\n${totalEvidence} evidence record${totalEvidence !== 1 ? "s" : ""}`;
    }

    if (d.depth === 2) {
      const providerList =
        d.data.providers.length > 0
          ? d.data.providers.join(", ")
          : "No implementations found";
      return `Technique: ${d.data.name}\nCategory: ${
        d.data.category
      }\nImplemented by ${d.data.providerCount} provider${
        d.data.providerCount !== 1 ? "s" : ""
      }\nEvidence records: ${
        d.data.evidenceCount
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


function _filters(html,data,d3)
{
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
                    <span style="color: #666; font-size: 12px; font-weight: normal;"> (${
                      techniques.length
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


function _4(filteredData,filters,data,md){return(
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
)}

async function _data()
{
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


function _filteredData(data,filters)
{
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


function _7(Plot,filteredData){return(
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
)}

function _8(Plot,d3,filteredData){return(
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
)}

function _9(Plot,d3,filteredData){return(
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
)}

function _table(Inputs,filteredData){return(
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
)}

function _exportOptions(html,filteredData,filters)
{
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
    link.download = `llm-safety-mechanisms-${
      new Date().toISOString().split("T")[0]
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
    link.download = `llm-safety-mechanisms-${
      new Date().toISOString().split("T")[0]
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
    link.download = `llm-safety-config-${
      new Date().toISOString().split("T")[0]
    }.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  div.querySelector("#export-json").addEventListener("click", exportJSON);
  div.querySelector("#export-csv").addEventListener("click", exportCSV);
  div.querySelector("#export-config").addEventListener("click", exportConfig);

  return div;
}


function _excludedDataSummary(data,html)
{
  const exclusions = data.exclusions;

  return html`<div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
    <h3 style="color: #856404; margin-top: 0;">📊 Data Quality Report</h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #28a745;">${
          data.evidence.length
        }</div>
        <div style="font-size: 14px; color: #666;">Valid Records</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${
          exclusions.missingProvider.length
        }</div>
        <div style="font-size: 14px; color: #666;">Missing Providers</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${
          exclusions.missingTechnique.length
        }</div>
        <div style="font-size: 14px; color: #666;">Missing Techniques</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${
          exclusions.missingModel.length
        }</div>
        <div style="font-size: 14px; color: #666;">Missing Models</div>
      </div>
      
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #dc3545;">${
          exclusions.missingCategory.length
        }</div>
        <div style="font-size: 14px; color: #666;">Missing Categories</div>
      </div>
    </div>
    
    ${
      exclusions.missingProvider.length > 0
        ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">🏢 Missing Providers (${
          exclusions.missingProvider.length
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
    
    ${
      exclusions.missingTechnique.length > 0
        ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">⚙️ Missing Techniques (${
          exclusions.missingTechnique.length
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
    
    ${
      exclusions.missingModel.length > 0
        ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">🤖 Missing Models (${
          exclusions.missingModel.length
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
    
    ${
      exclusions.missingCategory.length > 0
        ? `
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">📂 Missing Categories (${
          exclusions.missingCategory.length
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


function _embedAPI(filteredData,d3,URLSearchParams)
{
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
      return `${window.location.origin}${
        window.location.pathname
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


function _14(data,md){return(
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
)}

export default function define(runtime, observer) {
  const main = runtime.module();
  main.variable(observer()).define(["md"], _1);
  main.variable(observer("sunburstChart")).define("sunburstChart", ["data","filteredData","d3"], _sunburstChart);
  main.variable(observer("viewof filters")).define("viewof filters", ["html","data","d3"], _filters);
  main.variable(observer("filters")).define("filters", ["Generators", "viewof filters"], (G, _) => G.input(_));
  main.variable(observer()).define(["filteredData","filters","data","md"], _4);
  main.variable(observer("data")).define("data", _data);
  main.variable(observer("filteredData")).define("filteredData", ["data","filters"], _filteredData);
  main.variable(observer()).define(["Plot","filteredData"], _7);
  main.variable(observer()).define(["Plot","d3","filteredData"], _8);
  main.variable(observer()).define(["Plot","d3","filteredData"], _9);
  main.variable(observer("viewof table")).define("viewof table", ["Inputs","filteredData"], _table);
  main.variable(observer("table")).define("table", ["Generators", "viewof table"], (G, _) => G.input(_));
  main.variable(observer("viewof exportOptions")).define("viewof exportOptions", ["html","filteredData","filters"], _exportOptions);
  main.variable(observer("exportOptions")).define("exportOptions", ["Generators", "viewof exportOptions"], (G, _) => G.input(_));
  main.variable(observer("excludedDataSummary")).define("excludedDataSummary", ["data","html"], _excludedDataSummary);
  main.variable(observer("embedAPI")).define("embedAPI", ["filteredData","d3","URLSearchParams"], _embedAPI);
  main.variable(observer()).define(["data","md"], _14);
  return main;
}
