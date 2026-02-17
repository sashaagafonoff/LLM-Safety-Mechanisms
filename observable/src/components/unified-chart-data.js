// Unified chart: config, data building, layout algorithms, and layout validation
// Ported from Observable notebook cells: unifiedChartConfig, unifiedChartData,
// unifiedChartLayouts, unifiedChartValidatedLayout

export const unifiedChartConfig = {
  width: 1100,
  height: 900,

  techniqueSpacingY: 22,
  techniqueSymbolSize: 150,

  categoryPadding: 15,
  categoryRadius: 8,
  categoryMinWidth: 120,
  categoryHeight: 35,
  categoryTechGap: 20,
  categoryGroupGap: 30,

  providerRadius: 10,
  providerSpacing: 30,

  labelFontSize: "12px",
  categoryFontSize: "14px",
  labelBgOpacity: 0.6,
  labelPadding: 4,
  labelOffset: 15,

  nodeMargins: { left: 80, right: 80, top: 60, bottom: 80 },

  sequentialColumns: {
    category: 0.12,
    technique: 0.45,
    provider: 0.82
  },

  force: {
    linkDistanceProviderTechnique: 120,
    linkDistanceCategoryTechnique: 40,
    linkStrengthProviderTechnique: 0.2,
    linkStrengthCategoryTechnique: 0.6,
    chargeProvider: -60,
    chargeTechnique: -25,
    chargeCategory: 0,
    collideProvider: 20,
    collideTechnique: 10,
    alphaDecay: 0.03,
    velocityDecay: 0.4
  }
};

export const UNIFIED_LAYOUT_STORAGE_KEY = "unified-chart-layout-v1";

export function buildUnifiedChartData(data, filteredData, categoryColors, providerColors, d3) {
  const config = unifiedChartConfig;

  function getProviderColor(providerName) {
    if (!providerName) return "#999";
    if (providerColors[providerName]) return providerColors[providerName];
    const keys = Object.keys(providerColors);
    const match = keys.find((k) => k.toLowerCase() === providerName.toLowerCase());
    return match ? providerColors[match] : "#999";
  }

  function darkenColor(hex, amount = 40) {
    const num = parseInt(hex.replace("#", ""), 16);
    const r = Math.max(0, (num >> 16) - amount);
    const g = Math.max(0, ((num >> 8) & 0x00ff) - amount);
    const b = Math.max(0, (num & 0x0000ff) - amount);
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
  }

  const catLookup = new Map(data.categories.map((c) => [c.id, c.name]));

  const allTechniquesByCategory = new Map();
  data.techniques.forEach((t) => {
    const catName = catLookup.get(t.categoryId) || "Uncategorized";
    if (!allTechniquesByCategory.has(catName)) {
      allTechniquesByCategory.set(catName, []);
    }
    allTechniquesByCategory.get(catName).push(t.name);
  });

  allTechniquesByCategory.forEach((techs, cat) => {
    allTechniquesByCategory.set(cat, [...new Set(techs)].sort());
  });

  const allCategories = [...allTechniquesByCategory.keys()].sort();

  const selectedProviders = [...new Set(filteredData.map((d) => d.provider))].sort();

  const evidenceLookup = {};
  filteredData.forEach((evidence) => {
    const { provider, category, technique } = evidence;
    if (!evidenceLookup[provider]) evidenceLookup[provider] = {};
    if (!evidenceLookup[provider][category]) evidenceLookup[provider][category] = {};
    if (!evidenceLookup[provider][category][technique]) {
      evidenceLookup[provider][category][technique] = [];
    }
    evidenceLookup[provider][category][technique].push({
      ...evidence,
      evidenceTexts: Array.isArray(evidence.evidence)
        ? evidence.evidence.map((e) =>
            typeof e === "string" ? e : e.text || e.snippet || JSON.stringify(e)
          )
        : evidence.evidence
        ? [typeof evidence.evidence === "string" ? evidence.evidence : JSON.stringify(evidence.evidence)]
        : []
    });
  });

  const categoryGroups = allCategories.map((cat) => {
    const techniques = allTechniquesByCategory.get(cat) || [];
    const groupHeight =
      config.categoryHeight + config.categoryTechGap + techniques.length * config.techniqueSpacingY;
    return { name: cat, techniques, groupHeight };
  });

  function measureText(text, fontSize = "14px", fontWeight = "bold") {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    context.font = `${fontWeight} ${fontSize} sans-serif`;
    return context.measureText(text).width;
  }

  const nodes = [];
  const links = [];
  const nodeById = new Map();

  selectedProviders.forEach((provider) => {
    const node = {
      id: `provider-${provider}`,
      name: provider,
      type: "provider",
      color: getProviderColor(provider),
      x: 0,
      y: 0
    };
    nodes.push(node);
    nodeById.set(node.id, node);
  });

  allCategories.forEach((category) => {
    const textWidth = measureText(category);
    const nodeWidth = Math.max(textWidth + config.categoryPadding * 2, config.categoryMinWidth);
    const catColor = categoryColors[category] || "#666";

    const categoryNode = {
      id: `category-${category}`,
      name: category,
      type: "category",
      color: catColor,
      width: nodeWidth,
      height: config.categoryHeight,
      x: 0,
      y: 0
    };
    nodes.push(categoryNode);
    nodeById.set(categoryNode.id, categoryNode);

    const techniques = allTechniquesByCategory.get(category) || [];
    techniques.forEach((techName) => {
      const techId = `technique-${category}-${techName}`;

      let hasEvidence = false;
      selectedProviders.forEach((provider) => {
        if (evidenceLookup[provider]?.[category]?.[techName]) {
          hasEvidence = true;
        }
      });

      const techNode = {
        id: techId,
        name: techName,
        type: "technique",
        category: category,
        color: catColor,
        isOrphan: !hasEvidence,
        x: 0,
        y: 0
      };
      nodes.push(techNode);
      nodeById.set(techId, techNode);

      links.push({
        source: categoryNode.id,
        target: techId,
        type: "category-technique",
        color: darkenColor(catColor, 40)
      });

      selectedProviders.forEach((provider) => {
        const evidenceList = evidenceLookup[provider]?.[category]?.[techName];
        if (evidenceList && evidenceList.length > 0) {
          links.push({
            source: `provider-${provider}`,
            target: techId,
            type: "provider-technique",
            color: d3.color(getProviderColor(provider)).darker(0.4).toString(),
            data: evidenceList[0]
          });
        }
      });
    });
  });

  return {
    nodes,
    links,
    nodeById,
    selectedProviders,
    selectedCategories: allCategories,
    categoryGroups,
    techniquesByCategory: allTechniquesByCategory,
    evidenceLookup,
    getProviderColor,
    darkenColor,
    measureText
  };
}

