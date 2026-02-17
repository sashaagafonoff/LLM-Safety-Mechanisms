// Document viewer for the Tag & Review tool
// Renders flat text with evidence highlighting, supports text selection and scroll navigation

// --- Text normalization for fuzzy matching ---

function normalize(text) {
  return text
    .replace(/\ufb01/g, 'fi').replace(/\ufb02/g, 'fl').replace(/\ufb00/g, 'ff')
    .replace(/\ufb03/g, 'ffi').replace(/\ufb04/g, 'ffl')
    .replace(/[\u2018\u2019\u201A]/g, "'")
    .replace(/[\u201C\u201D\u201E]/g, '"')
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/\u2026/g, '...')
    .replace(/\f/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function normalizeWithMap(text) {
  const map = [];
  let result = '';
  let inWhitespace = false;
  const ligatures = {
    '\ufb01': 'fi', '\ufb02': 'fl', '\ufb00': 'ff',
    '\ufb03': 'ffi', '\ufb04': 'ffl'
  };

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ligatures[ch]) {
      inWhitespace = false;
      for (const c of ligatures[ch]) { map.push(i); result += c; }
      continue;
    }
    if (ch === '\u2026') {
      inWhitespace = false;
      for (let j = 0; j < 3; j++) { map.push(i); result += '.'; }
      continue;
    }
    let c = ch;
    if (/[\u2018\u2019\u201A]/.test(ch)) c = "'";
    else if (/[\u201C\u201D\u201E]/.test(ch)) c = '"';
    else if (/[\u2013\u2014]/.test(ch)) c = '-';
    else if (ch === '\f') c = ' ';

    if (/\s/.test(c)) {
      if (!inWhitespace) { map.push(i); result += ' '; inWhitespace = true; }
      continue;
    }
    inWhitespace = false;
    map.push(i);
    result += c.toLowerCase();
  }

  let start = 0;
  while (start < result.length && result[start] === ' ') start++;
  let end = result.length;
  while (end > start && result[end - 1] === ' ') end--;
  return { norm: result.slice(start, end), map: map.slice(start, end) };
}

function normRangeToOrig(map, normStart, normEnd, fullTextLength) {
  if (normStart >= map.length) return null;
  const origStart = map[normStart];
  const origEnd = normEnd < map.length ? map[normEnd] : fullTextLength;
  return origEnd > origStart ? { start: origStart, end: origEnd } : null;
}

function findEvidence(fullText, snippet) {
  if (!snippet || !fullText) return null;
  const { norm: normFull, map } = normalizeWithMap(fullText);
  const normSnip = normalize(snippet);

  function toOrig(nStart, nEnd) {
    return normRangeToOrig(map, nStart, nEnd, fullText.length);
  }

  // Exact normalized match
  let idx = normFull.indexOf(normSnip);
  if (idx !== -1) return toOrig(idx, idx + normSnip.length);

  // Keyword extraction for verification
  const stopWords = new Set(['the','a','an','and','or','but','in','on','at','to','for','of','with','by','from','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','could','should','may','might','can','this','that','these','those','it','its','we','our','they','their','not','no','also','as','such','more','most','very','all','any','each','than','other','into','about','which','when','where','how','what','who','if','then','so']);
  const snippetKeywords = normSnip.split(/\s+/).filter(w => w.length > 3 && !stopWords.has(w));

  function verifyRegion(candidateStart, candidateEnd) {
    const region = normFull.slice(candidateStart, candidateEnd);
    if (snippetKeywords.length === 0) return true;
    const hits = snippetKeywords.filter(kw => region.includes(kw)).length;
    return hits / snippetKeywords.length >= 0.35;
  }

  function findSentenceEnd(startIdx, maxLen) {
    const searchEnd = Math.min(startIdx + maxLen, normFull.length);
    const region = normFull.slice(startIdx, searchEnd);
    const targetLen = normSnip.length;
    for (let offset = 0; offset < 80 && targetLen + offset < region.length; offset++) {
      const pos = targetLen + offset;
      if (region[pos] === '.' && (pos + 1 >= region.length || region[pos + 1] === ' ')) return startIdx + pos + 1;
      if (region[pos] === '\n') return startIdx + pos;
    }
    return Math.min(startIdx + targetLen, normFull.length);
  }

  // Prefix matching (80-char, then 40-char)
  for (const prefixLen of [80, 40]) {
    if (normSnip.length <= prefixLen) continue;
    const prefix = normSnip.substring(0, prefixLen);
    let searchFrom = 0;
    let bestMatch = null;
    let bestScore = 0;

    while (searchFrom < normFull.length) {
      idx = normFull.indexOf(prefix, searchFrom);
      if (idx === -1) break;
      const endIdx = findSentenceEnd(idx, normSnip.length + 80);
      if (verifyRegion(idx, endIdx)) {
        const region = normFull.slice(idx, endIdx);
        const hits = snippetKeywords.filter(kw => region.includes(kw)).length;
        const score = snippetKeywords.length > 0 ? hits / snippetKeywords.length : 1;
        if (score > bestScore) { bestScore = score; bestMatch = { start: idx, end: endIdx }; }
      }
      searchFrom = idx + 1;
    }
    if (bestMatch) return toOrig(bestMatch.start, bestMatch.end);
  }

  // Keyword density sliding window
  if (snippetKeywords.length >= 3) {
    const windowLen = normSnip.length;
    const step = Math.max(20, Math.floor(windowLen / 4));
    let bestStart = -1, bestEnd = -1, bestScore = 0;

    for (let i = 0; i <= normFull.length - Math.min(windowLen / 2, normFull.length); i += step) {
      const end = Math.min(i + windowLen + 40, normFull.length);
      const region = normFull.slice(i, end);
      const hits = snippetKeywords.filter(kw => region.includes(kw)).length;
      const score = hits / snippetKeywords.length;
      if (score > bestScore && score >= 0.5) { bestScore = score; bestStart = i; bestEnd = end; }
    }
    if (bestStart !== -1) return toOrig(bestStart, bestEnd);
  }

  return null;
}

