// Review/add form component for the tagging tool
// Generates structured GitHub Issue URLs for submission
import {html} from "htl";

const REPO_URL = "https://github.com/sashaagafonoff/LLM-Safety-Mechanisms";

export function createReviewForm(selectedSource, tagData, d3) {
  if (!selectedSource) {
    return html`<div style="padding: 30px; text-align: center; color: #999; font-family: sans-serif; font-size: 14px; border: 2px dashed #ddd; border-radius: 8px;">
      Select a source document above to review or add tags.
    </div>`;
  }

  const {techniques, categories, techniquesByCategory} = tagData;
  const src = selectedSource;

  // Track existing technique IDs to exclude from "add" dropdown
  const existingTechIds = new Set(src.existingTags.map((t) => t.techniqueId));

  const container = html`<div style="font-family: sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background: white;">
    <h3 style="margin: 0 0 4px 0; font-size: 15px; color: #222;">${src.title}</h3>
    <div style="font-size: 12px; color: #666; margin-bottom: 12px;">
      ${src.providerName} &middot; <a href="${src.url}" target="_blank" style="color: #1976D2;">${src.url.length > 60 ? src.url.slice(0, 57) + "..." : src.url}</a>
    </div>

    <!-- Mode toggle -->
    <div style="display: flex; gap: 12px; margin-bottom: 14px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
      <label style="cursor: pointer; font-size: 13px;">
        <input type="radio" name="mode" value="review" checked style="margin-right: 4px;">
        Review Existing Tag
      </label>
      <label style="cursor: pointer; font-size: 13px;">
        <input type="radio" name="mode" value="add" style="margin-right: 4px;">
        Add New Tag
      </label>
    </div>

    <!-- Review mode panel -->
    <div id="review-panel">
      <label style="font-size: 12px; font-weight: 600; color: #555; display: block; margin-bottom: 4px;">Select technique to review:</label>
      <select id="existing-tag-select" style="width: 100%; padding: 6px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; margin-bottom: 10px;">
        ${src.existingTags.length === 0
          ? html`<option value="" disabled selected>No existing tags — use "Add New Tag" instead</option>`
          : src.existingTags.map((t) => html`<option value="${t.techniqueId}">${t.techniqueName} (${t.confidence})</option>`)}
      </select>
      <div style="margin-bottom: 10px;">
        <label style="font-size: 12px; font-weight: 600; color: #555; display: block; margin-bottom: 4px;">Action:</label>
        <label style="display: block; font-size: 13px; margin-bottom: 4px; cursor: pointer;">
          <input type="radio" name="review-action" value="confirm" checked style="margin-right: 4px;">
          Confirm (agree with current rating)
        </label>
        <label style="display: block; font-size: 13px; margin-bottom: 4px; cursor: pointer;">
          <input type="radio" name="review-action" value="adjust_confidence" style="margin-right: 4px;">
          Adjust confidence to:
          <select id="adjust-confidence" style="padding: 2px 6px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px; margin-left: 4px;">
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </label>
        <label style="display: block; font-size: 13px; margin-bottom: 4px; cursor: pointer;">
          <input type="radio" name="review-action" value="dispute" style="margin-right: 4px;">
          Dispute (mark as incorrect)
        </label>
      </div>
    </div>

    <!-- Add mode panel -->
    <div id="add-panel" style="display: none;">
      <label style="font-size: 12px; font-weight: 600; color: #555; display: block; margin-bottom: 4px;">Category:</label>
      <select id="add-category" style="width: 100%; padding: 6px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; margin-bottom: 10px;">
        <option value="">Select category...</option>
        ${categories.map((c) => html`<option value="${c.id}">${c.name}</option>`)}
      </select>

      <label style="font-size: 12px; font-weight: 600; color: #555; display: block; margin-bottom: 4px;">Technique:</label>
      <select id="add-technique" style="width: 100%; padding: 6px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; margin-bottom: 10px;">
        <option value="">Select category first...</option>
      </select>

      <label style="font-size: 12px; font-weight: 600; color: #555; display: block; margin-bottom: 4px;">Confidence:</label>
      <select id="add-confidence" style="width: 100%; padding: 6px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; margin-bottom: 10px;">
        <option value="High">High — explicitly described in source</option>
        <option value="Medium" selected>Medium — implied or partially described</option>
        <option value="Low">Low — briefly mentioned</option>
      </select>
    </div>

    <!-- Common fields -->
    <div style="border-top: 1px solid #eee; padding-top: 12px; margin-top: 4px;">
      <label style="font-size: 12px; font-weight: 600; color: #555; display: block; margin-bottom: 4px;">
        Evidence <span style="color: #c62828;">*</span>
        <span style="font-weight: 400; color: #999;"> — quote specific text from the source document</span>
      </label>
      <textarea id="evidence-text" rows="4" placeholder="Paste the relevant excerpt from the source document here..." style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; resize: vertical; box-sizing: border-box;"></textarea>

      <label style="font-size: 12px; font-weight: 600; color: #555; display: block; margin-bottom: 4px; margin-top: 10px;">
        Additional context <span style="font-weight: 400; color: #999;">(optional)</span>
      </label>
      <textarea id="context-text" rows="2" placeholder="Why does this evidence support the tag? Any relevant notes..." style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; resize: vertical; box-sizing: border-box;"></textarea>
    </div>

    <div id="validation-msg" style="color: #c62828; font-size: 12px; margin-top: 8px; display: none;"></div>

    <button id="submit-btn" style="
      margin-top: 14px; padding: 10px 24px; background: #1976D2; color: white;
      border: none; border-radius: 6px; font-size: 14px; font-weight: 600;
      cursor: pointer; width: 100%;
    ">Submit to GitHub Issues</button>
    <div style="font-size: 11px; color: #999; margin-top: 6px; text-align: center;">
      Opens a pre-filled GitHub issue in a new tab. Requires a GitHub account.
    </div>
  </div>`;

  // Element references
  const modeRadios = container.querySelectorAll('input[name="mode"]');
  const reviewPanel = container.querySelector("#review-panel");
  const addPanel = container.querySelector("#add-panel");
  const addCategorySelect = container.querySelector("#add-category");
  const addTechniqueSelect = container.querySelector("#add-technique");
  const submitBtn = container.querySelector("#submit-btn");
  const validationMsg = container.querySelector("#validation-msg");

  // Mode toggle
  for (const radio of modeRadios) {
    radio.addEventListener("change", () => {
      const mode = container.querySelector('input[name="mode"]:checked').value;
      reviewPanel.style.display = mode === "review" ? "" : "none";
      addPanel.style.display = mode === "add" ? "" : "none";
    });
  }

  // Category → technique dropdown
  addCategorySelect.addEventListener("change", () => {
    const catId = addCategorySelect.value;
    addTechniqueSelect.innerHTML = "";
    if (!catId) {
      addTechniqueSelect.appendChild(html`<option value="">Select category first...</option>`);
      return;
    }
    const cat = categories.find((c) => c.id === catId);
    const catName = cat ? cat.name : catId;
    const techs = (techniquesByCategory.get(catName) || []).filter((t) => !existingTechIds.has(t.id));
    if (techs.length === 0) {
      addTechniqueSelect.appendChild(html`<option value="" disabled>All techniques in this category are already tagged</option>`);
    } else {
      addTechniqueSelect.appendChild(html`<option value="">Select technique...</option>`);
      for (const t of techs) {
        addTechniqueSelect.appendChild(html`<option value="${t.id}">${t.name}</option>`);
      }
    }
  });

  // Submit
  submitBtn.addEventListener("click", () => {
    const mode = container.querySelector('input[name="mode"]:checked').value;
    const evidenceText = container.querySelector("#evidence-text").value.trim();
    const contextText = container.querySelector("#context-text").value.trim();

    // Validate
    if (evidenceText.length < 20) {
      showValidation("Evidence must be at least 20 characters. Quote specific text from the source document.");
      return;
    }

    let payload;
    if (mode === "review") {
      const tagSelect = container.querySelector("#existing-tag-select");
      const techniqueId = tagSelect.value;
      if (!techniqueId) {
        showValidation("Select a technique to review.");
        return;
      }
      const action = container.querySelector('input[name="review-action"]:checked').value;
      const tag = src.existingTags.find((t) => t.techniqueId === techniqueId);
      const newConfidence = action === "adjust_confidence"
        ? container.querySelector("#adjust-confidence").value
        : null;

      payload = {
        version: 1,
        submission_type: "review_existing",
        source_id: src.id,
        source_title: src.title,
        provider_name: src.providerName,
        source_url: src.url,
        technique_id: techniqueId,
        technique_name: tag ? tag.techniqueName : techniqueId,
        category_name: tag ? tag.categoryName : "",
        action,
        new_confidence: newConfidence,
        evidence_text: evidenceText,
        additional_context: contextText || null,
        timestamp: new Date().toISOString()
      };
    } else {
      const techniqueId = addTechniqueSelect.value;
      if (!techniqueId) {
        showValidation("Select a technique to add.");
        return;
      }
      const tech = techniques.find((t) => t.id === techniqueId);
      const cat = categories.find((c) => c.id === addCategorySelect.value);
      const confidence = container.querySelector("#add-confidence").value;

      payload = {
        version: 1,
        submission_type: "add_new_tag",
        source_id: src.id,
        source_title: src.title,
        provider_name: src.providerName,
        source_url: src.url,
        technique_id: techniqueId,
        technique_name: tech ? tech.name : techniqueId,
        category_name: cat ? cat.name : "",
        action: "add",
        new_confidence: confidence,
        evidence_text: evidenceText,
        additional_context: contextText || null,
        timestamp: new Date().toISOString()
      };
    }

    hideValidation();
    const url = buildGitHubIssueUrl(payload);
    window.open(url, "_blank");
  });

  function showValidation(msg) {
    validationMsg.textContent = msg;
    validationMsg.style.display = "";
  }
  function hideValidation() {
    validationMsg.style.display = "none";
  }

  return container;
}

