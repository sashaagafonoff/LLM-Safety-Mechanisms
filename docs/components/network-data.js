// Network graph: config, data building, positioning, auto-layout, and layout validation
// Ported from Observable notebook cells: networkConfig, networkGraph, positionedGraph,
// autoLayout, validatedLayout

export const networkConfig = {
  width: 1000,
  height: 1000,
  centerX: 400,
  centerY: 350,
  providerRadius: 100,
  modelRadius: 200,
  evidenceRadius: 300,
  nodeRadius: {
    provider: 20,
    model: 8
  },
  evidenceRect: {
    width: 14,
    height: 24
  },
  colors: {
    model: "#457b9d",
    evidence: "#e9ecef",
    evidenceBorder: "#adb5bd"
  },
  linkColors: {
    owns: "#888",
    documents: "#888"
  }
};

export const NETWORK_LAYOUT_STORAGE_KEY = "network-graph-layout-v1";

export function buildNetworkGraph(data) {
  const nodes = [];
  const links = [];
  const nodeSet = new Set();

  const modelsWithEvidence = new Set();
  const evidenceWithModels = new Set();

  data.raw.evidence.forEach((source) => {
    if (source.models && source.models.length > 0) {
      source.models.forEach((m) => {
        modelsWithEvidence.add(m.modelId);
      });
      evidenceWithModels.add(source.id || source.title.replace(/[^a-zA-Z0-9]/g, "-"));
    }
  });

  const providerIdToName = new Map(data.raw.providers.map((p) => [p.id, p.name]));

  data.raw.providers.forEach((provider) => {
    const nodeId = `provider:${provider.id}`;
    if (!nodeSet.has(nodeId)) {
      nodeSet.add(nodeId);
      nodes.push({
        id: nodeId,
        label: provider.name,
        type: "provider",
        providerId: provider.id,
        providerName: provider.name,
        headquarters: provider.headquarters,
        providerType: provider.type
      });
    }
  });

  const modelMap = new Map();
  data.raw.evidence.forEach((source) => {
    if (source.models && source.models.length > 0) {
      source.models.forEach((m) => {
        if (!modelMap.has(m.modelId)) {
          modelMap.set(m.modelId, {
            name: m.name || m.modelId,
            providerId: source.provider,
            providerName: providerIdToName.get(source.provider)
          });
        }
      });
    }
  });

  modelMap.forEach((info, modelId) => {
    const nodeId = `model:${modelId}`;
    if (!nodeSet.has(nodeId)) {
      nodeSet.add(nodeId);
      nodes.push({
        id: nodeId,
        label: info.name,
        type: "model",
        providerId: info.providerId,
        providerName: info.providerName,
        isOrphan: !modelsWithEvidence.has(modelId)
      });
      const providerNodeId = `provider:${info.providerId}`;
      if (nodeSet.has(providerNodeId)) {
        links.push({ source: providerNodeId, target: nodeId, type: "owns" });
      }
    }
  });

  data.raw.evidence.forEach((source) => {
    const evidenceId = `evidence:${source.id || source.title.replace(/[^a-zA-Z0-9]/g, "-")}`;
    const hasValidModels = source.models && source.models.length > 0;

    if (!nodeSet.has(evidenceId)) {
      nodeSet.add(evidenceId);
      nodes.push({
        id: evidenceId,
        label: source.title,
        type: "evidence",
        docType: source.type,
        providerId: source.provider,
        providerName: providerIdToName.get(source.provider),
        url: source.url,
        modelCount: source.models ? source.models.length : 0,
        isOrphan: !hasValidModels
      });
    }

    if (hasValidModels) {
      source.models.forEach((m) => {
        const modelNodeId = `model:${m.modelId}`;
        if (nodeSet.has(modelNodeId)) {
          links.push({ source: evidenceId, target: modelNodeId, type: "documents" });
        }
      });
    }
  });

  return { nodes, links };
}