// --- HTML helpers ---

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeAndFormat(text) {
  let html = escapeHtml(text);
  html = html.replace(/\n{2,}/g, '</p><p style="margin-top:12px;">');
  html = html.replace(/\n/g, '<br>');
  return html;
}

// --- Extract evidence text from snippet entry (handles old string and new object formats) ---

function extractSnippetInfo(snippet) {
  const isObject = typeof snippet === 'object' && snippet !== null;
  const text = isObject ? (snippet.text || '') : snippet;
  const createdBy = isObject ? (snippet.created_by || 'legacy') : (text === 'Manual annotation' ? 'manual' : 'legacy');
  const isActive = isObject ? (snippet.active !== false) : true;
  const deletedBy = isObject ? snippet.deleted_by : null;
  return { text, createdBy, isActive, deletedBy };
}

/**
 * Create a document viewer controller.
 * @param {HTMLElement} docContentEl - The container element for document text
 * @param {HTMLElement} selHintEl - The floating selection hint element
 * @returns viewer API object
 */
export function createDocViewer(docContentEl, selHintEl) {
  const evidenceMatchState = new Map();
  let pendingSelection = null;
  let onSidebarScrollCb = null;

  // Text selection handler
  docContentEl.addEventListener('mouseup', (e) => {
    const sel = window.getSelection();
    const text = sel.toString().trim();
    if (text.length > 10) {
      pendingSelection = { text };
      selHintEl.style.left = (e.clientX + 12) + 'px';
      selHintEl.style.top = (e.clientY - 30) + 'px';
      selHintEl.classList.add('visible');
    } else {
      pendingSelection = null;
      selHintEl.classList.remove('visible');
    }
  });

  // Clear selection when clicking outside doc/sidebar
  document.addEventListener('mousedown', (e) => {
    if (!e.target.closest('.doc-content') && !e.target.closest('.sidebar') && !e.target.closest('.selection-hint')) {
      pendingSelection = null;
      selHintEl.classList.remove('visible');
    }
  });

  return {
    /**
     * Render document text with evidence highlights.
     * @param {string} flatText - Raw document text
     * @param {Array} tags - Technique entries for this document from normalizedMap
     * @param {Map} techById - Technique lookup
     * @param {Map} catById - Category lookup
     */
    render(flatText, tags, techById, catById) {
      evidenceMatchState.clear();

      if (!flatText) {
        docContentEl.innerHTML = '<p style="color:#888;text-align:center;padding:40px;">No document text available.</p>';
        return;
      }

      // Collect evidence ranges
      const ranges = [];
      tags.forEach(tag => {
        const tech = techById.get(tag.techniqueId);
        if (!tech) return;

        const rawEvidence = tag.evidence || [];
        const snippets = Array.isArray(rawEvidence) ? rawEvidence : [rawEvidence];
        const snippetDetails = [];

        snippets.forEach((snippet, sIdx) => {
          const { text, createdBy, isActive, deletedBy } = extractSnippetInfo(snippet);

          if (text === 'Manual annotation') {
            snippetDetails.push({ index: sIdx, state: 'manual', text, createdBy: 'manual', active: true, deletedBy: null });
            return;
          }
          if (!isActive) {
            snippetDetails.push({ index: sIdx, state: 'deleted', text, createdBy, active: false, deletedBy });
            return;
          }

          const match = findEvidence(flatText, text);
          if (match) {
            snippetDetails.push({ index: sIdx, state: 'matched', text, createdBy, active: true, deletedBy: null });
            const cat = catById.get(tech.categoryId);
            ranges.push({
              start: match.start, end: match.end,
              techId: tag.techniqueId, techName: tech.name,
              snippetIndex: sIdx, catName: cat ? cat.name : ''
            });
          } else {
            snippetDetails.push({ index: sIdx, state: 'unmatched', text, createdBy, active: true, deletedBy: null });
          }
        });

        const anyMatched = snippetDetails.some(s => s.state === 'matched' && s.active);
        const anyReal = snippetDetails.some(s => s.state !== 'manual' && s.active);
        evidenceMatchState.set(tag.techniqueId, {
          overall: anyMatched ? 'matched' : (anyReal ? 'unmatched' : 'manual'),
          snippets: snippetDetails,
          techActive: tag.active !== false,
          techDeletedBy: tag.deleted_by || null
        });
      });

      // Sort and merge overlapping ranges
      ranges.sort((a, b) => a.start - b.start);
      const merged = [];
      ranges.forEach(r => {
        if (merged.length > 0) {
          const last = merged[merged.length - 1];
          if (r.start < last.end) {
            last.end = Math.max(last.end, r.end);
            last.refs.push({ techId: r.techId, techName: r.techName, snippetIndex: r.snippetIndex });
            return;
          }
        }
        merged.push({ start: r.start, end: r.end, refs: [{ techId: r.techId, techName: r.techName, snippetIndex: r.snippetIndex }] });
      });

      // Build HTML
      let html = '';
      let cursor = 0;
      merged.forEach(r => {
        if (r.start > cursor) html += escapeAndFormat(flatText.slice(cursor, r.start));
        const labelHtml = r.refs.map(ref =>
          `<span class="ev-tag" data-tech-id="${ref.techId}" data-snippet-idx="${ref.snippetIndex}">${escapeHtml(ref.techName)}</span>`
        ).join('');
        const primaryId = `ev-${r.refs[0].techId}-${r.refs[0].snippetIndex}`;
        const allIds = r.refs.map(ref => `ev-${ref.techId}-${ref.snippetIndex}`).join(' ');
        html += `<span class="evidence-highlight" id="${primaryId}" data-ev-ids="${allIds}" data-tech-ids="${r.refs.map(ref => ref.techId).join(',')}">`
              + escapeHtml(flatText.slice(r.start, r.end))
              + labelHtml
              + `</span>`;
        cursor = r.end;
      });
      if (cursor < flatText.length) html += escapeAndFormat(flatText.slice(cursor));
      docContentEl.innerHTML = html;

      // Click on evidence tags in document → scroll sidebar
      docContentEl.querySelectorAll('.ev-tag').forEach(tag => {
        tag.addEventListener('click', (e) => {
          e.stopPropagation();
          if (onSidebarScrollCb) onSidebarScrollCb(tag.dataset.techId);
        });
      });
    },

    /** Scroll to an evidence highlight and pulse it */
    scrollToEvidence(techId, snippetIndex) {
      let el = document.getElementById(`ev-${techId}-${snippetIndex}`);
      if (!el) {
        const target = `ev-${techId}-${snippetIndex}`;
        el = document.querySelector(`[data-ev-ids*="${target}"]`);
      }
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.remove('pulse');
        void el.offsetWidth;
        el.classList.add('pulse');
      }
    },

    getPendingSelection() { return pendingSelection; },
    clearPendingSelection() {
      pendingSelection = null;
      selHintEl.classList.remove('visible');
    },
    setPendingSelection(sel) { pendingSelection = sel; },
    getEvidenceMatchState() { return evidenceMatchState; },

    /** Register callback for when user clicks an ev-tag in the document */
    onEvTagClick(cb) { onSidebarScrollCb = cb; }
  };
}