export function createUnifiedChartLayouts(d3) {
  const config = unifiedChartConfig;

  function balancedLayout(chartData) {
    const { nodes, nodeById, categoryGroups, selectedProviders, selectedCategories } = chartData;
    const { width, height } = config;
    const positions = {};
    const labelAnchors = {};

    const sorted = [...categoryGroups].sort((a, b) => b.groupHeight - a.groupHeight);
    const leftGroups = [];
    const rightGroups = [];
    let leftHeight = 0;
    let rightHeight = 0;

    for (const group of sorted) {
      const addedHeight = group.groupHeight + config.categoryGroupGap;
      if (leftHeight <= rightHeight) {
        leftGroups.push(group);
        leftHeight += addedHeight;
      } else {
        rightGroups.push(group);
        rightHeight += addedHeight;
      }
    }

    leftGroups.sort((a, b) => a.name.localeCompare(b.name));
    rightGroups.sort((a, b) => a.name.localeCompare(b.name));

    const colHeight = (groups) =>
      groups.reduce((sum, g, i) => sum + g.groupHeight + (i > 0 ? config.categoryGroupGap : 0), 0);

    function layoutColumn(groups, xCenter, isLeft) {
      const totalH = colHeight(groups);
      let y = (height - totalH) / 2 + config.nodeMargins.top;

      groups.forEach((group) => {
        const catId = `category-${group.name}`;
        positions[catId] = { x: xCenter, y: y + config.categoryHeight / 2 };
        labelAnchors[catId] = "middle";

        group.techniques.forEach((techName, i) => {
          const techId = `technique-${group.name}-${techName}`;
          const techY = y + config.categoryHeight + config.categoryTechGap + i * config.techniqueSpacingY;
          positions[techId] = { x: xCenter, y: techY };
          labelAnchors[techId] = isLeft ? "end" : "start";
        });

        y += group.groupHeight + config.categoryGroupGap;
      });
    }

    const leftX = config.nodeMargins.left + config.categoryMinWidth / 2 + 60;
    const rightX = width - config.nodeMargins.right - config.categoryMinWidth / 2 - 60;

    layoutColumn(leftGroups, leftX, true);
    layoutColumn(rightGroups, rightX, false);

    const centerX = width / 2;
    const providerBlockHeight = selectedProviders.length * config.providerSpacing;
    const providerStartY = (height - providerBlockHeight) / 2 + config.providerSpacing / 2;

    selectedProviders.forEach((provider, i) => {
      const pid = `provider-${provider}`;
      positions[pid] = { x: centerX, y: providerStartY + i * config.providerSpacing };
      labelAnchors[pid] = "start";
    });

    return { positions, labelAnchors, layoutName: "balanced" };
  }

  function sequentialLayout(chartData) {
    const { nodes, nodeById, categoryGroups, selectedProviders } = chartData;
    const { width, height } = config;
    const positions = {};
    const labelAnchors = {};

    const colX = {
      category: width * config.sequentialColumns.category,
      technique: width * config.sequentialColumns.technique,
      provider: width * config.sequentialColumns.provider
    };

    const allTechniqueCount = categoryGroups.reduce((sum, g) => sum + g.techniques.length, 0);
    const techSpacing = Math.min(
      config.techniqueSpacingY,
      (height - 100) / Math.max(allTechniqueCount, 1)
    );

    const catPositions = [];
    let catY = config.nodeMargins.top + 20;

    categoryGroups.forEach((group) => {
      positions[`category-${group.name}`] = { x: colX.category, y: catY };
      labelAnchors[`category-${group.name}`] = "middle";
      catPositions.push({ name: group.name, y: catY, techniques: group.techniques });
      catY += config.categoryHeight + config.categoryGroupGap + group.techniques.length * techSpacing;
    });

    catPositions.forEach((catPos) => {
      catPos.techniques.forEach((techName, i) => {
        const techId = `technique-${catPos.name}-${techName}`;
        positions[techId] = { x: colX.technique, y: catPos.y + i * techSpacing };
        labelAnchors[techId] = "middle";
      });
    });

    const providerBlockHeight = selectedProviders.length * config.providerSpacing;
    const providerStartY = Math.max(config.nodeMargins.top + 20, (height - providerBlockHeight) / 2);

    selectedProviders.forEach((provider, i) => {
      const pid = `provider-${provider}`;
      positions[pid] = { x: colX.provider, y: providerStartY + i * config.providerSpacing };
      labelAnchors[pid] = "start";
    });

    return { positions, labelAnchors, layoutName: "sequential" };
  }

  function createForceSimulation(nodes, links, selectedNodeIds, nodeById) {
    const fc = config.force;

    const simulatedIds = selectedNodeIds.size > 0
      ? selectedNodeIds
      : new Set(nodes.map((n) => n.id));

    nodes.forEach((node) => {
      if (simulatedIds.has(node.id)) {
        node.fx = null;
        node.fy = null;
      } else {
        node.fx = node.x;
        node.fy = node.y;
      }
    });

    const relevantLinks = links
      .map((l) => ({
        source: typeof l.source === "object" ? l.source : nodeById.get(l.source),
        target: typeof l.target === "object" ? l.target : nodeById.get(l.target),
        type: l.type
      }))
      .filter((l) => l.source && l.target)
      .filter((l) => simulatedIds.has(l.source.id) || simulatedIds.has(l.target.id));

    return d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(relevantLinks)
          .id((d) => d.id)
          .distance((d) =>
            d.type === "provider-technique"
              ? fc.linkDistanceProviderTechnique
              : fc.linkDistanceCategoryTechnique
          )
          .strength((d) =>
            d.type === "provider-technique"
              ? fc.linkStrengthProviderTechnique
              : fc.linkStrengthCategoryTechnique
          )
      )
      .force(
        "charge",
        d3.forceManyBody().strength((d) => {
          if (!simulatedIds.has(d.id)) return 0;
          if (d.type === "provider") return fc.chargeProvider;
          if (d.type === "technique") return fc.chargeTechnique;
          return fc.chargeCategory;
        })
      )
      .force(
        "collide",
        d3.forceCollide().radius((d) => {
          if (!simulatedIds.has(d.id)) return 0;
          return d.type === "provider" ? fc.collideProvider : fc.collideTechnique;
        })
      )
      .alphaDecay(fc.alphaDecay)
      .velocityDecay(fc.velocityDecay);
  }

  return { balancedLayout, sequentialLayout, createForceSimulation };
}

