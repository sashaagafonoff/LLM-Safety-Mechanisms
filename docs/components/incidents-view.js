// Incident register view: shows safety incidents linked to models and techniques
import {html} from "htl";

export function createIncidentsView(data) {
  const incidents = data.raw.incidents || [];
  const techLookup = new Map(data.raw.techniques.map((t) => [t.id, t]));
  const providerLookup = new Map((data.raw.providers || []).map((p) => [p.id, p]));
  const modelLookup = new Map((data.raw.models || []).map((m) => [m.id, m]));
  const riskLookup = new Map();
  // risk_areas may not be in raw, read from techniques riskAreaIds
  // We'll just display IDs if no lookup available

  if (incidents.length === 0) {
    return html`<div style="padding: 20px; text-align: center; color: #999; background: #f8f9fa; border-radius: 8px;">
      <p style="font-size: 16px; margin-bottom: 8px;">No incidents recorded yet.</p>
      <p style="font-size: 13px;">Add entries to <code>data/incidents.json</code> to populate this view.</p>
    </div>`;
  }

  const severityColors = {
    critical: { bg: "#fef2f2", border: "#fca5a5", text: "#991b1b", badge: "#dc2626" },
    high: { bg: "#fff7ed", border: "#fdba74", text: "#9a3412", badge: "#ea580c" },
    medium: { bg: "#fefce8", border: "#fde047", text: "#854d0e", badge: "#ca8a04" },
    low: { bg: "#f8fafc", border: "#cbd5e1", text: "#475569", badge: "#64748b" }
  };

  const statusBadge = {
    confirmed: { bg: "#fee2e2", text: "#991b1b" },
    alleged: { bg: "#fef3c7", text: "#92400e" },
    disputed: { bg: "#e0e7ff", text: "#3730a3" },
    resolved: { bg: "#d1fae5", text: "#065f46" }
  };

  // Sort by date descending
  const sorted = [...incidents].sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  // Stats
  const bySeverity = {};
  for (const inc of incidents) {
    bySeverity[inc.severity] = (bySeverity[inc.severity] || 0) + 1;
  }

  return html`<div>
    <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
      ${["critical", "high", "medium", "low"].map((sev) => {
        const count = bySeverity[sev] || 0;
        const colors = severityColors[sev];
        return html`<div style="background: ${colors.bg}; border: 1px solid ${colors.border}; padding: 8px 14px; border-radius: 6px; min-width: 100px; text-align: center;">
          <div style="font-size: 20px; font-weight: bold; color: ${colors.badge};">${count}</div>
          <div style="font-size: 12px; color: ${colors.text}; text-transform: capitalize;">${sev}</div>
        </div>`;
      })}
    </div>

    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
      <thead>
        <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
          <th style="padding: 8px 10px; text-align: left; width: 90px;">Date</th>
          <th style="padding: 8px 10px; text-align: left;">Incident</th>
          <th style="padding: 8px 10px; text-align: left; width: 120px;">Provider</th>
          <th style="padding: 8px 10px; text-align: center; width: 80px;">Severity</th>
          <th style="padding: 8px 10px; text-align: center; width: 80px;">Status</th>
        </tr>
      </thead>
      <tbody>
        ${sorted.map((inc) => {
          const sevStyle = severityColors[inc.severity] || severityColors.low;
          const statStyle = statusBadge[inc.status] || statusBadge.alleged;
          const providerNames = (inc.providerIds || []).map((id) => {
            const p = providerLookup.get(id);
            return p ? p.name : id;
          }).join(", ");

          const modelNames = (inc.modelIds || []).map((id) => {
            const m = modelLookup.get(id);
            return m ? m.id : id;
          }).join(", ");

          const techNames = (inc.techniqueIds || []).map((id) => {
            const t = techLookup.get(id);
            return t ? t.name : id;
          });

          return html`<tr style="border-bottom: 1px solid #f0f0f0; vertical-align: top;">
            <td style="padding: 8px 10px; font-family: monospace; font-size: 12px; white-space: nowrap;">${inc.date || "—"}</td>
            <td style="padding: 8px 10px;">
              <details>
                <summary style="cursor: pointer; font-weight: 500;">${inc.title}</summary>
                <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px; font-size: 12px;">
                  ${inc.description ? html`<p style="margin: 0 0 6px 0;">${inc.description}</p>` : ""}
                  ${modelNames ? html`<p style="margin: 0 0 4px 0;"><strong>Models:</strong> ${modelNames}</p>` : ""}
                  ${techNames.length > 0 ? html`<p style="margin: 0 0 4px 0;"><strong>Technique failures:</strong> ${techNames.join(", ")}</p>` : ""}
                  ${(inc.riskAreaIds || []).length > 0 ? html`<p style="margin: 0 0 4px 0;"><strong>Risk areas:</strong> ${inc.riskAreaIds.join(", ")}</p>` : ""}
                  ${(inc.sources || []).length > 0 ? html`<div style="margin-top: 6px;">
                    <strong>Sources:</strong>
                    <ul style="margin: 4px 0 0 0; padding-left: 18px;">
                      ${inc.sources.map((s) => html`<li><a href="${s.url}" target="_blank" rel="noopener">${s.title || s.url}</a> ${s.date ? `(${s.date})` : ""}</li>`)}
                    </ul>
                  </div>` : ""}
                </div>
              </details>
            </td>
            <td style="padding: 8px 10px;">${providerNames || "—"}</td>
            <td style="padding: 8px 10px; text-align: center;">
              <span style="display: inline-block; background: ${sevStyle.bg}; border: 1px solid ${sevStyle.border}; color: ${sevStyle.text}; padding: 2px 8px; border-radius: 3px; font-size: 11px; text-transform: capitalize;">${inc.severity}</span>
            </td>
            <td style="padding: 8px 10px; text-align: center;">
              <span style="display: inline-block; background: ${statStyle.bg}; color: ${statStyle.text}; padding: 2px 8px; border-radius: 3px; font-size: 11px; text-transform: capitalize;">${inc.status}</span>
            </td>
          </tr>`;
        })}
      </tbody>
    </table>
  </div>`;
}
