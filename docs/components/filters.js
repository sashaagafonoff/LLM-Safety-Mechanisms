// Hierarchical filter UI component
// Ported from Observable notebook cell: `viewof filters`
import {html} from "htl";

export function createFilterForm(data, d3) {
  const uniqueProviders = Array.from(new Set(data.flatPairs.map((d) => d.provider)))
    .filter((p) => p)
    .sort()
    .map((p) => ({ id: p, name: p }));

  const catMap = new Map(data.categories.map((c) => [c.id, c.name]));

  const techniquesWithCategories = data.techniques.map((t) => ({
    id: t.id,
    name: t.name,
    category_name: catMap.get(t.categoryId) || "Uncategorized"
  }));

  const techniquesByCategory = new Map();
  techniquesWithCategories.forEach((technique) => {
    const categoryName = technique.category_name || "Other";
    if (!techniquesByCategory.has(categoryName)) {
      techniquesByCategory.set(categoryName, []);
    }
    techniquesByCategory.get(categoryName).push(technique);
  });

  const sortedCategories = Array.from(techniquesByCategory.entries())
    .sort(([a], [b]) => a.localeCompare(b));

  const colorScale = d3.scaleOrdinal(d3.schemeTableau10)
    .domain(Array.from(techniquesByCategory.keys()));

  const form = html`<div style="background: #f8f9fa; border-radius: 8px; padding: 10px; margin-bottom: 10px; font-family: sans-serif;">
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 10px;">
      <div>
        <h4 style="margin-top: 0; color: #333;">Providers</h4>
        <div style="max-height: 250px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
          ${uniqueProviders.map((provider) =>
            html`<label style="display: block; margin-bottom: 8px; cursor: pointer;">
              <input type="checkbox" name="providers" value="${provider.id}" style="margin-right: 8px;">
              <span style="font-size: 12px;">${provider.name}</span>
            </label>`
          )}
        </div>
        <div style="margin-top: 10px;">
          <button type="button" id="select-all-providers" style="font-size: 11px; padding: 4px 5px; margin-right: 5px;">Select All</button>
          <button type="button" id="clear-providers" style="font-size: 11px; padding: 4px 5px;">Clear All</button>
        </div>
      </div>
      <div>
        <h4 style="margin-top: 0; color: #333;">Categories & Techniques</h4>
        <div style="max-height: 250px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
          ${sortedCategories.map(([categoryName, techniques], categoryIndex) => {
            const categoryColor = colorScale(categoryName);
            const categoryId = `category-${categoryIndex}`;
            return html`<div style="margin-bottom: 5px; border-left: 4px solid ${categoryColor}; padding-left: 5px;">
              <label style="display: block; font-weight: bold; cursor: pointer; margin-bottom: 5px;">
                <input type="checkbox" name="categories" value="${categoryName}" id="${categoryId}" style="margin-right: 8px;">
                <span style="color: ${categoryColor}; font-size: 12px;">${categoryName}</span>
                <span style="color: #666; font-size: 11px; font-weight: normal;"> (${techniques.length})</span>
              </label>
              <div style="margin-left: 10px;">
                ${techniques.sort((a, b) => a.name.localeCompare(b.name)).map((technique) =>
                  html`<label style="display: block; margin: 0 0 4px 0; padding: 0; cursor: pointer;">
                    <input type="checkbox" name="techniques" value="${technique.name}" data-category="${categoryName}" style="margin-right: 5px;">
                    <span style="font-size: 12px; color: #555;">${technique.name}</span>
                  </label>`
                )}
              </div>
            </div>`;
          })}
        </div>
        <div style="margin-top: 5px;">
          <button type="button" id="select-all-categories" style="font-size: 11px; padding: 4px 5px; margin-right: 5px;">Select All Categories</button>
          <button type="button" id="clear-categories" style="font-size: 11px; padding: 4px 5px;">Clear All</button>
        </div>
      </div>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;">
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Minimum Confidence</label>
        <input name="rating" type="range" min="0" max="3" step="1" value="0" style="width: 100%;">
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888;">
          <span>All</span><span>Low</span><span>Med</span><span>High</span>
        </div>
        <span style="font-size: 11px; color: #666;">Current: <span id="rating-value">All</span></span>
      </div>
      <div>
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Search</label>
        <input name="search" type="text" placeholder="Search evidence descriptions, summaries..." style="width: 100%; padding: 8px;">
      </div>
    </div>
    <div style="margin-top: 5px; text-align: center;">
      <button type="button" id="clear-all" style="padding: 5px 10px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Clear All Filters
      </button>
    </div>
    <div style="margin-top: 5px; font-size: 11px; color: #666; border-top: 1px solid #ddd; padding-top: 5px;">
      <strong>Selected:</strong>
      <span id="selection-summary">No filters applied</span>
    </div>
  </div>`;

  // Helper functions
  const getSelectedValues = (name) =>
    Array.from(form.querySelectorAll(`input[name="${name}"]:checked`)).map((input) => input.value);

  const getSelectedText = (name) =>
    Array.from(form.querySelectorAll(`input[name="${name}"]:checked`)).map((input) => {
      const label = input.closest("label").textContent.trim();
      return label.split("(")[0].trim();
    });

  const ratingSpan = form.querySelector("#rating-value");
  const ratingInput = form.querySelector('input[name="rating"]');
  const ratingLabels = { 0: "All", 1: "Low+", 2: "Medium+", 3: "High" };

  ratingInput.addEventListener("input", () => {
    ratingSpan.textContent = ratingLabels[ratingInput.value];
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  // Category checkbox logic
  form.querySelectorAll('input[name="categories"]').forEach((categoryCheckbox) => {
    categoryCheckbox.addEventListener("change", (e) => {
      const categoryName = e.target.value;
      const isChecked = e.target.checked;
      form.querySelectorAll(`input[name="techniques"][data-category="${categoryName}"]`)
        .forEach((checkbox) => { checkbox.checked = isChecked; });
      updateSummary();
      form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
    });
  });

  // Technique checkbox logic
  form.querySelectorAll('input[name="techniques"]').forEach((techniqueCheckbox) => {
    techniqueCheckbox.addEventListener("change", (e) => {
      const categoryName = e.target.dataset.category;
      const categoryCheckbox = form.querySelector(`input[name="categories"][value="${categoryName}"]`);
      const allTechniques = form.querySelectorAll(`input[name="techniques"][data-category="${categoryName}"]`);
      const checkedTechniques = form.querySelectorAll(`input[name="techniques"][data-category="${categoryName}"]:checked`);

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
    form.querySelectorAll('input[name="providers"]').forEach((cb) => (cb.checked = true));
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  form.querySelector("#clear-providers").addEventListener("click", () => {
    form.querySelectorAll('input[name="providers"]').forEach((cb) => (cb.checked = false));
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  form.querySelector("#select-all-categories").addEventListener("click", () => {
    form.querySelectorAll('input[name="categories"], input[name="techniques"]').forEach((cb) => (cb.checked = true));
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  form.querySelector("#clear-categories").addEventListener("click", () => {
    form.querySelectorAll('input[name="categories"], input[name="techniques"]').forEach((cb) => {
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

  const updateSummary = () => {
    const selectedProviders = getSelectedText("providers");
    const selectedCategories = getSelectedText("categories");
    const selectedTechniques = getSelectedText("techniques");
    const minRating = parseFloat(ratingInput.value);
    const searchTerm = form.querySelector('input[name="search"]').value;

    const summaryParts = [];
    if (selectedProviders.length > 0) summaryParts.push(`Providers: ${selectedProviders.join(", ")}`);
    if (selectedCategories.length > 0) summaryParts.push(`Categories: ${selectedCategories.join(", ")}`);
    if (selectedTechniques.length > 0) summaryParts.push(`Techniques: ${selectedTechniques.length} selected`);
    if (minRating > 0) summaryParts.push(`Min Confidence: ${ratingLabels[minRating]}`);
    if (searchTerm) summaryParts.push(`Search: "${searchTerm}"`);

    form.querySelector("#selection-summary").textContent =
      summaryParts.length > 0 ? summaryParts.join(" | ") : "No filters applied";
  };

  form.querySelector('input[name="search"]').addEventListener("input", () => {
    updateSummary();
    form.dispatchEvent(new CustomEvent("input", { bubbles: true }));
  });

  // Initialize form value
  form.value = { providers: [], categories: [], techniques: [], rating: 0, search: "" };

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
