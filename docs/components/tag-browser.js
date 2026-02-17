// Browsable source document list for the tagging tool
// Displays sources grouped by provider with existing technique tags
import {html} from "htl";

export function createSourceBrowser(tagData, d3) {
  const {sources, providers} = tagData;

  let selectedSourceId = null;

  // Group sources by provider
  const byProvider = new Map();
  for (const s of sources) {
    if (!byProvider.has(s.providerId)) byProvider.set(s.providerId, []);
    byProvider.get(s.providerId).push(s);
  }

  // Sort providers by name
  const sortedProviders = providers
    .filter((p) => byProvider.has(p.id))
    .sort((a, b) => a.name.localeCompare(b.name));

  const confidenceColor = (c) =>
    c === "High" ? "#2e7d32" : c === "Medium" ? "#f57f17" : "#c62828";

  // Build the container
  const container = html`<div style="font-family: sans-serif;">
    <div style="display: flex; gap: 10px; margin-bottom: 12px; align-items: center; flex-wrap: wrap;">
      <label style="font-size: 13px; font-weight: 600; color: #555;">Filter by provider:</label>
      <select id="provider-filter" style="padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; font-size: 13px;">
        <option value="">All providers</option>
        ${sortedProviders.map((p) => html`<option value="${p.id}">${p.name}</option>`)}
      </select>
      <input id="search-input" type="text" placeholder="Search sources..." style="padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; font-size: 13px; flex: 1; min-width: 180px;">
    </div>
    <div id="source-list" style="max-height: 500px; overflow-y: auto;"></div>
  </div>`;

  const listEl = container.querySelector("#source-list");
  const providerFilter = container.querySelector("#provider-filter");
  const searchInput = container.querySelector("#search-input");

  function renderList() {
    const filterProv = providerFilter.value;
    const searchTerm = searchInput.value.toLowerCase().trim();
    listEl.innerHTML = "";

    for (const prov of sortedProviders) {
      if (filterProv && prov.id !== filterProv) continue;

      let provSources = byProvider.get(prov.id) || [];
      if (searchTerm) {
        provSources = provSources.filter(
          (s) =>
            s.title.toLowerCase().includes(searchTerm) ||
            s.existingTags.some((t) => t.techniqueName.toLowerCase().includes(searchTerm))
        );
      }
      if (provSources.length === 0) continue;

      const provSection = html`<div style="margin-bottom: 16px;">
        <div style="font-weight: 700; font-size: 14px; color: #333; margin-bottom: 6px; border-bottom: 2px solid #e0e0e0; padding-bottom: 4px;">
          ${prov.name} <span style="font-weight: 400; color: #999; font-size: 12px;">(${provSources.length} source${provSources.length !== 1 ? "s" : ""})</span>
        </div>
      </div>`;

      for (const src of provSources) {
        const isSelected = src.id === selectedSourceId;
        const card = buildSourceCard(src, isSelected);
        card.addEventListener("click", () => {
          selectedSourceId = src.id;
          container.value = src;
          container.dispatchEvent(new Event("input", {bubbles: true}));
          renderList();
        });
        provSection.appendChild(card);
      }
      listEl.appendChild(provSection);
    }

    if (listEl.children.length === 0) {
      listEl.appendChild(html`<div style="color: #999; padding: 20px; text-align: center; font-size: 13px;">No sources match your filter.</div>`);
    }
  }

  function buildSourceCard(src, isSelected) {
    const tagBadges = src.existingTags.slice(0, 8).map((t) => {
      return html`<span style="
        display: inline-block; padding: 2px 6px; margin: 1px 3px 1px 0; border-radius: 3px;
        font-size: 10px; font-weight: 500; color: white; background: ${t.categoryColor};
        opacity: ${t.confidence === "High" ? 1 : t.confidence === "Medium" ? 0.75 : 0.55};
      " title="${t.techniqueName} (${t.confidence} confidence)">${t.techniqueName}</span>`;
    });
    const moreCount = src.existingTags.length - 8;

    return html`<div style="
      padding: 10px 12px; margin-bottom: 6px; border-radius: 6px; cursor: pointer;
      border: 2px solid ${isSelected ? "#1976D2" : "#e0e0e0"};
      background: ${isSelected ? "#e3f2fd" : "white"};
      transition: border-color 0.15s, background 0.15s;
    " class="source-card">
      <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <div style="font-weight: 600; font-size: 13px; color: #222;">${src.title}</div>
        <div style="font-size: 11px; color: #888; white-space: nowrap; margin-left: 8px;">${src.type}</div>
      </div>
      <div style="font-size: 11px; color: #666; margin-top: 2px;">
        ${src.models.length > 0 ? src.models.map((m) => m.name).join(", ") : "No models listed"}
      </div>
      <div style="margin-top: 6px; line-height: 1.6;">
        ${tagBadges}
        ${moreCount > 0 ? html`<span style="font-size: 10px; color: #888;">+${moreCount} more</span>` : ""}
        ${src.existingTags.length === 0 ? html`<span style="font-size: 11px; color: #aaa; font-style: italic;">No tags yet</span>` : ""}
      </div>
    </div>`;
  }

  // Wire up filter events
  providerFilter.addEventListener("input", renderList);
  searchInput.addEventListener("input", renderList);

  // Add hover effect via stylesheet
  const style = html`<style>
    .source-card:hover { border-color: #90caf9 !important; }
  </style>`;
  container.prepend(style);

  container.value = null;
  renderList();
  return container;
}
