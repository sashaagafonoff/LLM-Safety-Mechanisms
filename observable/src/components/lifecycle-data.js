// Lifecycle chart: configuration and data preparation
// Ported from Observable notebook cells: lifecycleConfig, lifecycleChartData

export const lifecycleConfig = {
  width: 950,
  height: 850,

  margin: { top: 30, right: 30, bottom: 30, left: 30 },

  governance: {
    top: 40,
    height: 120,
    labelOffsetY: 18
  },

  phases: {
    headerHeight: 44,
    headerRadius: 6,
    columnGap: 12,
    areaTop: 195,
    areaBottom: 680
  },

  harm: {
    top: 705,
    height: 220,
    labelOffsetY: 18
  },

  node: {
    width: 150,
    height: 28,
    radius: 6,
    fontSize: 11,
    padding: { x: 8, y: 6 },
    verticalGap: 6
  },

  connector: {
    strokeWidth: 1.5,
    color: "#90A4AE",
    dashArray: "4,3",
    opacity: 0.6
  },

  phaseColors: {
    "pre-training": "#E8F5E9",
    training: "#E3F2FD",
    evaluation: "#FBE9E7",
    inference: "#F3E5F5",
    monitoring: "#FFF3E0"
  },
  phaseBorderColors: {
    "pre-training": "#66BB6A",
    training: "#42A5F5",
    evaluation: "#EF5350",
    inference: "#AB47BC",
    monitoring: "#FFA726"
  },

  temporalPhaseIds: ["pre-training", "training", "evaluation", "inference", "monitoring"],

  governanceCategoryId: "cat-governance",
  harmCategoryId: "cat-harm-classification",

  spanningTechniques: {
    "tech-configurable-safety": { from: "inference", to: "monitoring" }
  },

  governanceConnectors: [
    { techId: "tech-capability-monitoring", temporalPhase: "evaluation" },
    { techId: "tech-incident-reporting", temporalPhase: "monitoring" }
  ]
};