export function positionGraph(networkGraph, validatedLayout, config, d3) {
  const { nodes, links } = networkGraph;
  const { layout, source, stats } = validatedLayout;
  const { centerX, centerY, providerRadius, modelRadius, evidenceRadius } = config;

  const providers = nodes.filter((n) => n.type === "provider");
  const models = nodes.filter((n) => n.type === "model");
  const evidence = nodes.filter((n) => n.type === "evidence");

  const providerAngles = new Map();
  const angleStep = (2 * Math.PI) / providers.length;
  providers.forEach((p, i) => {
    const angle = i * angleStep - Math.PI / 2;
    providerAngles.set(p.providerId, angle);
    p.angle = angle;
    p.x = centerX + providerRadius * Math.cos(angle);
    p.y = centerY + providerRadius * Math.sin(angle);
  });

  const modelsByProvider = d3.group(models, (d) => d.providerId);
  modelsByProvider.forEach((providerModels, providerId) => {
    const providerAngle = providerAngles.get(providerId);
    if (providerAngle === undefined) return;
    const arcSpread = angleStep * 0.7;
    const modelAngleStep = providerModels.length > 1 ? arcSpread / (providerModels.length - 1) : 0;
    const startAngle = providerAngle - arcSpread / 2;
    providerModels.forEach((m, i) => {
      const angle = providerModels.length > 1 ? startAngle + i * modelAngleStep : providerAngle;
      m.angle = angle;
      m.x = centerX + modelRadius * Math.cos(angle);
      m.y = centerY + modelRadius * Math.sin(angle);
    });
  });

  const evidenceByProvider = d3.group(evidence, (d) => d.providerId);
  evidenceByProvider.forEach((providerEvidence, providerId) => {
    const providerAngle = providerAngles.get(providerId);
    if (providerAngle === undefined) return;
    const arcSpread = angleStep * 0.8;
    const evidenceAngleStep = providerEvidence.length > 1 ? arcSpread / (providerEvidence.length - 1) : 0;
    const startAngle = providerAngle - arcSpread / 2;
    providerEvidence.forEach((e, i) => {
      const angle = providerEvidence.length > 1 ? startAngle + i * evidenceAngleStep : providerAngle;
      e.angle = angle;
      e.x = centerX + evidenceRadius * Math.cos(angle);
      e.y = centerY + evidenceRadius * Math.sin(angle);
    });
  });

  let applied = 0;
  if (layout) {
    nodes.forEach((n) => {
      const saved = layout[n.id];
      if (saved && typeof saved.x === "number" && typeof saved.y === "number" && isFinite(saved.x) && isFinite(saved.y)) {
        n.x = saved.x;
        n.y = saved.y;
        applied++;
      }
    });
    stats.applied = applied;
  }

  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  const resolvedLinks = links
    .map((l) => ({
      source: nodeById.get(l.source) || l.source,
      target: nodeById.get(l.target) || l.target,
      type: l.type
    }))
    .filter(
      (l) => l.source && l.target && typeof l.source.x === "number" && typeof l.target.x === "number"
    );

  const orphanModels = models.filter((m) => m.isOrphan).length;
  const orphanEvidence = evidence.filter((e) => e.isOrphan).length;

  return { nodes, providers, models, evidence, resolvedLinks, nodeById, orphanModels, orphanEvidence };
}

