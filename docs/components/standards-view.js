// Standards alignment view: shows technique coverage across external frameworks
import {html} from "htl";

export function createStandardsView(data) {
  const standards = data.raw.standards;
  const mapping = data.raw.standardsMapping || [];
  const techniques = data.raw.techniques;

  if (!standards || !standards.frameworks || standards.frameworks.length === 0) {
    return html`<p style="color: #999;">No standards data loaded.</p>`;
  }

  const techLookup = new Map(techniques.map((t) => [t.id, t]));
  const catLookup = new Map((data.raw.categories || []).map((c) => [c.id, c]));

  // Build lookup: frameworkId -> code -> [{techniqueId, relationship, notes}]
  const coverageMap = new Map();
  for (const fw of standards.frameworks) {
    const fwMap = new Map();
    const allCodes = flattenCodes(fw.structure);
    for (const code of allCodes) {
      fwMap.set(code, []);
    }
    coverageMap.set(fw.id, fwMap);
  }

  for (const m of mapping) {
    const fwMap = coverageMap.get(m.frameworkId);
    if (!fwMap) continue;
    for (const code of m.codes) {
      const list = fwMap.get(code);
      if (list) {
        list.push({
          techniqueId: m.techniqueId,
          relationship: m.relationship,
          notes: m.notes
        });
      }
    }
  }

  // Summary stats
  const totalMappings = mapping.length;
  const techniquesWithMappings = new Set(mapping.map((m) => m.techniqueId)).size;
  const frameworksUsed = new Set(mapping.map((m) => m.frameworkId)).size;

  // State for expanded details
  const container = html`<div></div>`;

  // Framework selector
  let selectedFw = standards.frameworks[0].id;

  function render() {
    container.innerHTML = "";

    // Stats bar
    const statsBar = html`<div style="display: flex; gap: 20px; margin-bottom: 16px; flex-wrap: wrap;">
      <div style="background: #f0f4ff; padding: 10px 16px; border-radius: 6px;">
        <span style="font-size: 20px; font-weight: bold; color: #2563eb;">${techniquesWithMappings}</span>
        <span style="font-size: 13px; color: #666;"> / ${techniques.length} techniques mapped</span>
      </div>
      <div style="background: #f0fdf4; padding: 10px 16px; border-radius: 6px;">
        <span style="font-size: 20px; font-weight: bold; color: #16a34a;">${frameworksUsed}</span>
        <span style="font-size: 13px; color: #666;"> frameworks</span>
      </div>
      <div style="background: #fefce8; padding: 10px 16px; border-radius: 6px;">
        <span style="font-size: 20px; font-weight: bold; color: #ca8a04;">${totalMappings}</span>
        <span style="font-size: 13px; color: #666;"> total mappings</span>
      </div>
    </div>`;

    // Framework tabs
    const tabs = html`<div style="display: flex; gap: 4px; margin-bottom: 16px; flex-wrap: wrap;">
      ${standards.frameworks.map((fw) => {
        const isActive = fw.id === selectedFw;
        const btn = html`<button style="
          padding: 6px 14px; border-radius: 4px; border: 1px solid ${isActive ? "#2563eb" : "#ddd"};
          background: ${isActive ? "#2563eb" : "#fff"}; color: ${isActive ? "#fff" : "#333"};
          cursor: pointer; font-size: 13px; white-space: nowrap;
        ">${fw.name}</button>`;
        btn.onclick = () => { selectedFw = fw.id; render(); };
        return btn;
      })}
    </div>`;

    // Current framework detail
    const fw = standards.frameworks.find((f) => f.id === selectedFw);
    const fwMap = coverageMap.get(selectedFw);

    const fwLink = html`<p style="margin: 0 0 12px 0; font-size: 13px; color: #666;">
      Version ${fw.version} &mdash; <a href="${fw.url}" target="_blank" rel="noopener">${fw.url}</a>
    </p>`;

    // Build table rows
    const rows = [];
    for (const item of fw.structure) {
      if (item.children) {
        // Parent row (GOVERN, MAP, etc.)
        rows.push({ code: item.code, name: item.name, isParent: true, techs: [] });
        for (const child of item.children) {
          const techs = fwMap ? (fwMap.get(child.code) || []) : [];
          rows.push({ code: child.code, name: child.name, isParent: false, techs });
        }
      } else {
        const techs = fwMap ? (fwMap.get(item.code) || []) : [];
        rows.push({ code: item.code, name: item.name, isParent: false, techs });
      }
    }

    const table = html`<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
      <thead>
        <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
          <th style="padding: 8px 12px; text-align: left; width: 100px;">Code</th>
          <th style="padding: 8px 12px; text-align: left;">Requirement</th>
          <th style="padding: 8px 12px; text-align: center; width: 80px;">Count</th>
          <th style="padding: 8px 12px; text-align: left;">Techniques</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map((row) => {
          if (row.isParent) {
            return html`<tr style="background: #e9ecef; border-top: 1px solid #dee2e6;">
              <td style="padding: 8px 12px; font-weight: bold;" colspan="4">${row.code} &mdash; ${row.name}</td>
            </tr>`;
          }
          const count = row.techs.length;
          const bgColor = count === 0 ? "#fff5f5" : "#fff";
          const countColor = count === 0 ? "#dc3545" : "#28a745";
          return html`<tr style="background: ${bgColor}; border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 6px 12px; font-family: monospace; font-size: 12px;">${row.code}</td>
            <td style="padding: 6px 12px;">${row.name}</td>
            <td style="padding: 6px 12px; text-align: center; font-weight: bold; color: ${countColor};">${count}</td>
            <td style="padding: 6px 12px;">
              ${row.techs.length > 0
                ? row.techs.map((t) => {
                    const tech = techLookup.get(t.techniqueId);
                    const cat = tech ? catLookup.get(tech.categoryId) : null;
                    const name = tech ? tech.name : t.techniqueId;
                    const relBadge = relationshipBadge(t.relationship);
                    return html`<span style="display: inline-block; background: #f0f4ff; border: 1px solid #d4e0ff; border-radius: 3px; padding: 2px 6px; margin: 1px 2px; font-size: 11px; white-space: nowrap;" title="${t.notes || ""}">${relBadge} ${name}</span>`;
                  })
                : html`<span style="color: #ccc; font-style: italic;">no coverage</span>`}
            </td>
          </tr>`;
        })}
      </tbody>
    </table>`;

    // Gap analysis summary for this framework
    const allCodes = flattenCodes(fw.structure);
    const covered = allCodes.filter((c) => fwMap && (fwMap.get(c) || []).length > 0).length;
    const gaps = allCodes.length - covered;

    const gapSummary = html`<div style="margin-top: 12px; padding: 10px 16px; background: ${gaps > 0 ? "#fff5f5" : "#f0fdf4"}; border-radius: 6px; font-size: 13px;">
      <strong>Coverage:</strong> ${covered} / ${allCodes.length} controls mapped
      ${gaps > 0
        ? html` &mdash; <span style="color: #dc3545;">${gaps} gap${gaps > 1 ? "s" : ""}</span>`
        : html` &mdash; <span style="color: #16a34a;">full coverage</span>`}
    </div>`;

    container.append(statsBar, tabs, fwLink, table, gapSummary);
  }

  render();
  return container;
}

function flattenCodes(structure) {
  const codes = [];
  for (const item of structure) {
    if (item.children) {
      for (const child of item.children) codes.push(child.code);
    } else {
      codes.push(item.code);
    }
  }
  return codes;
}

function relationshipBadge(rel) {
  const colors = {
    mitigates: "#16a34a",
    addresses: "#2563eb",
    supports: "#ca8a04",
    defends: "#dc2626"
  };
  const color = colors[rel] || "#666";
  return html`<span style="color: ${color}; font-weight: bold; font-size: 10px;">[${(rel || "").charAt(0).toUpperCase()}]</span>`;
}
