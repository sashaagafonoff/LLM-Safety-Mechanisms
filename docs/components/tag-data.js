// Data layer for the Tag & Review tool
// Fetches all JSON data from GitHub, normalizes technique map keys, and provides flat text access

const GH_RAW = "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data";

function fetchJson(name) {
  return fetch(`${GH_RAW}/${name}`).then(r => {
    if (!r.ok) throw new Error(`Failed to load ${name}`);
    return r.json();
  });
}

/**
 * Fetch flat text for a document by evidence ID.
 * Returns the raw text string, or null if not found.
 */
export async function fetchFlatText(docId) {
  const url = `${GH_RAW}/flat_text/${encodeURIComponent(docId)}.txt`;
  const r = await fetch(url);
  if (!r.ok) return null;
  return r.text();
}

/**
 * Load and normalize all tag data.
 * Returns { sources, techniques, categories, providers,
 *           normalizedMap, techById, catById, provById, techByCategory }
 */
export async function loadTagData() {
  const [evidenceRaw, techniques, categories, techniqueMap, providers] = await Promise.all([
    fetchJson("evidence.json"),
    fetchJson("techniques.json"),
    fetchJson("categories.json"),
    fetchJson("model_technique_map.json"),
    fetchJson("providers.json")
  ]);

  const sources = Array.isArray(evidenceRaw) ? evidenceRaw : evidenceRaw.sources || [];

  // Lookup maps
  const techById = new Map(techniques.map(t => [t.id, t]));
  const catById = new Map(categories.map(c => [c.id, c]));
  const provById = new Map(providers.map(p => [p.id, p]));

  // Techniques grouped by category
  const techByCategory = new Map();
  for (const t of techniques) {
    const cat = catById.get(t.categoryId);
    const catName = cat ? cat.name : "Uncategorized";
    if (!techByCategory.has(catName)) techByCategory.set(catName, []);
    techByCategory.get(catName).push(t);
  }

  // --- Normalize technique map keys to evidence IDs ---
  const urlToEvidenceId = new Map();
  const titleToEvidenceId = new Map();
  const evidenceIdSet = new Set();
  for (const doc of sources) {
    evidenceIdSet.add(doc.id);
    if (doc.url) urlToEvidenceId.set(doc.url, doc.id);
    if (doc.title) titleToEvidenceId.set(doc.title, doc.id);
  }

  function resolveMapKey(key) {
    if (evidenceIdSet.has(key)) return key;
    if (urlToEvidenceId.has(key)) return urlToEvidenceId.get(key);
    if (titleToEvidenceId.has(key)) return titleToEvidenceId.get(key);
    return key; // orphan — keep as-is
  }

  const normalizedMap = {};
  for (const [key, value] of Object.entries(techniqueMap)) {
    const resolved = resolveMapKey(key);
    // Merge if key already exists (e.g. both ID and URL entries for same doc)
    if (normalizedMap[resolved]) {
      const existing = new Set(normalizedMap[resolved].map(t => t.techniqueId));
      value.forEach(entry => {
        if (!existing.has(entry.techniqueId)) {
          normalizedMap[resolved].push(entry);
        }
      });
    } else {
      normalizedMap[resolved] = value;
    }
  }

  return {
    sources,
    techniques,
    categories,
    providers,
    normalizedMap,
    techById,
    catById,
    provById,
    techByCategory
  };
}
