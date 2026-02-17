// GitHub issue URL builders for the Tag & Review tool
// Three actions: delete_tag, link_evidence, add_new_tag

const REPO_URL = "https://github.com/sashaagafonoff/LLM-Safety-Mechanisms";
const MAX_EVIDENCE_LEN = 2000; // keep URL under ~8KB

function truncate(text, max) {
  if (!text || text.length <= max) return text;
  return text.slice(0, max) + "...";
}

function buildUrl(title, body) {
  const labels = "data-review";
  return `${REPO_URL}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}&labels=${encodeURIComponent(labels)}`;
}

function buildBody(payload, summary) {
  return `## Data Review Submission

<!-- MACHINE_READABLE: Do not edit the JSON block below -->
\`\`\`json
${JSON.stringify(payload, null, 2)}
\`\`\`

## Summary

**Source:** ${payload.source_title}
**Provider:** ${payload.provider_name}
**Technique:** ${payload.technique_name}

${summary}

### Evidence

> ${truncate(payload.evidence_text, MAX_EVIDENCE_LEN)}

---

**Submitted by:** @${payload.github_username}

Add the \`accepted\` label to trigger automated processing.`;
}

/**
 * Build issue URL for deleting (disputing) an existing tag.
 */
export function buildDeleteIssueUrl({ sourceId, sourceTitle, providerName, techniqueId, techniqueName, evidenceText, githubUsername }) {
  const payload = {
    version: 2,
    action: "delete_tag",
    source_id: sourceId,
    source_title: sourceTitle,
    provider_name: providerName,
    technique_id: techniqueId,
    technique_name: techniqueName,
    evidence_text: truncate(evidenceText, MAX_EVIDENCE_LEN),
    github_username: githubUsername,
    timestamp: new Date().toISOString()
  };
  const title = `[Tag] Delete ${techniqueName} from ${sourceTitle}`;
  const summary = `**Action:** Remove tag — contributor considers this mapping incorrect.`;
  return buildUrl(title, buildBody(payload, summary));
}

/**
 * Build issue URL for linking existing evidence to another technique.
 */
export function buildLinkIssueUrl({ sourceId, sourceTitle, providerName, techniqueId, techniqueName, evidenceText, githubUsername }) {
  const payload = {
    version: 2,
    action: "link_evidence",
    source_id: sourceId,
    source_title: sourceTitle,
    provider_name: providerName,
    technique_id: techniqueId,
    technique_name: techniqueName,
    evidence_text: truncate(evidenceText, MAX_EVIDENCE_LEN),
    github_username: githubUsername,
    timestamp: new Date().toISOString()
  };
  const title = `[Tag] Link evidence to ${techniqueName} in ${sourceTitle}`;
  const summary = `**Action:** Link existing evidence passage to an additional technique.`;
  return buildUrl(title, buildBody(payload, summary));
}

/**
 * Build issue URL for adding a new tag from selected text.
 */
export function buildNewTagIssueUrl({ sourceId, sourceTitle, providerName, techniqueId, techniqueName, evidenceText, githubUsername }) {
  const payload = {
    version: 2,
    action: "add_new_tag",
    source_id: sourceId,
    source_title: sourceTitle,
    provider_name: providerName,
    technique_id: techniqueId,
    technique_name: techniqueName,
    evidence_text: truncate(evidenceText, MAX_EVIDENCE_LEN),
    github_username: githubUsername,
    timestamp: new Date().toISOString()
  };
  const title = `[Tag] Add ${techniqueName} to ${sourceTitle}`;
  const summary = `**Action:** Add new technique tag based on selected evidence text.`;
  return buildUrl(title, buildBody(payload, summary));
}