function buildGitHubIssueUrl(payload) {
  const actionLabels = {
    confirm: "Confirm",
    adjust_confidence: "Adjust confidence",
    dispute: "Dispute",
    add: "Add"
  };

  const title = payload.submission_type === "add_new_tag"
    ? `[Tag] Add ${payload.technique_name} to ${payload.source_title}`
    : `[Review] ${actionLabels[payload.action] || payload.action} ${payload.technique_name} in ${payload.source_title}`;

  const body = buildIssueBody(payload, actionLabels);
  const labels = "data-review";
  return `${REPO_URL}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}&labels=${encodeURIComponent(labels)}`;
}

function buildIssueBody(payload, actionLabels) {
  const actionDesc = payload.submission_type === "add_new_tag"
    ? `**Adding new tag:** ${payload.technique_name} (${payload.new_confidence} confidence)`
    : `**${actionLabels[payload.action]}:** ${payload.technique_name}${payload.new_confidence ? ` → ${payload.new_confidence} confidence` : ""}`;

  return `## Data Review Submission

<!-- MACHINE_READABLE: Do not edit the JSON block below -->
\`\`\`json
${JSON.stringify(payload, null, 2)}
\`\`\`

## Summary

**Source:** ${payload.source_title}
**Provider:** ${payload.provider_name}
**URL:** ${payload.source_url}

${actionDesc}
**Category:** ${payload.category_name}

### Evidence

> ${payload.evidence_text}

${payload.additional_context ? `### Additional Context\n\n${payload.additional_context}\n` : ""}
---

**Reviewer checklist:**
- [ ] Evidence is accurate and from the cited source
- [ ] Technique classification is appropriate
- [ ] Confidence level matches evidence strength
- [ ] No duplicate mapping exists

Add the \`approved\` label to trigger automated processing.`;
}
