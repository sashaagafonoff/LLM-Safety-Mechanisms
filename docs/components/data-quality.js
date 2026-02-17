// Data quality report component
// Ported from Observable notebook cell: excludedDataSummary
import {html} from "htl";

export function createDataQualityReport(data, providerColors) {
  const exclusions = {
    missingProvider: [],
    missingTechnique: [],
    orphanedModelRefs: [],
    missingCategory: []
  };

  const techIds = new Set(data.raw.techniques.map((t) => t.id));
  const catIds = new Set(data.raw.categories.map((c) => c.id));

  const providerIds = new Set(
    data.raw.providers
      ? data.raw.providers.map((p) => p.id)
      : Object.keys(providerColors || {})
  );

  Object.values(data.raw.techniqueMap)
    .flat()
    .forEach((d) => {
      if (!techIds.has(d.techniqueId)) {
        exclusions.missingTechnique.push({ _techniqueId: d.techniqueId });
      }
    });

  data.raw.techniques.forEach((t) => {
    if (!catIds.has(t.categoryId)) {
      exclusions.missingCategory.push({ _categoryId: t.categoryId });
    }
  });

  data.raw.evidence.forEach((s) => {
    if (s.provider) {
      const isKnown = [...providerIds].some(
        (id) => id.toLowerCase() === s.provider.toLowerCase()
      );
      if (!isKnown) {
        exclusions.missingProvider.push({ _providerId: s.provider });
      }
    }
  });

  if (data.raw.models && Array.isArray(data.raw.models)) {
    const knownModelIds = new Set(data.raw.models.map((m) => m.id));

    data.raw.evidence.forEach((s) => {
      if (s.models) {
        s.models.forEach((m) => {
          if (!knownModelIds.has(m.modelId)) {
            exclusions.orphanedModelRefs.push({ _modelId: m.modelId });
          }
        });
      }
    });
  }

  const modelsWithoutTechniques = new Set();
  if (data.raw.models && Array.isArray(data.raw.models)) {
    const modelsWithTechniques = new Set();

    data.flatPairs.forEach((pair) => {
      if (pair.model) {
        pair.model.split(", ").forEach((modelId) => {
          modelsWithTechniques.add(modelId.trim());
        });
      }
    });

    data.raw.models.forEach((m) => {
      if (!modelsWithTechniques.has(m.id)) {
        modelsWithoutTechniques.add(m.id);
      }
    });
  }

  const uniqueMissingProviders = new Set(exclusions.missingProvider.map((item) => item._providerId));
  const uniqueOrphanedModels = new Set(exclusions.orphanedModelRefs.map((item) => item._modelId));

  return html`<div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
    <h3 style="color: #856404; margin-top: 0;">Data Quality Report</h3>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #28a745;">${data.flatPairs.length}</div>
        <div style="font-size: 14px; color: #666;">Valid Technique Mappings</div>
      </div>

      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: ${uniqueMissingProviders.size > 0 ? "#dc3545" : "#28a745"};">${uniqueMissingProviders.size}</div>
        <div style="font-size: 14px; color: #666;">Orphaned Provider IDs</div>
      </div>

      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: ${uniqueOrphanedModels.size > 0 ? "#dc3545" : "#28a745"};">${uniqueOrphanedModels.size}</div>
        <div style="font-size: 14px; color: #666;">Orphaned Model IDs</div>
      </div>

      <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: ${modelsWithoutTechniques.size > 0 ? "#ffc107" : "#28a745"};">${modelsWithoutTechniques.size}</div>
        <div style="font-size: 14px; color: #666;">Models Without Techniques</div>
      </div>
    </div>

    <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
      <h4 style="margin-top: 0; color: #495057;">Definitions</h4>
      <ul style="margin: 0; padding-left: 20px; color: #6c757d; font-size: 13px;">
        <li><strong>Orphaned Provider IDs:</strong> Provider IDs referenced in evidence.json but not defined in providers.json</li>
        <li><strong>Orphaned Model IDs:</strong> Model IDs referenced in evidence.json but not defined in models.json</li>
        <li><strong>Models Without Techniques:</strong> Models defined in models.json but with no safety techniques detected or mapped</li>
      </ul>
    </div>

    ${uniqueMissingProviders.size > 0 ? html`
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">Orphaned Provider IDs (${uniqueMissingProviders.size})</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
            These provider IDs appear in evidence.json but are not defined in providers.json.
          </div>
          ${[...uniqueMissingProviders].map((id) =>
            html`<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px;">${id}</code>`
          )}
        </div>
      </details>` : ""}

    ${uniqueOrphanedModels.size > 0 ? html`
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">Orphaned Model IDs (${uniqueOrphanedModels.size})</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
            These model IDs appear in evidence.json but are not defined in models.json.
          </div>
          ${[...uniqueOrphanedModels].map((id) =>
            html`<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px;">${id}</code>`
          )}
        </div>
      </details>` : ""}

    ${modelsWithoutTechniques.size > 0 ? html`
      <details style="margin-bottom: 15px;">
        <summary style="cursor: pointer; font-weight: bold; color: #856404;">Models Without Techniques (${modelsWithoutTechniques.size})</summary>
        <div style="margin-top: 10px; background: white; padding: 10px; border-radius: 4px;">
          <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
            These models are defined in models.json but have no safety techniques mapped.
          </div>
          ${[...modelsWithoutTechniques].map((id) =>
            html`<code style="background: #f8f9fa; padding: 2px 4px; margin: 2px;">${id}</code>`
          )}
        </div>
      </details>` : ""}
  </div>`;
}
