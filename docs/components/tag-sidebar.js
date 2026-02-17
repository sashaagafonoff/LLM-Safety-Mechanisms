// Technique sidebar for the Tag & Review tool
// Displays techniques grouped by category with evidence rows, delete buttons, and click interactions

/**
 * Create sidebar controller.
 * @param {HTMLElement} sidebarListEl - Container for technique list
 * @param {Map} techByCategory - Map of category name → technique array
 * @param {Map} catById - Category lookup
 * @returns sidebar API object
 */
export function createSidebar(sidebarListEl, techByCategory, catById) {
  let onTechClickCb = null;
  let onDeleteClickCb = null;
  let onEvidenceRowClickCb = null;

  // Build category color lookup
  const catColors = {};
  for (const [, cat] of catById) {
    catColors[cat.name] = cat.color || '#888';
  }

  // Build static sidebar structure
  function buildStructure() {
    sidebarListEl.innerHTML = '';
    const sorted = Array.from(techByCategory.entries()).sort((a, b) => a[0].localeCompare(b[0]));

    sorted.forEach(([catName, techs]) => {
      const group = document.createElement('div');
      group.className = 'cat-group';

      const header = document.createElement('div');
      header.className = 'cat-header';
      header.innerHTML = `<span class="cat-dot" style="background:${catColors[catName] || '#888'}"></span>${catName}`;
      group.appendChild(header);

      techs.sort((a, b) => a.name.localeCompare(b.name)).forEach(t => {
        const item = document.createElement('div');
        item.className = 'tech-item';
        item.dataset.techId = t.id;

        item.innerHTML = `
          <div class="tech-body">
            <div class="tech-name">${escapeHtml(t.name)}</div>
            <div class="tech-evidence-list" data-tech-ev="${t.id}"></div>
          </div>
        `;

        // Technique name click — triggers link/add action
        item.querySelector('.tech-name').addEventListener('click', (e) => {
          e.stopPropagation();
          if (onTechClickCb) onTechClickCb(t.id, t.name);
        });

        group.appendChild(item);
      });

      sidebarListEl.appendChild(group);
    });
  }

  buildStructure();

  return {
    /**
     * Update sidebar to reflect current document's tags.
     * @param {Array} tags - Technique entries for current doc
     * @param {Map} evidenceMatchState - From viewer
     * @param {Map} techById - Technique lookup
     */
    update(tags, evidenceMatchState, techById) {
      const taggedIds = new Set();
      const tagMap = new Map();
      if (tags) {
        tags.forEach(t => {
          if (t.active !== false) taggedIds.add(t.techniqueId);
          tagMap.set(t.techniqueId, t);
        });
      }

      sidebarListEl.querySelectorAll('.tech-item').forEach(item => {
        const techId = item.dataset.techId;
        const tagged = taggedIds.has(techId);
        item.classList.toggle('tagged', tagged);

        const matchInfo = evidenceMatchState.get(techId);
        item.classList.toggle('ev-missing-item', tagged && matchInfo?.overall === 'unmatched');

        // Evidence list
        const listEl = item.querySelector('.tech-evidence-list');
        listEl.innerHTML = '';

        if (tagged && matchInfo && matchInfo.snippets.length > 0) {
          listEl.style.display = '';

          matchInfo.snippets.forEach(snip => {
            if (!snip.active && snip.state === 'deleted') return; // hide deleted

            const row = document.createElement('div');
            row.className = 'ev-row';

            const link = document.createElement('span');
            link.className = 'ev-link';

            // Provenance marker
            const provMap = { 'nlu': 'N', 'llm': 'L', 'manual': 'M', 'legacy': '?' };
            const prov = provMap[snip.createdBy] || '?';

            const preview = snip.text === 'Manual annotation'
              ? snip.text
              : snip.text.substring(0, 45) + (snip.text.length > 45 ? '\u2026' : '');

            if (snip.state === 'matched') {
              link.innerHTML = `<span class="prov-marker prov-${snip.createdBy}">(${prov})</span> \u25CF ${escapeHtml(preview)}`;
              link.classList.add('has-evidence', 'clickable');
              // Click evidence text → set pending selection from this evidence, scroll viewer
              link.addEventListener('click', (e) => {
                e.stopPropagation();
                if (onEvidenceRowClickCb) onEvidenceRowClickCb(techId, snip.index, snip.text);
              });
            } else if (snip.state === 'unmatched') {
              link.innerHTML = `<span class="prov-marker prov-${snip.createdBy}">(${prov})</span> \u26A0 ${escapeHtml(preview)}`;
              link.classList.add('ev-missing');
              // Still allow clicking unmatched evidence to set as pending selection
              link.addEventListener('click', (e) => {
                e.stopPropagation();
                if (onEvidenceRowClickCb) onEvidenceRowClickCb(techId, snip.index, snip.text);
              });
            } else {
              link.innerHTML = `<span class="prov-marker prov-manual">(M)</span> \u25CB ${escapeHtml(preview)}`;
              link.classList.add('ev-manual');
            }

            // Delete button
            const remove = document.createElement('span');
            remove.className = 'ev-remove';
            remove.textContent = '\u2715';
            remove.title = 'Remove this tag (creates GitHub issue)';
            remove.addEventListener('click', (e) => {
              e.stopPropagation();
              if (onDeleteClickCb) onDeleteClickCb(techId, snip.index, snip.text);
            });

            row.appendChild(link);
            row.appendChild(remove);
            listEl.appendChild(row);
          });
        } else {
          listEl.style.display = 'none';
        }
      });
    },

    /** Register callback: technique name clicked (for link/add actions) */
    onTechniqueClick(cb) { onTechClickCb = cb; },

    /** Register callback: X button clicked on evidence row */
    onDeleteClick(cb) { onDeleteClickCb = cb; },

    /** Register callback: evidence row text clicked */
    onEvidenceRowClick(cb) { onEvidenceRowClickCb = cb; },

    /** Scroll sidebar to a technique and flash it */
    scrollToItem(techId) {
      const item = sidebarListEl.querySelector(`.tech-item[data-tech-id="${techId}"]`);
      if (item) {
        item.scrollIntoView({ behavior: 'smooth', block: 'center' });
        item.classList.remove('flash-highlight');
        void item.offsetWidth;
        item.classList.add('flash-highlight');
      }
    }
  };
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