export function buildLifecycleChartData(data) {
  const cfg = lifecycleConfig;
  const catLookup = new Map(data.categories.map((c) => [c.id, c]));
  const phaseLookup = new Map((data.lifecycle || []).map((p) => [p.id, p]));
  const techniques = data.raw?.techniques || data.techniques || [];

  const techProviders = new Map();
  (data.flatPairs || []).forEach((fp) => {
    if (!techProviders.has(fp.technique)) {
      techProviders.set(fp.technique, new Set());
    }
    techProviders.get(fp.technique).add(fp.provider);
  });

  function enrich(tech) {
    const cat = catLookup.get(tech.categoryId);
    const providers = techProviders.get(tech.name);
    return {
      id: tech.id,
      name: tech.name,
      description: tech.description,
      categoryId: tech.categoryId,
      categoryName: cat?.name || "Other",
      categoryColor: cat?.color || "#999",
      lifecycleStages: tech.lifecycleStages || [],
      providerNames: providers ? [...providers].sort() : []
    };
  }

  const governanceTechniques = [];
  const harmTechniques = [];
  const temporalTechniques = [];

  techniques.forEach((tech) => {
    if (tech.categoryId === cfg.governanceCategoryId) {
      governanceTechniques.push(enrich(tech));
    } else if (tech.categoryId === cfg.harmCategoryId) {
      harmTechniques.push(enrich(tech));
    } else {
      temporalTechniques.push(enrich(tech));
    }
  });

  const usableWidth = cfg.width - cfg.margin.left - cfg.margin.right;
  const columnWidth =
    (usableWidth - cfg.phases.columnGap * (cfg.temporalPhaseIds.length - 1)) /
    cfg.temporalPhaseIds.length;

  const columns = cfg.temporalPhaseIds.map((pid, i) => {
    const phaseDef = phaseLookup.get(pid) || { name: pid, description: "" };
    const x = cfg.margin.left + i * (columnWidth + cfg.phases.columnGap);
    return {
      phaseId: pid,
      phaseName: phaseDef.name,
      phaseDescription: phaseDef.description,
      x,
      width: columnWidth,
      centerX: x + columnWidth / 2
    };
  });

  const columnLookup = new Map(columns.map((c) => [c.phaseId, c]));

  const spanningIds = new Set(Object.keys(cfg.spanningTechniques));

  const phaseGroups = new Map();
  cfg.temporalPhaseIds.forEach((pid) => phaseGroups.set(pid, []));

  const spanningNodes = [];

  temporalTechniques.forEach((tech) => {
    if (spanningIds.has(tech.id)) {
      spanningNodes.push(tech);
      return;
    }
    const primary = (tech.lifecycleStages || []).find((s) => cfg.temporalPhaseIds.includes(s));
    if (primary) {
      phaseGroups.get(primary)?.push(tech);
    }
  });

  const govConnectorIds = new Set(cfg.governanceConnectors.map((gc) => gc.techId));
  govConnectorIds.forEach((techId) => {
    const tech = governanceTechniques.find((t) => t.id === techId);
    const connector = cfg.governanceConnectors.find((gc) => gc.techId === techId);
    if (tech && connector) {
      phaseGroups.get(connector.temporalPhase)?.push({ ...tech, _isEcho: true });
    }
  });

  const nodePositions = new Map();

  columns.forEach((col) => {
    const techs = phaseGroups.get(col.phaseId) || [];
    techs.sort((a, b) => {
      if (a._isEcho !== b._isEcho) return a._isEcho ? 1 : -1;
      const catCmp = a.categoryName.localeCompare(b.categoryName);
      return catCmp !== 0 ? catCmp : a.name.localeCompare(b.name);
    });

    let yOffset = cfg.phases.areaTop + cfg.phases.headerHeight + 16;
    techs.forEach((tech) => {
      const nodeX = col.x + (col.width - cfg.node.width) / 2;
      const posKey = tech._isEcho ? `${tech.id}__temporal` : tech.id;
      nodePositions.set(posKey, {
        x: nodeX,
        y: yOffset,
        cx: nodeX + cfg.node.width / 2,
        cy: yOffset + cfg.node.height / 2,
        width: cfg.node.width,
        height: cfg.node.height,
        phaseId: col.phaseId
      });
      yOffset += cfg.node.height + cfg.node.verticalGap;
    });

    col.techniques = techs;
    col.contentBottom = yOffset;
  });

  const spanningPositions = [];

  spanningNodes.forEach((tech) => {
    const spanDef = cfg.spanningTechniques[tech.id];
    if (!spanDef) return;
    const fromCol = columnLookup.get(spanDef.from);
    const toCol = columnLookup.get(spanDef.to);
    if (!fromCol || !toCol) return;

    const yOffset = Math.max(
      columns.find((c) => c.phaseId === spanDef.from)?.contentBottom || 0,
      columns.find((c) => c.phaseId === spanDef.to)?.contentBottom || 0
    );

    const spanX = fromCol.x + (fromCol.width - cfg.node.width) / 2;
    const spanWidth = toCol.x + toCol.width / 2 + cfg.node.width / 2 - spanX;

    spanningPositions.push({
      tech,
      x: spanX,
      y: yOffset,
      cx: spanX + spanWidth / 2,
      cy: yOffset + cfg.node.height / 2,
      width: spanWidth,
      height: cfg.node.height,
      fromPhase: spanDef.from,
      toPhase: spanDef.to
    });
  });

  governanceTechniques.sort((a, b) => a.name.localeCompare(b.name));

  const govStartY = cfg.governance.top + cfg.governance.labelOffsetY + 20;
  const govNodeWidth = cfg.node.width;
  const govNodesPerRow = Math.floor(
    (usableWidth + cfg.phases.columnGap) / (govNodeWidth + cfg.phases.columnGap)
  );

  const govPositions = new Map();

  governanceTechniques.forEach((tech, i) => {
    const row = Math.floor(i / govNodesPerRow);
    const col = i % govNodesPerRow;
    const itemsInRow = Math.min(govNodesPerRow, governanceTechniques.length - row * govNodesPerRow);
    const totalRowWidth = itemsInRow * (govNodeWidth + cfg.phases.columnGap) - cfg.phases.columnGap;
    const rowStartX = cfg.margin.left + (usableWidth - totalRowWidth) / 2;

    const nodeX = rowStartX + col * (govNodeWidth + cfg.phases.columnGap);
    const nodeY = govStartY + row * (cfg.node.height + cfg.node.verticalGap);

    govPositions.set(tech.id, {
      x: nodeX,
      y: nodeY,
      cx: nodeX + govNodeWidth / 2,
      cy: nodeY + cfg.node.height / 2,
      width: govNodeWidth,
      height: cfg.node.height
    });
  });

  harmTechniques.sort((a, b) => a.name.localeCompare(b.name));

  const harmStartY = cfg.harm.top + cfg.harm.labelOffsetY + 20;
  const harmNodeWidth = cfg.node.width;
  const harmNodesPerRow = Math.floor(
    (usableWidth + cfg.phases.columnGap) / (harmNodeWidth + cfg.phases.columnGap)
  );

  const harmPositions = new Map();

  harmTechniques.forEach((tech, i) => {
    const row = Math.floor(i / harmNodesPerRow);
    const col = i % harmNodesPerRow;
    const itemsInRow = Math.min(harmNodesPerRow, harmTechniques.length - row * harmNodesPerRow);
    const totalRowWidth = itemsInRow * (harmNodeWidth + cfg.phases.columnGap) - cfg.phases.columnGap;
    const rowStartX = cfg.margin.left + (usableWidth - totalRowWidth) / 2;

    const nodeX = rowStartX + col * (harmNodeWidth + cfg.phases.columnGap);
    const nodeY = harmStartY + row * (cfg.node.height + cfg.node.verticalGap);

    harmPositions.set(tech.id, {
      x: nodeX,
      y: nodeY,
      cx: nodeX + harmNodeWidth / 2,
      cy: nodeY + cfg.node.height / 2,
      width: harmNodeWidth,
      height: cfg.node.height
    });
  });

  const connectors = [];
  cfg.governanceConnectors.forEach((gc) => {
    const govPos = govPositions.get(gc.techId);
    const tempPos = nodePositions.get(`${gc.techId}__temporal`);
    if (govPos && tempPos) {
      const tech = governanceTechniques.find((t) => t.id === gc.techId);
      connectors.push({
        techId: gc.techId,
        techName: tech?.name || gc.techId,
        categoryColor: tech?.categoryColor || "#999",
        govPos,
        tempPos
      });
    }
  });

  const allProviders = [...new Set(data.flatPairs?.map((fp) => fp.provider) || [])].sort();

  return {
    columns,
    columnLookup,
    governanceTechniques,
    harmTechniques,
    spanningPositions,
    nodePositions,
    govPositions,
    harmPositions,
    connectors,
    allProviders,
    allTechniques: techniques,
    techProviders
  };
}
