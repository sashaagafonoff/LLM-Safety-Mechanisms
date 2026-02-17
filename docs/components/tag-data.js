// Data transformation for tagging UI
// Builds a structure optimized for browsing sources and reviewing/adding technique tags

export function buildTaggingDataset(evidenceRaw, techniques, categories, techniqueMap, providers) {
  const sources = Array.isArray(evidenceRaw) ? evidenceRaw : evidenceRaw.sources || [];

  const techById = new Map(techniques.map((t) => [t.id, t]));
  const catById = new Map(categories.map((c) => [c.id, c]));
  const provById = new Map(providers.map((p) => [p.id, p]));

  // Build techniquesByCategory map for dropdowns
  const techniquesByCategory = new Map();
  for (const t of techniques) {
    const cat = catById.get(t.categoryId);
    const catName = cat ? cat.name : "Uncategorized";
    if (!techniquesByCategory.has(catName)) techniquesByCategory.set(catName, []);
    techniquesByCategory.get(catName).push(t);
  }

  // Enrich sources with existing tags from techniqueMap
  const enrichedSources = sources.map((s) => {
    const mappings = techniqueMap[s.id] || [];
    const existingTags = mappings
      .filter((m) => m.active !== false)
      .map((m) => {
        const tech = techById.get(m.techniqueId);
        const cat = tech ? catById.get(tech.categoryId) : null;
        return {
          techniqueId: m.techniqueId,
          techniqueName: tech ? tech.name : m.techniqueId,
          categoryId: tech ? tech.categoryId : null,
          categoryName: cat ? cat.name : "Unknown",
          categoryColor: cat ? cat.color : "#999",
          confidence: m.confidence || "Medium",
          evidence: (m.evidence || []).filter((e) => e.active !== false)
        };
      });

    const prov = provById.get(s.provider);
    return {
      id: s.id,
      title: s.title,
      providerId: s.provider,
      providerName: prov ? prov.name : s.provider,
      url: s.url,
      type: s.type || "",
      dateAdded: s.date_added || "",
      models: s.models || [],
      existingTags,
      tagCount: existingTags.length
    };
  });

  return {
    sources: enrichedSources,
    techniques,
    categories,
    providers,
    techniquesByCategory
  };
}
