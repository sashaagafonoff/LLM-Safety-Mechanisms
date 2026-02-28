// Safety incidents analytical table with filtering, sorting, pivot views, and CSV export

export function createIncidentsTable(incidents, providers, models, techniques, riskAreas, categories) {
  // --- Lookups ---
  const provLookup = new Map(providers.map(p => [p.id, p]));
  const modelsList = Array.isArray(models) ? models : models.models || [];
  const modelLookup = new Map(modelsList.map(m => [m.id, m]));
  const techLookup = new Map(techniques.map(t => [t.id, t]));
  const catLookup = new Map(categories.map(c => [c.id, c]));
  const riskLookup = new Map(riskAreas.map(r => [r.id, r]));

  // --- Color constants (match incidents-view.js) ---
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };

  // --- Enrich data ---
  const enriched = incidents.map(inc => {
    const resolvedProviders = (inc.providerIds || []).map(pid => ({
      id: pid,
      name: provLookup.get(pid)?.name || capitalizeProvider(pid)
    }));
    const resolvedModels = (inc.modelIds || []).map(mid => {
      const m = modelLookup.get(mid);
      return { id: mid, name: m?.version || m?.id || mid };
    }).filter(m => m.name);
    const resolvedTechniques = (inc.techniqueIds || []).map(tid => {
      const tech = techLookup.get(tid);
      const cat = tech ? catLookup.get(tech.categoryId) : null;
      return {
        id: tid,
        name: tech?.name || tid,
        categoryName: cat?.name || "",
        categoryColor: cat?.color || "#999"
      };
    });
    const resolvedRiskAreas = (inc.riskAreaIds || []).map(rid => ({
      id: rid,
      name: riskLookup.get(rid)?.name || rid
    }));
    return {
      ...inc,
      resolvedProviders,
      resolvedModels,
      resolvedTechniques,
      resolvedRiskAreas,
      dateObj: inc.date ? new Date(inc.date) : null
    };
  });

  // --- Provider-centric aggregation ---
  const byProvider = new Map();
  for (const inc of enriched) {
    for (const prov of inc.resolvedProviders) {
      if (!byProvider.has(prov.id)) {
        byProvider.set(prov.id, { provider: prov, incidents: [], severities: {} });
      }
      const group = byProvider.get(prov.id);
      group.incidents.push(inc);
      const s = inc.severity || "medium";
      group.severities[s] = (group.severities[s] || 0) + 1;
    }
  }

  // --- Technique failure aggregation ---
  const byTechFailure = new Map();
  for (const inc of enriched) {
    for (const tech of inc.resolvedTechniques) {
      if (!byTechFailure.has(tech.id)) {
        byTechFailure.set(tech.id, {
          technique: tech,
          incidents: [],
          providerIds: new Set(),
          riskAreaIds: new Set(),
          severities: {}
        });
      }
      const group = byTechFailure.get(tech.id);
      group.incidents.push(inc);
      for (const p of inc.resolvedProviders) group.providerIds.add(p.id);
      for (const r of inc.resolvedRiskAreas) group.riskAreaIds.add(r.id);
      const s = inc.severity || "medium";
      group.severities[s] = (group.severities[s] || 0) + 1;
    }
  }

  // --- Unique filter values ---
  const allProviderIds = [...new Set(enriched.flatMap(i => i.resolvedProviders.map(p => p.id)))].sort();
  const allSeverities = ["critical", "high", "medium", "low"].filter(s => enriched.some(i => i.severity === s));
  const allRiskAreaIds = [...new Set(enriched.flatMap(i => i.resolvedRiskAreas.map(r => r.id)))].sort((a, b) => {
    return (riskLookup.get(a)?.name || a).localeCompare(riskLookup.get(b)?.name || b);
  });
  const allTechIds = [...new Set(enriched.flatMap(i => i.resolvedTechniques.map(t => t.id)))].sort((a, b) => {
    return (techLookup.get(a)?.name || a).localeCompare(techLookup.get(b)?.name || b);
  });

  // --- State ---
  let viewMode = "by-incident";
  let filterState = { provider: "", severity: "", riskArea: "", technique: "", search: "" };
  let sortState = { column: "date", direction: "desc" };
  let expandedRow = null;

  // --- Container ---
  const container = document.createElement("div");

  function render() {
    container.innerHTML = "";
    container.appendChild(renderStats());
    container.appendChild(renderViewToggle());
    container.appendChild(renderFilters());
    if (viewMode === "by-incident") {
      container.appendChild(renderIncidentTable());
    } else if (viewMode === "by-provider") {
      container.appendChild(renderProviderTable());
    } else {
      container.appendChild(renderTechFailureTable());
    }
  }

  // --- Stats ---
  function renderStats() {
    const sevCounts = {};
    for (const inc of enriched) sevCounts[inc.severity] = (sevCounts[inc.severity] || 0) + 1;
    const uniqueProvs = new Set(enriched.flatMap(i => i.resolvedProviders.map(p => p.id)));
    const maxTech = [...byTechFailure.entries()].sort((a, b) => b[1].incidents.length - a[1].incidents.length)[0];
    const maxRisk = getMostCommon(enriched.flatMap(i => i.resolvedRiskAreas.map(r => r.name)));

    const row = document.createElement("div");
    row.className = "stats-row";
    const cards = [
      { value: enriched.length, label: "Total Incidents" },
      { value: uniqueProvs.size, label: "Providers Affected" },
    ];
    for (const s of ["critical", "high", "medium"]) {
      if (sevCounts[s]) {
        const colors = { critical: "#dc2626", high: "#ea580c", medium: "#ca8a04" };
        cards.push({ value: sevCounts[s], label: capitalize(s), color: colors[s] });
      }
    }
    if (maxTech) {
      cards.push({ value: maxTech[1].incidents.length, label: `Top fail: ${truncateText(maxTech[1].technique.name, 18)}` });
    }
    if (maxRisk) {
      cards.push({ value: maxRisk.count, label: `Risk: ${truncateText(maxRisk.value, 18)}` });
    }
    for (const c of cards) {
      const card = document.createElement("div");
      card.className = "stat-card";
      card.innerHTML = `<div class="stat-value" ${c.color ? `style="color:${c.color}"` : ""}>${c.value}</div>
        <div class="stat-label">${c.label}</div>`;
      row.appendChild(card);
    }
    return row;
  }

  // --- View toggle ---
  function renderViewToggle() {
    const div = document.createElement("div");
    div.className = "view-toggle";
    const modes = [
      { id: "by-incident", label: "By Incident" },
      { id: "by-provider", label: "By Provider" },
      { id: "by-technique", label: "By Technique Failure" }
    ];
    for (const m of modes) {
      const btn = document.createElement("button");
      btn.textContent = m.label;
      if (m.id === viewMode) btn.className = "active";
      btn.addEventListener("click", () => {
        viewMode = m.id;
        expandedRow = null;
        render();
      });
      div.appendChild(btn);
    }
    const exportBtn = document.createElement("button");
    exportBtn.textContent = "Export CSV";
    exportBtn.className = "export-btn";
    exportBtn.style.marginLeft = "auto";
    exportBtn.addEventListener("click", exportCSV);
    div.appendChild(exportBtn);
    return div;
  }

  // --- Filters ---
  function renderFilters() {
    const bar = document.createElement("div");
    bar.className = "filter-bar";

    bar.appendChild(makeSelect("Provider", allProviderIds.map(id => ({
      value: id, label: provLookup.get(id)?.name || capitalizeProvider(id)
    })), filterState.provider, v => { filterState.provider = v; expandedRow = null; render(); }));

    bar.appendChild(makeSelect("Severity", allSeverities.map(s => ({
      value: s, label: capitalize(s)
    })), filterState.severity, v => { filterState.severity = v; expandedRow = null; render(); }));

    bar.appendChild(makeSelect("Risk Area", allRiskAreaIds.map(id => ({
      value: id, label: riskLookup.get(id)?.name || id
    })), filterState.riskArea, v => { filterState.riskArea = v; expandedRow = null; render(); }));

    bar.appendChild(makeSelect("Technique", allTechIds.map(id => ({
      value: id, label: techLookup.get(id)?.name || id
    })), filterState.technique, v => { filterState.technique = v; expandedRow = null; render(); }));

    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "Search title, description...";
    searchInput.value = filterState.search;
    searchInput.addEventListener("input", () => {
      filterState.search = searchInput.value;
      expandedRow = null;
      render();
    });
    bar.appendChild(searchInput);

    if (hasActiveFilters()) {
      const clearBtn = document.createElement("button");
      clearBtn.textContent = "Clear filters";
      clearBtn.style.fontSize = "12px";
      clearBtn.addEventListener("click", () => {
        filterState = { provider: "", severity: "", riskArea: "", technique: "", search: "" };
        expandedRow = null;
        render();
      });
      bar.appendChild(clearBtn);
    }

    return bar;
  }

  function hasActiveFilters() {
    return Object.values(filterState).some(v => v !== "");
  }

  // --- Incident table ---
  function renderIncidentTable() {
    const filtered = applyFilters(enriched);
    const sorted = applySort(filtered);

    const wrapper = document.createElement("div");
    const countEl = document.createElement("div");
    countEl.className = "filter-count";
    countEl.textContent = `Showing ${sorted.length} of ${enriched.length} incidents`;
    countEl.style.marginBottom = "8px";
    wrapper.appendChild(countEl);

    const table = document.createElement("table");
    table.className = "anal-table";

    const columns = [
      { key: "date", label: "Date", width: "90px" },
      { key: "severity", label: "Severity", width: "80px" },
      { key: "providers", label: "Provider", width: "120px" },
      { key: "title", label: "Title" },
      { key: "techniques", label: "Techniques Failed" },
      { key: "riskAreas", label: "Risk Areas", width: "160px" },
      { key: "sources", label: "Src", width: "45px" }
    ];

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    for (const col of columns) {
      const th = document.createElement("th");
      if (col.width) th.style.width = col.width;
      th.className = sortState.column === col.key ? "sort-active" : "";
      const arrow = sortState.column === col.key ? (sortState.direction === "asc" ? "\u25B2" : "\u25BC") : "\u25B4";
      th.innerHTML = `${col.label} <span class="sort-arrow">${arrow}</span>`;
      th.addEventListener("click", () => {
        if (sortState.column === col.key) {
          sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
        } else {
          sortState.column = col.key;
          sortState.direction = col.key === "date" ? "desc" : "asc";
        }
        expandedRow = null;
        render();
      });
      headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (const inc of sorted) {
      const tr = document.createElement("tr");
      tr.addEventListener("click", () => {
        expandedRow = expandedRow === inc.id ? null : inc.id;
        render();
      });

      // Date
      addCell(tr, inc.date || "");
      // Severity
      const sevTd = document.createElement("td");
      sevTd.innerHTML = `<span class="chip badge-${inc.severity || 'medium'}">${capitalize(inc.severity || "medium")}</span>`;
      tr.appendChild(sevTd);
      // Provider
      const provTd = document.createElement("td");
      provTd.appendChild(renderChips(inc.resolvedProviders, 2, p => p.name, () => "#607d8b"));
      tr.appendChild(provTd);
      // Title
      const titleTd = document.createElement("td");
      titleTd.textContent = truncateText(inc.title, 65);
      titleTd.title = inc.title;
      tr.appendChild(titleTd);
      // Techniques
      const techTd = document.createElement("td");
      techTd.appendChild(renderChips(inc.resolvedTechniques, 3, t => t.name, t => t.categoryColor));
      tr.appendChild(techTd);
      // Risk Areas
      const riskTd = document.createElement("td");
      riskTd.appendChild(renderChips(inc.resolvedRiskAreas, 2, r => r.name, () => "#78909c"));
      tr.appendChild(riskTd);
      // Sources count
      addCell(tr, String((inc.sources || []).length));

      tbody.appendChild(tr);

      // Expanded detail
      if (expandedRow === inc.id) {
        const detailTr = document.createElement("tr");
        detailTr.className = "detail-row";
        const detailTd = document.createElement("td");
        detailTd.colSpan = columns.length;
        detailTd.innerHTML = buildIncidentDetail(inc);
        detailTr.appendChild(detailTd);
        tbody.appendChild(detailTr);
      }
    }
    table.appendChild(tbody);
    wrapper.appendChild(table);
    return wrapper;
  }

  // --- Provider pivot table ---
  function renderProviderTable() {
    let provRows = [...byProvider.values()];

    // Apply filters
    if (filterState.provider) provRows = provRows.filter(r => r.provider.id === filterState.provider);
    if (filterState.severity || filterState.riskArea || filterState.technique || filterState.search) {
      provRows = provRows.map(r => {
        let incs = r.incidents;
        if (filterState.severity) incs = incs.filter(i => i.severity === filterState.severity);
        if (filterState.riskArea) incs = incs.filter(i => i.resolvedRiskAreas.some(ra => ra.id === filterState.riskArea));
        if (filterState.technique) incs = incs.filter(i => i.resolvedTechniques.some(t => t.id === filterState.technique));
        if (filterState.search) {
          const q = filterState.search.toLowerCase();
          incs = incs.filter(i => (i.title || "").toLowerCase().includes(q) || (i.description || "").toLowerCase().includes(q));
        }
        if (incs.length === 0) return null;
        const severities = {};
        for (const i of incs) severities[i.severity] = (severities[i.severity] || 0) + 1;
        return { ...r, incidents: incs, severities };
      }).filter(Boolean);
    }

    const dir = sortState.direction === "asc" ? 1 : -1;
    provRows.sort((a, b) => {
      switch (sortState.column) {
        case "provider": return dir * a.provider.name.localeCompare(b.provider.name);
        case "total": return dir * (a.incidents.length - b.incidents.length);
        default: return dir * (b.incidents.length - a.incidents.length);
      }
    });

    const wrapper = document.createElement("div");
    const countEl = document.createElement("div");
    countEl.className = "filter-count";
    countEl.textContent = `Showing ${provRows.length} providers`;
    countEl.style.marginBottom = "8px";
    wrapper.appendChild(countEl);

    const table = document.createElement("table");
    table.className = "anal-table";
    const columns = [
      { key: "provider", label: "Provider" },
      { key: "total", label: "Total", width: "65px" },
      { key: "critical", label: "Critical", width: "70px" },
      { key: "high", label: "High", width: "55px" },
      { key: "medium", label: "Medium", width: "65px" },
      { key: "topTech", label: "Most Failed Techniques" },
      { key: "riskAreas", label: "Risk Areas" }
    ];

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    for (const col of columns) {
      const th = document.createElement("th");
      if (col.width) th.style.width = col.width;
      th.className = sortState.column === col.key ? "sort-active" : "";
      const arrow = sortState.column === col.key ? (sortState.direction === "asc" ? "\u25B2" : "\u25BC") : "\u25B4";
      th.innerHTML = `${col.label} <span class="sort-arrow">${arrow}</span>`;
      th.addEventListener("click", () => {
        if (sortState.column === col.key) sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
        else { sortState.column = col.key; sortState.direction = "desc"; }
        expandedRow = null;
        render();
      });
      headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (const row of provRows) {
      const tr = document.createElement("tr");
      tr.addEventListener("click", () => {
        expandedRow = expandedRow === row.provider.id ? null : row.provider.id;
        render();
      });

      addCell(tr, row.provider.name);
      const totalTd = document.createElement("td");
      totalTd.innerHTML = `<strong>${row.incidents.length}</strong>`;
      tr.appendChild(totalTd);

      for (const s of ["critical", "high", "medium"]) {
        const td = document.createElement("td");
        const count = row.severities[s] || 0;
        if (count > 0) {
          td.innerHTML = `<span class="chip badge-${s}">${count}</span>`;
        } else {
          td.textContent = "-";
          td.style.color = "#ccc";
        }
        tr.appendChild(td);
      }

      // Top failed techniques
      const techCounts = {};
      for (const inc of row.incidents) {
        for (const t of inc.resolvedTechniques) techCounts[t.id] = (techCounts[t.id] || 0) + 1;
      }
      const topTechs = Object.entries(techCounts).sort((a, b) => b[1] - a[1]).slice(0, 3);
      const techTd = document.createElement("td");
      techTd.appendChild(renderChips(
        topTechs.map(([tid, count]) => {
          const tech = techLookup.get(tid);
          const cat = tech ? catLookup.get(tech.categoryId) : null;
          return { name: `${tech?.name || tid} (${count})`, color: cat?.color || "#999" };
        }), 3, t => t.name, t => t.color
      ));
      tr.appendChild(techTd);

      // Risk areas
      const riskIds = new Set();
      for (const inc of row.incidents) for (const r of inc.resolvedRiskAreas) riskIds.add(r.id);
      const riskTd = document.createElement("td");
      riskTd.appendChild(renderChips(
        [...riskIds].map(rid => ({ name: riskLookup.get(rid)?.name || rid, color: "#78909c" })),
        3, r => r.name, r => r.color
      ));
      tr.appendChild(riskTd);

      tbody.appendChild(tr);

      // Expanded: list incidents for this provider
      if (expandedRow === row.provider.id) {
        const detailTr = document.createElement("tr");
        detailTr.className = "detail-row";
        const detailTd = document.createElement("td");
        detailTd.colSpan = columns.length;
        let html = `<div style="max-height:400px;overflow-y:auto">`;
        const sorted = [...row.incidents].sort((a, b) => (b.dateObj || 0) - (a.dateObj || 0));
        for (const inc of sorted) {
          html += `<div style="margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #e0e0e0">
            <div><span class="chip badge-${inc.severity}">${capitalize(inc.severity)}</span>
            <strong>${escapeHtml(inc.title)}</strong>
            <span style="font-size:11px;color:#888;margin-left:6px">${inc.date || ""}</span></div>
            <div style="font-size:12px;color:#555;margin-top:4px">${escapeHtml(truncateText(inc.description, 200))}</div>
            <div style="margin-top:4px">${inc.resolvedTechniques.map(t =>
              `<span class="chip" style="background:${t.categoryColor}18;color:${t.categoryColor};border-color:${t.categoryColor}40">${escapeHtml(t.name)}</span>`
            ).join(" ")}</div>
          </div>`;
        }
        html += `</div>`;
        detailTd.innerHTML = html;
        detailTr.appendChild(detailTd);
        tbody.appendChild(detailTr);
      }
    }
    table.appendChild(tbody);
    wrapper.appendChild(table);
    return wrapper;
  }

  // --- Technique failure pivot table ---
  function renderTechFailureTable() {
    let techRows = [...byTechFailure.values()];

    // Apply filters
    if (filterState.technique) techRows = techRows.filter(r => r.technique.id === filterState.technique);
    if (filterState.provider) {
      techRows = techRows.filter(r => r.providerIds.has(filterState.provider));
    }
    if (filterState.severity || filterState.riskArea || filterState.search) {
      techRows = techRows.map(r => {
        let incs = r.incidents;
        if (filterState.severity) incs = incs.filter(i => i.severity === filterState.severity);
        if (filterState.riskArea) incs = incs.filter(i => i.resolvedRiskAreas.some(ra => ra.id === filterState.riskArea));
        if (filterState.search) {
          const q = filterState.search.toLowerCase();
          incs = incs.filter(i => (i.title || "").toLowerCase().includes(q) || (i.description || "").toLowerCase().includes(q));
        }
        if (incs.length === 0) return null;
        const providerIds = new Set();
        const riskAreaIds = new Set();
        const severities = {};
        for (const i of incs) {
          for (const p of i.resolvedProviders) providerIds.add(p.id);
          for (const ra of i.resolvedRiskAreas) riskAreaIds.add(ra.id);
          severities[i.severity] = (severities[i.severity] || 0) + 1;
        }
        return { ...r, incidents: incs, providerIds, riskAreaIds, severities };
      }).filter(Boolean);
    }

    const dir = sortState.direction === "asc" ? 1 : -1;
    techRows.sort((a, b) => {
      switch (sortState.column) {
        case "technique": return dir * a.technique.name.localeCompare(b.technique.name);
        case "category": return dir * a.technique.categoryName.localeCompare(b.technique.categoryName);
        case "failures": return dir * (a.incidents.length - b.incidents.length);
        default: return dir * (b.incidents.length - a.incidents.length);
      }
    });

    const wrapper = document.createElement("div");
    const countEl = document.createElement("div");
    countEl.className = "filter-count";
    countEl.textContent = `Showing ${techRows.length} techniques with recorded failures`;
    countEl.style.marginBottom = "8px";
    wrapper.appendChild(countEl);

    const table = document.createElement("table");
    table.className = "anal-table";
    const columns = [
      { key: "technique", label: "Technique" },
      { key: "category", label: "Category", width: "160px" },
      { key: "failures", label: "Failures", width: "70px" },
      { key: "providers", label: "Affected Providers" },
      { key: "severity", label: "Severity Breakdown", width: "180px" },
      { key: "risks", label: "Risk Areas" }
    ];

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    for (const col of columns) {
      const th = document.createElement("th");
      if (col.width) th.style.width = col.width;
      th.className = sortState.column === col.key ? "sort-active" : "";
      const arrow = sortState.column === col.key ? (sortState.direction === "asc" ? "\u25B2" : "\u25BC") : "\u25B4";
      th.innerHTML = `${col.label} <span class="sort-arrow">${arrow}</span>`;
      th.addEventListener("click", () => {
        if (sortState.column === col.key) sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
        else { sortState.column = col.key; sortState.direction = "desc"; }
        expandedRow = null;
        render();
      });
      headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (const row of techRows) {
      const tr = document.createElement("tr");
      tr.addEventListener("click", () => {
        expandedRow = expandedRow === row.technique.id ? null : row.technique.id;
        render();
      });

      addCell(tr, row.technique.name);
      const catTd = document.createElement("td");
      catTd.innerHTML = `<span class="chip" style="background:${row.technique.categoryColor}20;color:${row.technique.categoryColor};border-color:${row.technique.categoryColor}40">${escapeHtml(row.technique.categoryName)}</span>`;
      tr.appendChild(catTd);

      const failTd = document.createElement("td");
      failTd.innerHTML = `<strong>${row.incidents.length}</strong>`;
      tr.appendChild(failTd);

      // Providers
      const provTd = document.createElement("td");
      provTd.appendChild(renderChips(
        [...row.providerIds].sort().map(pid => ({
          name: provLookup.get(pid)?.name || capitalizeProvider(pid),
          color: "#607d8b"
        })), 4, p => p.name, p => p.color
      ));
      tr.appendChild(provTd);

      // Severity breakdown
      const sevTd = document.createElement("td");
      for (const s of ["critical", "high", "medium"]) {
        const count = row.severities[s] || 0;
        if (count > 0) {
          const span = document.createElement("span");
          span.className = `chip badge-${s}`;
          span.textContent = `${capitalize(s)}: ${count}`;
          span.style.marginRight = "4px";
          sevTd.appendChild(span);
        }
      }
      tr.appendChild(sevTd);

      // Risk areas
      const riskTd = document.createElement("td");
      riskTd.appendChild(renderChips(
        [...row.riskAreaIds].map(rid => ({ name: riskLookup.get(rid)?.name || rid, color: "#78909c" })),
        3, r => r.name, r => r.color
      ));
      tr.appendChild(riskTd);

      tbody.appendChild(tr);

      // Expanded: list incidents for this technique
      if (expandedRow === row.technique.id) {
        const detailTr = document.createElement("tr");
        detailTr.className = "detail-row";
        const detailTd = document.createElement("td");
        detailTd.colSpan = columns.length;
        let html = `<div style="max-height:400px;overflow-y:auto">`;
        const sorted = [...row.incidents].sort((a, b) => (b.dateObj || 0) - (a.dateObj || 0));
        for (const inc of sorted) {
          html += `<div style="margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #e0e0e0">
            <div><span class="chip badge-${inc.severity}">${capitalize(inc.severity)}</span>
            <strong>${escapeHtml(inc.title)}</strong>
            <span style="font-size:11px;color:#888;margin-left:6px">${inc.date || ""}</span>
            ${inc.resolvedProviders.map(p => `<span class="chip" style="background:#607d8b18;color:#607d8b;border-color:#607d8b40">${escapeHtml(p.name)}</span>`).join(" ")}</div>
            <div style="font-size:12px;color:#555;margin-top:4px">${escapeHtml(truncateText(inc.description, 200))}</div>
          </div>`;
        }
        html += `</div>`;
        detailTd.innerHTML = html;
        detailTr.appendChild(detailTd);
        tbody.appendChild(detailTr);
      }
    }
    table.appendChild(tbody);
    wrapper.appendChild(table);
    return wrapper;
  }

  // --- Filter logic ---
  function applyFilters(entries) {
    let result = entries;
    if (filterState.provider) result = result.filter(i => i.resolvedProviders.some(p => p.id === filterState.provider));
    if (filterState.severity) result = result.filter(i => i.severity === filterState.severity);
    if (filterState.riskArea) result = result.filter(i => i.resolvedRiskAreas.some(r => r.id === filterState.riskArea));
    if (filterState.technique) result = result.filter(i => i.resolvedTechniques.some(t => t.id === filterState.technique));
    if (filterState.search) {
      const q = filterState.search.toLowerCase();
      result = result.filter(i =>
        (i.title || "").toLowerCase().includes(q) ||
        (i.description || "").toLowerCase().includes(q));
    }
    return result;
  }

  // --- Sort logic ---
  function applySort(entries) {
    const { column, direction } = sortState;
    const dir = direction === "asc" ? 1 : -1;
    return [...entries].sort((a, b) => {
      switch (column) {
        case "date": return dir * ((a.dateObj || new Date(0)) - (b.dateObj || new Date(0)));
        case "severity": return dir * ((severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3));
        case "title": return dir * (a.title || "").localeCompare(b.title || "");
        case "providers": return dir * ((a.resolvedProviders[0]?.name || "").localeCompare(b.resolvedProviders[0]?.name || ""));
        case "techniques": return dir * (a.resolvedTechniques.length - b.resolvedTechniques.length);
        case "riskAreas": return dir * (a.resolvedRiskAreas.length - b.resolvedRiskAreas.length);
        case "sources": return dir * ((a.sources || []).length - (b.sources || []).length);
        default: return 0;
      }
    });
  }

  // --- CSV export ---
  function exportCSV() {
    const filtered = applySort(applyFilters(enriched));
    const rows = [["Date", "Severity", "Providers", "Models", "Title", "Description", "Techniques Failed", "Risk Areas", "Sources"]];
    for (const inc of filtered) {
      rows.push([
        inc.date || "",
        inc.severity || "",
        inc.resolvedProviders.map(p => p.name).join("; "),
        inc.resolvedModels.map(m => m.name).join("; "),
        inc.title || "",
        (inc.description || "").replace(/"/g, '""'),
        inc.resolvedTechniques.map(t => t.name).join("; "),
        inc.resolvedRiskAreas.map(r => r.name).join("; "),
        (inc.sources || []).map(s => s.url).join("; ")
      ]);
    }
    const csv = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
    downloadFile("incidents-analysis.csv", csv, "text/csv");
  }

  // --- Helpers ---
  function makeSelect(label, options, current, onChange) {
    const wrap = document.createElement("label");
    wrap.textContent = label + " ";
    const sel = document.createElement("select");
    const defOpt = document.createElement("option");
    defOpt.value = "";
    defOpt.textContent = `All`;
    sel.appendChild(defOpt);
    for (const o of options) {
      const opt = document.createElement("option");
      opt.value = o.value;
      opt.textContent = truncateText(o.label, 30);
      if (o.value === current) opt.selected = true;
      sel.appendChild(opt);
    }
    sel.addEventListener("change", () => onChange(sel.value));
    wrap.appendChild(sel);
    return wrap;
  }

  function addCell(tr, text) {
    const td = document.createElement("td");
    td.textContent = text;
    tr.appendChild(td);
  }

  function renderChips(items, max, getName, getColor) {
    const frag = document.createDocumentFragment();
    const show = items.slice(0, max);
    for (const item of show) {
      const span = document.createElement("span");
      span.className = "chip";
      const color = getColor(item);
      span.style.cssText = `background:${color}18;color:${color};border-color:${color}40`;
      span.textContent = getName(item);
      frag.appendChild(span);
    }
    if (items.length > max) {
      const more = document.createElement("span");
      more.className = "chip-overflow";
      more.textContent = `+${items.length - max}`;
      more.title = items.slice(max).map(getName).join(", ");
      frag.appendChild(more);
    }
    return frag;
  }

  function buildIncidentDetail(inc) {
    let html = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">`;
    html += `<div>`;
    html += `<div style="margin-bottom:8px"><strong>Description:</strong> ${escapeHtml(inc.description || "No description available")}</div>`;
    if (inc.resolvedModels.length > 0) {
      html += `<div style="margin-bottom:8px"><strong>Models:</strong> ${inc.resolvedModels.map(m => escapeHtml(m.name)).join(", ")}</div>`;
    }
    html += `<div><strong>Status:</strong> ${capitalize(inc.status || "unknown")}</div>`;
    html += `</div><div>`;
    html += `<div style="margin-bottom:8px"><strong>Techniques that failed:</strong></div>`;
    for (const t of inc.resolvedTechniques) {
      html += `<div style="margin-bottom:2px"><span class="chip" style="background:${t.categoryColor}18;color:${t.categoryColor};border-color:${t.categoryColor}40">${escapeHtml(t.name)}</span> <span style="font-size:11px;color:#888">${escapeHtml(t.categoryName)}</span></div>`;
    }
    if (inc.sources && inc.sources.length > 0) {
      html += `<div style="margin-top:8px"><strong>Sources:</strong></div>`;
      for (const src of inc.sources) {
        html += `<div style="font-size:12px;margin-top:2px"><a href="${escapeHtml(src.url)}" target="_blank">${escapeHtml(src.title || src.url)}</a> <span style="color:#888">${src.date || ""}</span></div>`;
      }
    }
    html += `</div></div>`;
    return html;
  }

  function getMostCommon(arr) {
    const counts = {};
    for (const v of arr) counts[v] = (counts[v] || 0) + 1;
    let max = null;
    for (const [value, count] of Object.entries(counts)) {
      if (!max || count > max.count) max = { value, count };
    }
    return max;
  }

  function truncateText(text, max) {
    if (!text || text.length <= max) return text || "";
    return text.slice(0, max) + "...";
  }

  function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }

  function capitalizeProvider(id) {
    const map = { openai: "OpenAI", anthropic: "Anthropic", google: "Google", meta: "Meta", amazon: "Amazon", microsoft: "Microsoft", nvidia: "Nvidia", xai: "xAI", alibaba: "Alibaba", tencent: "Tencent", deepseek: "DeepSeek", cohere: "Cohere", mistral: "Mistral AI", tii: "TII" };
    return map[id] || capitalize(id);
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s || "";
    return div.innerHTML;
  }

  function downloadFile(name, content, type) {
    const blob = new Blob([content], { type });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  render();
  return container;
}