export function computeAutoLayout(networkGraph, config, d3) {
  const { nodes, links } = networkGraph;
  const { width, height, nodeRadius, evidenceRect } = config;

  const providers = nodes.filter((n) => n.type === "provider");
  const models = nodes.filter((n) => n.type === "model");
  const evidence = nodes.filter((n) => n.type === "evidence");

  const modelsByProvider = d3.group(models, (d) => d.providerId);
  const evidenceByProvider = d3.group(evidence, (d) => d.providerId);

  const providerGroups = providers.map((p) => {
    const pModels = modelsByProvider.get(p.providerId) || [];
    const pEvidence = evidenceByProvider.get(p.providerId) || [];
    const rowCount = Math.max(pModels.length, pEvidence.length, 1);
    return { provider: p, models: pModels, evidence: pEvidence, rowCount };
  });

  const groupGapY = 25;
  const modelRowHeight = 22;
  const evidenceRowHeight = 24;
  const groupPaddingY = 8;
  const colGap = 40;
  const providerColX = 0;
  const modelColX = 70;
  const evidenceColX = 190;
  const groupWidth = 460;

  providerGroups.forEach((g) => {
    const modelHeight = g.models.length * modelRowHeight;
    const evidenceHeight = g.evidence.length * evidenceRowHeight;
    g.height = Math.max(modelHeight, evidenceHeight, modelRowHeight) + groupPaddingY * 2;
  });

  const sorted = [...providerGroups].sort((a, b) => b.height - a.height);

  const col1Groups = [];
  const col2Groups = [];
  let col1Height = 0;
  let col2Height = 0;

  for (const g of sorted) {
    const h1 = col1Height + (col1Groups.length > 0 ? groupGapY : 0) + g.height;
    const h2 = col2Height + (col2Groups.length > 0 ? groupGapY : 0) + g.height;
    if (h1 <= h2) {
      col1Groups.push(g);
      col1Height = h1;
    } else {
      col2Groups.push(g);
      col2Height = h2;
    }
  }

  col1Groups.sort((a, b) => b.rowCount - a.rowCount);
  col2Groups.sort((a, b) => b.rowCount - a.rowCount);

  const col1TotalHeight = col1Groups.reduce((sum, g, i) => sum + g.height + (i > 0 ? groupGapY : 0), 0);
  const col2TotalHeight = col2Groups.reduce((sum, g, i) => sum + g.height + (i > 0 ? groupGapY : 0), 0);

  const totalWidth = groupWidth * 2 + colGap;
  const startX = (width - totalWidth) / 2;
  const col1X = startX;
  const col2X = startX + groupWidth + colGap;

  function layoutColumn(groups, baseX, totalH) {
    let y = (height - totalH) / 2;

    groups.forEach((g) => {
      const { provider, models: pModels, evidence: pEvidence } = g;

      const groupCenterY = y + g.height / 2;
      provider.x = baseX + providerColX;
      provider.y = groupCenterY;
      provider.labelAnchor = "end";

      const modelBlockHeight = pModels.length * modelRowHeight;
      const modelStartY = y + (g.height - modelBlockHeight) / 2 + modelRowHeight / 2;
      pModels.forEach((m, i) => {
        m.x = baseX + modelColX;
        m.y = modelStartY + i * modelRowHeight;
        m.labelAnchor = "end";
      });

      const evidenceBlockHeight = pEvidence.length * evidenceRowHeight;
      const evidenceStartY = y + (g.height - evidenceBlockHeight) / 2 + evidenceRowHeight / 2;
      pEvidence.forEach((e, i) => {
        e.x = baseX + evidenceColX;
        e.y = evidenceStartY + i * evidenceRowHeight;
        e.labelAnchor = "start";
      });

      y += g.height + groupGapY;
    });
  }

  layoutColumn(col1Groups, col1X, col1TotalHeight);
  layoutColumn(col2Groups, col2X, col2TotalHeight);

  const layout = {};
  nodes.forEach((n) => {
    layout[n.id] = { x: n.x, y: n.y };
  });

  return layout;
}

export function validateNetworkLayout(networkGraph, defaultLayout) {
  const { nodes } = networkGraph;
  const liveNodeIds = new Set(nodes.map((n) => n.id));

  let layout = null;
  let source = "default";
  let stats = { applied: 0, stale: 0, newNodes: 0 };

  try {
    const saved = localStorage.getItem(NETWORK_LAYOUT_STORAGE_KEY);
    if (saved) {
      layout = JSON.parse(saved);
      source = "saved";
    }
  } catch (e) {
    console.warn("Could not load saved layout:", e);
  }

  if (!layout && defaultLayout) {
    layout = JSON.parse(JSON.stringify(defaultLayout));
    source = "attached";
  }

  if (layout) {
    const staleIds = Object.keys(layout).filter((id) => !liveNodeIds.has(id));
    staleIds.forEach((id) => delete layout[id]);
    stats.stale = staleIds.length;

    const savedIds = new Set(Object.keys(layout));
    const newNodeIds = nodes.filter((n) => !savedIds.has(n.id)).map((n) => n.id);
    stats.newNodes = newNodeIds.length;
  }

  return { layout, source, stats };
}
