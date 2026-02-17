// Data pipeline: builds enriched dataset and applies filters
// Ported from Observable notebook cells: `data`, `filteredData`

export function buildDataset(evidenceRaw, techniques, categories, techniqueMap, models, providers, lifecycle) {
  // Unwrap: evidence.json is { "sources": [...] }
  const evidence = Array.isArray(evidenceRaw) ? evidenceRaw : evidenceRaw.sources || [];

  // 1. Lookup Maps
  const techLookup = new Map(techniques.map((t) => [t.id, t]));
  const catLookup = new Map(categories.map((c) => [c.id, c]));

  // 2. Hydrate & Flatten
  const flatPairs = evidence.flatMap((source) => {
    let detections = [];

    if (source.id && techniqueMap[source.id]) {
      detections = techniqueMap[source.id];
    } else if (source.url && source.url !== "<missing>" && techniqueMap[source.url]) {
      detections = techniqueMap[source.url];
    } else if (techniqueMap[source.title]) {
      detections = techniqueMap[source.title];
    }

    const modelString =
      source.models && source.models.length > 0
        ? source.models.map((m) => m.modelId).join(", ")
        : source.title;

    return detections
      .map((d) => {
        const def = techLookup.get(d.techniqueId);
        if (!def) return null;
        return {
          provider: source.provider || "Unknown",
          model: modelString,
          technique: def.name,
          category: catLookup.get(def.categoryId)?.name || "Uncategorized",
          confidence: d.confidence,
          source: source.title,
          source_uri: source.url,
          evidence: d.evidence
        };
      })
      .filter((t) => t !== null);
  });

  // 3. Enriched Models
  const enrichedModels = evidence.map((source) => {
    const sourcePairs = flatPairs.filter((p) => p.source === source.title);
    const techniquesList = sourcePairs.map((p) => {
      const techDef = techniques.find((t) => t.name === p.technique);
      return {
        id: techDef?.id,
        name: p.technique,
        category: p.category,
        categoryId: techDef?.categoryId,
        confidence: p.confidence,
        evidence: p.evidence
      };
    });
    return {
      ...source,
      id:
        source.models && source.models.length > 0
          ? source.models[0].modelId
          : source.title.replace(/[^a-zA-Z0-9-_]/g, ""),
      techniqueCount: techniquesList.length,
      techniques: techniquesList
    };
  });

  return {
    raw: { evidence, techniques, categories, techniqueMap, models, providers, lifecycle },
    enrichedModels,
    flatPairs,
    categories,
    techniques,
    lifecycle
  };
}

export function applyFilters(dataOrPairs, filters) {
  // Accept either the full dataset object or a flat array
  const flatPairs = Array.isArray(dataOrPairs) ? dataOrPairs : dataOrPairs?.flatPairs || [];
  if (!flatPairs || flatPairs.length === 0) return [];

  let filtered = [...flatPairs];
  const confidenceScore = { High: 3, Medium: 2, Low: 1, Unknown: 0 };

  try {
    if (filters && filters.providers && filters.providers.length > 0) {
      filtered = filtered.filter((d) => filters.providers.includes(d.provider));
    }

    if (filters && filters.categories && filters.categories.length > 0) {
      filtered = filtered.filter((d) => filters.categories.includes(d.category));
    }

    if (filters && filters.techniques && filters.techniques.length > 0) {
      filtered = filtered.filter((d) => filters.techniques.includes(d.technique));
    }

    if (filters && filters.rating && filters.rating > 0) {
      filtered = filtered.filter(
        (d) => (confidenceScore[d.confidence] || 0) >= filters.rating
      );
    }

    if (filters && filters.search && filters.search !== "") {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter((d) => {
        const inModel = d.model && d.model.toLowerCase().includes(searchTerm);
        const inProvider = d.provider && d.provider.toLowerCase().includes(searchTerm);
        const inTechnique = d.technique && d.technique.toLowerCase().includes(searchTerm);
        const inCategory = d.category && d.category.toLowerCase().includes(searchTerm);
        const inEvidence = d.evidence && d.evidence.some((txt) => txt.toLowerCase().includes(searchTerm));
        return inModel || inProvider || inTechnique || inCategory || inEvidence;
      });
    }

    return filtered;
  } catch (error) {
    console.error("Error in filtering:", error);
    return flatPairs;
  }
}
