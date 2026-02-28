// Third-party commentary analytical table with filtering, sorting, pivot views, and CSV export

export function createCommentaryTable(commentary, techniques, categories, evidenceSources, techniqueMap) {
  // --- Lookups ---
  const techLookup = new Map(techniques.map(t => [t.id, t]));
  const catLookup = new Map(categories.map(c => [c.id, c]));

  // --- Provider bridging via evidence + techniqueMap ---
  // Build sourceId → providerId from evidence sources
  const sourceToProvider = new Map();
  for (const src of evidenceSources) {
    sourceToProvider.set(src.id, src.provider);
  }
  // Build techniqueId → Set<providerId> from techniqueMap
  const techToProviders = new Map();
  for (const [sourceId, entries] of Object.entries(techniqueMap)) {
    const providerId = sourceToProvider.get(sourceId);
    if (!providerId) continue;
    for (const entry of entries) {
      if (!entry.active) continue;
      const tid = entry.techniqueId;
      if (!techToProviders.has(tid)) techToProviders.set(tid, new Set());
      techToProviders.get(tid).add(providerId);
    }
  }

  // --- Color constants (match commentary-view.js) ---
  const sentimentColors = {
    positive: { bg: "#dcfce7", text: "#166534" },
    negative: { bg: "#fef2f2", text: "#991b1b" },
    mixed:    { bg: "#fefce8", text: "#854d0e" },
    neutral:  { bg: "#f3f4f6", text: "#374151" }
  };
  const typeBadgeLabels = {
    academic_paper: "Academic Paper",
    blog_post: "Blog Post",
    report: "Report",
    news_analysis: "News Analysis",
    audit: "Audit"
  };

  // --- Enrich data ---
  const enriched = commentary.map(c => {
    const resolvedTechniques = (c.techniqueIds || []).map(tid => {
      const tech = techLookup.get(tid);
      const cat = tech ? catLookup.get(tech.categoryId) : null;
      return {
        id: tid,
        name: tech?.name || tid,
        categoryName: cat?.name || "",
        categoryColor: cat?.color || "#999"
      };
    });
    // Collect providers implementing these techniques
    const providerSet = new Set();
    for (const tid of c.techniqueIds || []) {
      const providers = techToProviders.get(tid);
      if (providers) providers.forEach(p => providerSet.add(p));
    }
    return {
      ...c,
      resolvedTechniques,
      resolvedProviders: [...providerSet].sort(),
      dateObj: c.date ? new Date(c.date) : null,
      typeLabel: typeBadgeLabels[c.type] || c.type || ""
    };
  });

  // --- Technique-centric aggregation ---
  const byTechnique = new Map();
  for (const c of enriched) {
    for (const rt of c.resolvedTechniques) {
      if (!byTechnique.has(rt.id)) {
        byTechnique.set(rt.id, {
          technique: rt,
          entries: [],
          sentiments: { positive: 0, negative: 0, mixed: 0, neutral: 0 }
        });
      }
      const group = byTechnique.get(rt.id);
      group.entries.push(c);
      group.sentiments[c.sentiment || "neutral"]++;
    }
  }

  // --- Unique filter values ---
  const allTypes = [...new Set(commentary.map(c => c.type).filter(Boolean))].sort();
  const allSentiments = ["positive", "negative", "mixed", "neutral"];
  const allCategories = [...new Set(enriched.flatMap(c => c.resolvedTechniques.map(t => t.categoryName)))].filter(Boolean).sort();
  const allTechIds = [...new Set(enriched.flatMap(c => c.resolvedTechniques.map(t => t.id)))].sort((a, b) => {
    const na = techLookup.get(a)?.name || a;
    const nb = techLookup.get(b)?.name || b;
    return na.localeCompare(nb);
  });
  const allProviders = [...new Set(enriched.flatMap(c => c.resolvedProviders))].sort();

  // --- State ---
  let viewMode = "by-commentary";
  let filterState = { technique: "", category: "", type: "", sentiment: "", provider: "", search: "" };
  let sortState = { column: "date", direction: "desc" };
  let expandedRow = null;

  // --- Container ---
  const container = document.createElement("div");

  function render() {
    container.innerHTML = "";
    container.appendChild(renderStats());
    container.appendChild(renderViewToggle());
    container.appendChild(renderFilters());
    if (viewMode === "by-commentary") {
      container.appendChild(renderCommentaryTable());
    } else {
      container.appendChild(renderTechniqueTable());
    }
  }

  // --- Stats ---
  function renderStats() {
    const uniqueTechs = new Set(enriched.flatMap(c => c.resolvedTechniques.map(t => t.id)));
    const uniqueOrgs = new Set(enriched.map(c => c.organization).filter(Boolean));
    const sentimentCounts = { positive: 0, negative: 0, mixed: 0, neutral: 0 };
    for (const c of enriched) sentimentCounts[c.sentiment || "neutral"]++;
    const maxTech = [...byTechnique.entries()].sort((a, b) => b[1].entries.length - a[1].entries.length)[0];

    const row = document.createElement("div");
    row.className = "stats-row";
    const cards = [
      { value: enriched.length, label: "Total References" },
      { value: uniqueTechs.size, label: "Techniques Covered" },
      { value: uniqueOrgs.size, label: "Organizations" },
    ];
    for (const s of allSentiments) {
      if (sentimentCounts[s] > 0) {
        cards.push({
          value: sentimentCounts[s],
          label: s.charAt(0).toUpperCase() + s.slice(1),
          color: sentimentColors[s]?.text
        });
      }
    }
    if (maxTech) {
      cards.push({
        value: maxTech[1].entries.length,
        label: `Top: ${truncateText(maxTech[1].technique.name, 20)}`
      });
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
      { id: "by-commentary", label: "By Commentary" },
      { id: "by-technique", label: "By Technique" }
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
    // Export button
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

    bar.appendChild(makeSelect("Category", allCategories.map(c => ({ value: c, label: c })), filterState.category, v => { filterState.category = v; expandedRow = null; render(); }));
    bar.appendChild(makeSelect("Technique", allTechIds.map(id => ({ value: id, label: techLookup.get(id)?.name || id })), filterState.technique, v => { filterState.technique = v; expandedRow = null; render(); }));
    bar.appendChild(makeSelect("Type", allTypes.map(t => ({ value: t, label: typeBadgeLabels[t] || t })), filterState.type, v => { filterState.type = v; expandedRow = null; render(); }));
    bar.appendChild(makeSelect("Sentiment", allSentiments.map(s => ({ value: s, label: s.charAt(0).toUpperCase() + s.slice(1) })), filterState.sentiment, v => { filterState.sentiment = v; expandedRow = null; render(); }));
    bar.appendChild(makeSelect("Provider", allProviders.map(p => ({ value: p, label: capitalizeProvider(p) })), filterState.provider, v => { filterState.provider = v; expandedRow = null; render(); }));

    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "Search title, summary, author...";
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
        filterState = { technique: "", category: "", type: "", sentiment: "", provider: "", search: "" };
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

  // --- Commentary table ---
  function renderCommentaryTable() {
    const filtered = applyFilters(enriched);
    const sorted = applySort(filtered);

    const wrapper = document.createElement("div");
    const countEl = document.createElement("div");
    countEl.className = "filter-count";
    countEl.textContent = `Showing ${sorted.length} of ${enriched.length} entries`;
    countEl.style.marginBottom = "8px";
    wrapper.appendChild(countEl);

    const table = document.createElement("table");
    table.className = "anal-table";

    const columns = [
      { key: "date", label: "Date", width: "90px" },
      { key: "title", label: "Title" },
      { key: "organization", label: "Organization", width: "130px" },
      { key: "type", label: "Type", width: "100px" },
      { key: "sentiment", label: "Sentiment", width: "85px" },
      { key: "techniques", label: "Techniques" },
      { key: "providers", label: "Providers", width: "140px" }
    ];

    // Header
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

    // Body
    const tbody = document.createElement("tbody");
    for (const c of sorted) {
      const tr = document.createElement("tr");
      tr.addEventListener("click", () => {
        expandedRow = expandedRow === c.id ? null : c.id;
        render();
      });

      // Date
      addCell(tr, c.date || "");
      // Title
      const titleTd = document.createElement("td");
      const link = document.createElement("a");
      link.href = c.url;
      link.target = "_blank";
      link.textContent = truncateText(c.title, 60);
      link.title = c.title;
      link.addEventListener("click", e => e.stopPropagation());
      titleTd.appendChild(link);
      tr.appendChild(titleTd);
      // Organization
      addCell(tr, c.organization || "");
      // Type
      const typeTd = document.createElement("td");
      typeTd.innerHTML = `<span class="chip badge-${c.type}">${c.typeLabel}</span>`;
      tr.appendChild(typeTd);
      // Sentiment
      const sentTd = document.createElement("td");
      sentTd.innerHTML = `<span class="chip badge-${c.sentiment || 'neutral'}">${capitalize(c.sentiment || "neutral")}</span>`;
      tr.appendChild(sentTd);
      // Techniques
      const techTd = document.createElement("td");
      techTd.appendChild(renderChips(c.resolvedTechniques, 3, t => t.name, t => t.categoryColor));
      tr.appendChild(techTd);
      // Providers
      const provTd = document.createElement("td");
      provTd.appendChild(renderChips(c.resolvedProviders.map(p => ({ name: capitalizeProvider(p), color: "#607d8b" })), 3, p => p.name, p => p.color));
      tr.appendChild(provTd);

      tbody.appendChild(tr);

      // Expanded detail row
      if (expandedRow === c.id) {
        const detailTr = document.createElement("tr");
        detailTr.className = "detail-row";
        const detailTd = document.createElement("td");
        detailTd.colSpan = columns.length;
        detailTd.innerHTML = buildCommentaryDetail(c);
        detailTr.appendChild(detailTd);
        tbody.appendChild(detailTr);
      }
    }
    table.appendChild(tbody);
    wrapper.appendChild(table);
    return wrapper;
  }

  // --- Technique pivot table ---
  function renderTechniqueTable() {
    let techRows = [...byTechnique.values()];

    // Apply filters to technique view
    if (filterState.category) {
      techRows = techRows.filter(r => r.technique.categoryName === filterState.category);
    }
    if (filterState.technique) {
      techRows = techRows.filter(r => r.technique.id === filterState.technique);
    }
    if (filterState.provider) {
      techRows = techRows.filter(r => {
        const provs = techToProviders.get(r.technique.id);
        return provs && provs.has(filterState.provider);
      });
    }
    // Filter entries within each technique group for type/sentiment/search
    if (filterState.type || filterState.sentiment || filterState.search) {
      techRows = techRows.map(r => {
        let entries = r.entries;
        if (filterState.type) entries = entries.filter(c => c.type === filterState.type);
        if (filterState.sentiment) entries = entries.filter(c => c.sentiment === filterState.sentiment);
        if (filterState.search) {
          const q = filterState.search.toLowerCase();
          entries = entries.filter(c =>
            (c.title || "").toLowerCase().includes(q) ||
            (c.summary || "").toLowerCase().includes(q) ||
            (c.author || "").toLowerCase().includes(q) ||
            (c.organization || "").toLowerCase().includes(q));
        }
        if (entries.length === 0) return null;
        const sentiments = { positive: 0, negative: 0, mixed: 0, neutral: 0 };
        for (const e of entries) sentiments[e.sentiment || "neutral"]++;
        return { ...r, entries, sentiments };
      }).filter(Boolean);
    }

    // Sort
    const dir = sortState.direction === "asc" ? 1 : -1;
    techRows.sort((a, b) => {
      switch (sortState.column) {
        case "technique": return dir * a.technique.name.localeCompare(b.technique.name);
        case "category": return dir * a.technique.categoryName.localeCompare(b.technique.categoryName);
        case "references": return dir * (a.entries.length - b.entries.length);
        default: return dir * (b.entries.length - a.entries.length);
      }
    });

    const wrapper = document.createElement("div");
    const countEl = document.createElement("div");
    countEl.className = "filter-count";
    countEl.textContent = `Showing ${techRows.length} techniques`;
    countEl.style.marginBottom = "8px";
    wrapper.appendChild(countEl);

    const table = document.createElement("table");
    table.className = "anal-table";

    const columns = [
      { key: "technique", label: "Technique" },
      { key: "category", label: "Category", width: "160px" },
      { key: "references", label: "Refs", width: "60px" },
      { key: "positive", label: "Pos", width: "50px" },
      { key: "mixed", label: "Mix", width: "50px" },
      { key: "negative", label: "Neg", width: "50px" },
      { key: "neutral", label: "Neu", width: "50px" },
      { key: "providers", label: "Providers" }
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
          sortState.direction = "desc";
        }
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
      catTd.innerHTML = `<span class="chip" style="background:${row.technique.categoryColor}20;color:${row.technique.categoryColor};border-color:${row.technique.categoryColor}40">${row.technique.categoryName}</span>`;
      tr.appendChild(catTd);
      addCell(tr, String(row.entries.length));

      for (const s of ["positive", "mixed", "negative", "neutral"]) {
        const td = document.createElement("td");
        const count = row.sentiments[s] || 0;
        if (count > 0) {
          td.innerHTML = `<span class="chip badge-${s}">${count}</span>`;
        } else {
          td.textContent = "-";
          td.style.color = "#ccc";
        }
        tr.appendChild(td);
      }

      // Providers implementing this technique
      const provs = techToProviders.get(row.technique.id);
      const provTd = document.createElement("td");
      if (provs && provs.size > 0) {
        provTd.appendChild(renderChips(
          [...provs].sort().map(p => ({ name: capitalizeProvider(p), color: "#607d8b" })),
          4, p => p.name, p => p.color
        ));
      } else {
        provTd.textContent = "-";
        provTd.style.color = "#ccc";
      }
      tr.appendChild(provTd);

      tbody.appendChild(tr);

      // Expanded: show commentary entries for this technique
      if (expandedRow === row.technique.id) {
        const detailTr = document.createElement("tr");
        detailTr.className = "detail-row";
        const detailTd = document.createElement("td");
        detailTd.colSpan = columns.length;
        let html = `<div style="max-height:400px;overflow-y:auto">`;
        const sorted = [...row.entries].sort((a, b) => (b.dateObj || 0) - (a.dateObj || 0));
        for (const c of sorted) {
          html += `<div style="margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #e0e0e0">
            <div><strong><a href="${escapeHtml(c.url)}" target="_blank">${escapeHtml(c.title)}</a></strong>
            <span class="chip badge-${c.sentiment || 'neutral'}" style="margin-left:6px">${capitalize(c.sentiment || "neutral")}</span>
            <span class="chip badge-${c.type}">${c.typeLabel}</span></div>
            <div style="font-size:12px;color:#666">${escapeHtml(c.author || "")} ${c.organization ? `(${escapeHtml(c.organization)})` : ""} &middot; ${c.date || ""}</div>
            <div style="font-size:12px;color:#555;margin-top:4px">${escapeHtml(c.summary || "")}</div>
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
    if (filterState.technique) result = result.filter(c => c.resolvedTechniques.some(t => t.id === filterState.technique));
    if (filterState.category) result = result.filter(c => c.resolvedTechniques.some(t => t.categoryName === filterState.category));
    if (filterState.type) result = result.filter(c => c.type === filterState.type);
    if (filterState.sentiment) result = result.filter(c => c.sentiment === filterState.sentiment);
    if (filterState.provider) result = result.filter(c => c.resolvedProviders.includes(filterState.provider));
    if (filterState.search) {
      const q = filterState.search.toLowerCase();
      result = result.filter(c =>
        (c.title || "").toLowerCase().includes(q) ||
        (c.summary || "").toLowerCase().includes(q) ||
        (c.author || "").toLowerCase().includes(q) ||
        (c.organization || "").toLowerCase().includes(q));
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
        case "title": return dir * (a.title || "").localeCompare(b.title || "");
        case "organization": return dir * (a.organization || "").localeCompare(b.organization || "");
        case "type": return dir * (a.type || "").localeCompare(b.type || "");
        case "sentiment": return dir * (a.sentiment || "").localeCompare(b.sentiment || "");
        case "techniques": return dir * (a.resolvedTechniques.length - b.resolvedTechniques.length);
        case "providers": return dir * (a.resolvedProviders.length - b.resolvedProviders.length);
        default: return 0;
      }
    });
  }

  // --- CSV export ---
  function exportCSV() {
    const filtered = applySort(applyFilters(enriched));
    const rows = [["Date", "Title", "URL", "Author", "Organization", "Type", "Sentiment", "Techniques", "Providers", "Summary"]];
    for (const c of filtered) {
      rows.push([
        c.date || "",
        c.title || "",
        c.url || "",
        c.author || "",
        c.organization || "",
        c.typeLabel,
        c.sentiment || "",
        c.resolvedTechniques.map(t => t.name).join("; "),
        c.resolvedProviders.map(capitalizeProvider).join("; "),
        (c.summary || "").replace(/"/g, '""')
      ]);
    }
    const csv = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
    downloadFile("commentary-analysis.csv", csv, "text/csv");
  }

  // --- Helpers ---
  function makeSelect(label, options, current, onChange) {
    const wrap = document.createElement("label");
    wrap.textContent = label + " ";
    const sel = document.createElement("select");
    const defOpt = document.createElement("option");
    defOpt.value = "";
    defOpt.textContent = `All ${label}s`;
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

  function buildCommentaryDetail(c) {
    let html = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">`;
    html += `<div>`;
    html += `<div style="margin-bottom:8px"><strong>Summary:</strong> ${escapeHtml(c.summary || "No summary available")}</div>`;
    html += `<div style="margin-bottom:8px"><strong>Author:</strong> ${escapeHtml(c.author || "Unknown")}</div>`;
    html += `<div><strong>Source:</strong> <a href="${escapeHtml(c.url)}" target="_blank">${escapeHtml(truncateText(c.url, 60))}</a></div>`;
    html += `</div><div>`;
    html += `<div style="margin-bottom:8px"><strong>Techniques discussed:</strong></div>`;
    for (const t of c.resolvedTechniques) {
      html += `<div style="margin-bottom:2px"><span class="chip" style="background:${t.categoryColor}18;color:${t.categoryColor};border-color:${t.categoryColor}40">${escapeHtml(t.name)}</span> <span style="font-size:11px;color:#888">${escapeHtml(t.categoryName)}</span></div>`;
    }
    if (c.resolvedProviders.length > 0) {
      html += `<div style="margin-top:8px"><strong>Implementing providers:</strong> ${c.resolvedProviders.map(p => `<span class="chip" style="background:#607d8b18;color:#607d8b;border-color:#607d8b40">${capitalizeProvider(p)}</span>`).join(" ")}</div>`;
    }
    html += `</div></div>`;
    return html;
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