export function validateUnifiedChartLayout(chartData, layouts) {
  const { nodes } = chartData;
  const liveNodeIds = new Set(nodes.map((n) => n.id));

  let savedLayout = null;
  let source = "default";
  const stats = { applied: 0, stale: 0, newNodes: 0 };

  try {
    const saved = localStorage.getItem(UNIFIED_LAYOUT_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.positions && typeof parsed.positions === "object") {
        savedLayout = parsed;
        source = "saved";
      }
    }
  } catch (e) {
    console.warn("Could not load saved unified chart layout:", e);
  }

  if (savedLayout) {
    const staleIds = Object.keys(savedLayout.positions).filter((id) => !liveNodeIds.has(id));
    staleIds.forEach((id) => delete savedLayout.positions[id]);
    if (savedLayout.labelAnchors) {
      staleIds.forEach((id) => delete savedLayout.labelAnchors[id]);
    }
    stats.stale = staleIds.length;

    const savedIds = new Set(Object.keys(savedLayout.positions));
    stats.newNodes = nodes.filter((n) => !savedIds.has(n.id)).length;
    stats.applied = nodes.filter((n) => savedIds.has(n.id)).length;
  }

  const balanced = layouts.balancedLayout(chartData);

  const finalPositions = { ...balanced.positions };
  const finalAnchors = { ...balanced.labelAnchors };

  if (savedLayout) {
    Object.entries(savedLayout.positions).forEach(([id, pos]) => {
      if (liveNodeIds.has(id) && typeof pos.x === "number" && typeof pos.y === "number" && isFinite(pos.x) && isFinite(pos.y)) {
        finalPositions[id] = pos;
      }
    });
    if (savedLayout.labelAnchors) {
      Object.entries(savedLayout.labelAnchors).forEach(([id, anchor]) => {
        if (liveNodeIds.has(id)) {
          finalAnchors[id] = anchor;
        }
      });
    }
  }

  return {
    positions: finalPositions,
    labelAnchors: finalAnchors,
    layoutName: source === "saved" ? savedLayout.layoutName || "saved" : "balanced",
    source,
    stats
  };
}
