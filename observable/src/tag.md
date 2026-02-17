---
title: Tag & Review Safety Techniques
style: custom-styles.css
---

# Tag & Review Safety Techniques

Help improve the LLM Safety Mechanisms dataset by reviewing existing technique tags or suggesting new ones. Submissions create a GitHub issue for maintainer review — approved submissions are automatically merged.

---

```js
// --- Data Loading (from GitHub) ---
const ghBase = "https://raw.githubusercontent.com/sashaagafonoff/LLM-Safety-Mechanisms/main/data";
const fetchJson = (name) => fetch(`${ghBase}/${name}`).then((r) => r.json());

const [evidence, techniques, categories, techniqueMap, providers] = await Promise.all([
  fetchJson("evidence.json"),
  fetchJson("techniques.json"),
  fetchJson("categories.json"),
  fetchJson("model_technique_map.json"),
  fetchJson("providers.json")
]);
```

```js
// --- Component Imports ---
import {buildTaggingDataset} from "./components/tag-data.js";
import {createSourceBrowser} from "./components/tag-browser.js";
import {createReviewForm} from "./components/tag-form.js";
```

```js
// --- Build Dataset ---
const tagData = buildTaggingDataset(evidence, techniques, categories, techniqueMap, providers);
```

## Source Documents

Browse source documents by provider. Click a source to review its tags or add new ones.

```js
const selectedSource = view(createSourceBrowser(tagData, d3));
```

---

## Review / Add Tag

```js
display(createReviewForm(selectedSource, tagData, d3));
```

---

<details>
<summary><strong>How this works</strong></summary>

1. **Browse sources** — select a source document to see its existing technique tags
2. **Review existing tags** — confirm accuracy, adjust confidence, or dispute incorrect mappings
3. **Add new tags** — suggest a technique not yet mapped to this source
4. **Submit** — generates a GitHub issue with structured data for maintainer review
5. **Automation** — approved submissions are processed via GitHub Actions and merged as a PR

**Requirements:**
- GitHub account (for creating issues)
- Evidence must quote specific text from the source document

**Confidence levels:**
- **High** — technique is explicitly described with implementation details
- **Medium** — technique is implied or partially described
- **Low** — technique is briefly mentioned without detail

</details>
