// Third-party commentary reference list
import {html} from "htl";

export function createCommentaryView(data) {
  const commentary = data.raw.commentary || [];
  const techniques = data.raw.techniques;
  const techLookup = new Map(techniques.map((t) => [t.id, t]));

  if (commentary.length === 0) {
    return html`<div style="padding: 20px; text-align: center; color: #999; background: #f8f9fa; border-radius: 8px;">
      <p style="font-size: 16px; margin-bottom: 8px;">No third-party commentary entries yet.</p>
      <p style="font-size: 13px;">Add entries to <code>data/commentary.json</code> to populate this view.</p>
    </div>`;
  }

  // Group by technique
  const byTechnique = new Map();
  for (const entry of commentary) {
    for (const techId of entry.techniqueIds || []) {
      if (!byTechnique.has(techId)) byTechnique.set(techId, []);
      byTechnique.get(techId).push(entry);
    }
  }

  // Sort techniques alphabetically by name
  const sortedTechIds = [...byTechnique.keys()].sort((a, b) => {
    const nameA = techLookup.get(a)?.name || a;
    const nameB = techLookup.get(b)?.name || b;
    return nameA.localeCompare(nameB);
  });

  const typeBadgeColors = {
    academic_paper: { bg: "#e0e7ff", text: "#3730a3" },
    blog_post: { bg: "#fef3c7", text: "#92400e" },
    report: { bg: "#d1fae5", text: "#065f46" },
    news: { bg: "#f3e8ff", text: "#6b21a8" },
    audit: { bg: "#fce7f3", text: "#9d174d" }
  };

  const sentimentIcons = {
    positive: { symbol: "+", color: "#16a34a" },
    negative: { symbol: "-", color: "#dc2626" },
    mixed: { symbol: "~", color: "#ca8a04" },
    neutral: { symbol: "=", color: "#6b7280" }
  };

  return html`<div>
    <div style="margin-bottom: 12px; font-size: 13px; color: #666;">
      ${commentary.length} reference${commentary.length !== 1 ? "s" : ""} across ${byTechnique.size} technique${byTechnique.size !== 1 ? "s" : ""}
    </div>
    ${sortedTechIds.map((techId) => {
      const tech = techLookup.get(techId);
      const entries = byTechnique.get(techId);
      return html`<div style="margin-bottom: 16px;">
        <h4 style="margin: 0 0 6px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 4px;">
          ${tech ? tech.name : techId}
          <span style="font-weight: normal; color: #999; font-size: 12px;">(${entries.length})</span>
        </h4>
        ${entries.map((e) => {
          const typeStyle = typeBadgeColors[e.type] || { bg: "#f3f4f6", text: "#374151" };
          const sent = sentimentIcons[e.sentiment] || sentimentIcons.neutral;
          return html`<div style="padding: 6px 0; border-bottom: 1px solid #f8f8f8; font-size: 13px;">
            <a href="${e.url}" target="_blank" rel="noopener" style="font-weight: 500;">${e.title}</a>
            <span style="display: inline-block; background: ${typeStyle.bg}; color: ${typeStyle.text}; padding: 1px 6px; border-radius: 3px; font-size: 11px; margin-left: 6px;">${(e.type || "").replace(/_/g, " ")}</span>
            <span style="color: ${sent.color}; font-weight: bold; margin-left: 4px;" title="Sentiment: ${e.sentiment || "neutral"}">[${sent.symbol}]</span>
            <br>
            <span style="color: #888; font-size: 12px;">
              ${e.author || e.organization ? `${e.author || ""}${e.author && e.organization ? ", " : ""}${e.organization || ""}` : ""}
              ${e.date ? ` &mdash; ${e.date}` : ""}
            </span>
            ${e.summary ? html`<div style="color: #555; font-size: 12px; margin-top: 2px;">${e.summary}</div>` : ""}
          </div>`;
        })}
      </div>`;
    })}
  </div>`;
}
