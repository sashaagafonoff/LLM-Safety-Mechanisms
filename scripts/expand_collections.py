#!/usr/bin/env python3
"""
Expand Commentary & Incidents Collections via LLM Web Search

Uses Claude's built-in web_search tool to discover and ETL new third-party
commentary and safety incident entries into data/commentary.json and
data/incidents.json.

Usage:
    python scripts/expand_collections.py                          # All providers, both types
    python scripts/expand_collections.py --provider openai        # Single provider
    python scripts/expand_collections.py --type commentary        # Commentary only
    python scripts/expand_collections.py --type incidents         # Incidents only
    python scripts/expand_collections.py --write                  # Persist (default is a safe dry run)
    python scripts/expand_collections.py --model haiku            # Use cheaper model

Note: writes are OFF by default (safe dry run). LLM-sourced records use a distinct
`webllm-` id namespace and must be reviewed before persisting with --write.

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - anthropic package installed: pip install anthropic
"""

import json
import os
import sys
import re
import argparse
import time
from pathlib import Path
from difflib import SequenceMatcher

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / "API_key.env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed")
    print("Install with: pip install anthropic")
    sys.exit(1)

# Paths
DATA_DIR = Path("data")
COMMENTARY_PATH = DATA_DIR / "commentary.json"
INCIDENTS_PATH = DATA_DIR / "incidents.json"
PROVIDERS_PATH = DATA_DIR / "providers.json"
TECHNIQUES_PATH = DATA_DIR / "techniques.json"
MODELS_PATH = DATA_DIR / "models.json"
RISK_AREAS_PATH = DATA_DIR / "risk_areas.json"

# Model configuration
MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}

VALID_COMMENTARY_TYPES = ["academic_paper", "report", "blog_post", "audit", "news_analysis", "conference_talk"]
VALID_SENTIMENTS = ["positive", "negative", "neutral", "mixed"]
VALID_SEVERITIES = ["critical", "high", "medium", "low"]
VALID_SOURCE_TYPES = ["news", "blog", "research", "advisory"]


class CollectionExpander:
    def __init__(self, model="sonnet"):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set")
            sys.exit(1)

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = MODEL_MAP.get(model, model)
        print(f"Using model: {self.model}")

        # Load reference data
        self.providers = json.loads(PROVIDERS_PATH.read_text(encoding="utf-8"))
        self.techniques = json.loads(TECHNIQUES_PATH.read_text(encoding="utf-8"))
        models_data = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
        self.models = models_data.get("models", models_data) if isinstance(models_data, dict) else models_data
        self.risk_areas = json.loads(RISK_AREAS_PATH.read_text(encoding="utf-8"))

        # Build lookup sets
        self.provider_ids = {p["id"] for p in self.providers}
        self.technique_ids = {t["id"] for t in self.techniques}
        self.model_ids = {m["id"] for m in self.models}
        self.risk_area_ids = {r["id"] for r in self.risk_areas}

        # Build provider → name and provider → models maps
        self.provider_names = {p["id"]: p["name"] for p in self.providers}
        self.provider_models = {}
        for m in self.models:
            pid = m.get("providerId")
            if pid:
                self.provider_models.setdefault(pid, []).append(m["id"])

        # Load existing collections
        self.commentary = json.loads(COMMENTARY_PATH.read_text(encoding="utf-8"))
        self.incidents = json.loads(INCIDENTS_PATH.read_text(encoding="utf-8"))

        # Existing URLs for deduplication
        self.existing_commentary_urls = {e["url"] for e in self.commentary}
        self.existing_commentary_titles = [e["title"].lower().strip() for e in self.commentary]
        self.existing_incident_urls = set()
        self.existing_incident_titles = [e["title"].lower().strip() for e in self.incidents]
        for inc in self.incidents:
            for src in inc.get("sources", []):
                self.existing_incident_urls.add(src["url"])

        # Next IDs
        self._next_commentary_id = self._max_id(self.commentary, "webllm-commentary") + 1
        self._next_incident_id = self._max_id(self.incidents, "webllm-incident") + 1

        # Counters
        self.stats = {"commentary_added": 0, "incidents_added": 0, "commentary_skipped": 0, "incidents_skipped": 0}

    def _max_id(self, entries, prefix):
        """Max trailing number among ids in the given namespace prefix only.

        LLM-sourced records use a distinct `webllm-` namespace so their counter
        never collides with manual/AIID (`aiid-*`) ids (REFACTOR §5.6).
        """
        max_num = 0
        for e in entries:
            eid = e.get("id", "")
            if not eid.startswith(prefix):
                continue
            match = re.search(r"(\d+)$", eid)
            if match:
                max_num = max(max_num, int(match.group(1)))
        return max_num

    def _next_commentary_num(self):
        num = self._next_commentary_id
        self._next_commentary_id += 1
        return f"webllm-commentary-{num:03d}"

    def _next_incident_num(self):
        num = self._next_incident_id
        self._next_incident_id += 1
        return f"webllm-incident-{num:03d}"

    def _technique_list_str(self):
        lines = []
        for t in self.techniques:
            lines.append(f"  {t['id']}: {t['name']}")
        return "\n".join(lines)

    def _risk_area_list_str(self):
        return ", ".join(r["id"] for r in self.risk_areas)

    def _call_claude(self, prompt, max_retries=2):
        """Call Claude with web_search tool, return text response."""
        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=16384,
                    tools=[{
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": 10
                    }],
                    messages=[{"role": "user", "content": prompt}]
                )
                # Extract text blocks from response
                text_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                return "\n".join(text_parts)
            except anthropic.APIError as e:
                if "rate_limit" in str(e).lower():
                    print(f"    Rate limited, waiting 60s...")
                    time.sleep(60)
                    continue
                raise
            except Exception as e:
                if attempt < max_retries:
                    print(f"    Error: {e}, retrying in 10s...")
                    time.sleep(10)
                    continue
                raise
        return ""

    def _parse_json_response(self, text):
        """Extract JSON array from LLM response text."""
        if not text:
            return []

        # Try to find JSON array in response
        # Look for ```json ... ``` blocks first
        match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON array
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return []

    def _is_duplicate_title(self, title, existing_titles):
        """Check if a title is too similar to an existing one."""
        title_lower = title.lower().strip()
        for existing in existing_titles:
            ratio = SequenceMatcher(None, title_lower, existing).ratio()
            if ratio > 0.80:
                return True
        return False

    def expand_commentary(self, provider_id):
        """Discover new commentary entries for a provider."""
        provider_name = self.provider_names[provider_id]

        prompt = f"""You are a research assistant building a dataset of third-party analysis about LLM safety mechanisms.

Search the web for academic papers, independent audits, blog posts, and expert analyses that discuss **{provider_name}**'s LLM safety techniques. Focus on substantive analysis of specific safety mechanisms — skip press releases, product announcements, marketing materials, and the provider's own documentation.

Run multiple searches such as:
- "{provider_name} LLM safety analysis"
- "{provider_name} AI alignment research paper"
- "{provider_name} model safety audit"
- "{provider_name} AI safety criticism"
- "{provider_name} red teaming results"

For each result found, extract a structured entry. Only include entries with substantive third-party analysis of specific safety techniques.

Valid technique IDs (only use these exact IDs):
{self._technique_list_str()}

Return ONLY a JSON array (no other text) with entries matching this schema:
```json
[
  {{
    "title": "Full title of the paper/article",
    "url": "https://...",
    "author": "Author names",
    "organization": "Author's organization",
    "date": "YYYY-MM-DD",
    "type": "academic_paper|report|blog_post|audit|news_analysis|conference_talk",
    "techniqueIds": ["tech-xxx", "tech-yyy"],
    "summary": "2-3 sentence summary of the analysis and its findings about safety techniques",
    "sentiment": "positive|negative|neutral|mixed"
  }}
]
```

Rules:
- Only use techniqueIds from the list above — do not invent new ones
- Date must be in YYYY-MM-DD format (use approximate date if exact date unknown)
- type must be one of: academic_paper, report, blog_post, audit, news_analysis, conference_talk
- sentiment reflects the analysis's assessment of the safety technique(s): positive (effective), negative (flawed/insufficient), neutral (descriptive), mixed (both pros and cons)
- Aim for 3-8 high-quality, diverse entries
- Each entry must have a real, accessible URL
- Do NOT include {provider_name}'s own papers about their own techniques — focus on third-party analysis"""

        response = self._call_claude(prompt)
        entries = self._parse_json_response(response)

        new_entries = []
        for entry in entries:
            # Basic validation
            if not entry.get("title") or not entry.get("url"):
                continue

            # Dedup by URL
            if entry["url"] in self.existing_commentary_urls:
                self.stats["commentary_skipped"] += 1
                continue

            # Dedup by title
            if self._is_duplicate_title(entry["title"], self.existing_commentary_titles):
                self.stats["commentary_skipped"] += 1
                continue

            # Validate and filter technique IDs
            valid_techs = [t for t in entry.get("techniqueIds", []) if t in self.technique_ids]
            if not valid_techs:
                continue
            entry["techniqueIds"] = valid_techs

            # Validate type and sentiment
            if entry.get("type") not in VALID_COMMENTARY_TYPES:
                entry["type"] = "blog_post"
            if entry.get("sentiment") not in VALID_SENTIMENTS:
                entry["sentiment"] = "neutral"

            # Assign ID
            entry["id"] = self._next_commentary_num()

            # Ensure all fields present
            clean = {
                "id": entry["id"],
                "title": entry["title"].strip(),
                "url": entry["url"].strip(),
                "author": entry.get("author", "Unknown").strip(),
                "organization": entry.get("organization", "Unknown").strip(),
                "date": entry.get("date", "2024-01-01"),
                "type": entry["type"],
                "techniqueIds": entry["techniqueIds"],
                "summary": entry.get("summary", "").strip(),
                "sentiment": entry["sentiment"]
            }

            new_entries.append(clean)
            self.existing_commentary_urls.add(clean["url"])
            self.existing_commentary_titles.append(clean["title"].lower().strip())

        return new_entries

    def expand_incidents(self, provider_id):
        """Discover new incident entries for a provider."""
        provider_name = self.provider_names[provider_id]
        model_list = self.provider_models.get(provider_id, [])
        model_str = ", ".join(model_list) if model_list else "(no specific models listed)"

        prompt = f"""You are a safety researcher building a dataset of documented AI safety incidents.

Search the web for confirmed safety incidents, failures, jailbreaks, data leaks, harmful outputs, and security vulnerabilities involving **{provider_name}**'s AI models. Focus on well-documented incidents with credible sources.

Run multiple searches such as:
- "{provider_name} AI safety incident"
- "{provider_name} AI jailbreak"
- "{provider_name} model failure"
- "{provider_name} AI harmful output"
- "{provider_name} AI data leak"
- "{provider_name} AI bias incident"

Valid reference IDs (only use these exact IDs):

Provider ID: {provider_id}

Models for this provider: {model_str}

Technique IDs (techniques that may have been insufficient):
{self._technique_list_str()}

Risk area IDs: {self._risk_area_list_str()}

Return ONLY a JSON array (no other text) with entries matching this schema:
```json
[
  {{
    "title": "Brief incident title",
    "date": "YYYY-MM-DD",
    "description": "Detailed description of what happened, 2-4 sentences",
    "severity": "critical|high|medium|low",
    "providerIds": ["{provider_id}"],
    "modelIds": ["model-id-if-known"],
    "techniqueIds": ["tech-xxx"],
    "riskAreaIds": ["risk_area_id"],
    "sources": [
      {{
        "url": "https://...",
        "title": "Source article title",
        "date": "YYYY-MM-DD",
        "type": "news|blog|research|advisory"
      }}
    ],
    "status": "confirmed"
  }}
]
```

Rules:
- Only use IDs from the lists above — do not invent new ones
- modelIds should be empty array [] if the specific model isn't known
- techniqueIds should reference techniques that were insufficient or failed in the incident
- severity: critical (widespread harm or data breach), high (significant safety failure), medium (notable but contained), low (minor issue)
- Each entry must have at least one source with a real URL
- Only include confirmed, well-documented incidents — not rumors or speculation
- Aim for 2-5 incidents per provider (only real, documented ones)
- If no credible incidents are found for this provider, return an empty array []"""

        response = self._call_claude(prompt)
        entries = self._parse_json_response(response)

        new_entries = []
        for entry in entries:
            # Basic validation
            if not entry.get("title") or not entry.get("sources"):
                continue

            sources = entry.get("sources", [])
            if not sources:
                continue

            # Check if any source URL is already known
            entry_urls = {s.get("url", "") for s in sources}
            if entry_urls & self.existing_incident_urls:
                self.stats["incidents_skipped"] += 1
                continue

            # Dedup by title
            if self._is_duplicate_title(entry["title"], self.existing_incident_titles):
                self.stats["incidents_skipped"] += 1
                continue

            # Validate IDs
            valid_providers = [p for p in entry.get("providerIds", []) if p in self.provider_ids]
            if not valid_providers:
                valid_providers = [provider_id]
            entry["providerIds"] = valid_providers

            entry["modelIds"] = [m for m in entry.get("modelIds", []) if m in self.model_ids]
            entry["techniqueIds"] = [t for t in entry.get("techniqueIds", []) if t in self.technique_ids]
            entry["riskAreaIds"] = [r for r in entry.get("riskAreaIds", []) if r in self.risk_area_ids]

            if not entry["riskAreaIds"]:
                continue

            # Validate severity
            if entry.get("severity") not in VALID_SEVERITIES:
                entry["severity"] = "medium"

            # Validate sources
            clean_sources = []
            for src in sources:
                if not src.get("url"):
                    continue
                clean_sources.append({
                    "url": src["url"].strip(),
                    "title": src.get("title", "").strip() or "Source",
                    "date": src.get("date", entry.get("date", "2024-01-01")),
                    "type": src.get("type", "news") if src.get("type") in VALID_SOURCE_TYPES else "news"
                })
            if not clean_sources:
                continue

            # Assign ID
            entry["id"] = self._next_incident_num()

            clean = {
                "id": entry["id"],
                "title": entry["title"].strip(),
                "date": entry.get("date", "2024-01-01"),
                "description": entry.get("description", "").strip(),
                "severity": entry["severity"],
                "providerIds": entry["providerIds"],
                "modelIds": entry["modelIds"],
                "techniqueIds": entry["techniqueIds"],
                "riskAreaIds": entry["riskAreaIds"],
                "sources": clean_sources,
                "status": "confirmed"
            }

            new_entries.append(clean)
            for src in clean_sources:
                self.existing_incident_urls.add(src["url"])
            self.existing_incident_titles.append(clean["title"].lower().strip())

        return new_entries

    def run(self, providers=None, collection_type="both", write=False):
        """Run expansion across providers."""
        target_providers = providers or list(self.provider_ids)
        do_commentary = collection_type in ("both", "commentary")
        do_incidents = collection_type in ("both", "incidents")

        total = len(target_providers)
        all_new_commentary = []
        all_new_incidents = []

        for i, pid in enumerate(target_providers, 1):
            name = self.provider_names.get(pid, pid)
            print(f"\n[{i}/{total}] {name}")

            if do_commentary:
                print(f"  Searching commentary...")
                try:
                    entries = self.expand_commentary(pid)
                    all_new_commentary.extend(entries)
                    print(f"  Found {len(entries)} new commentary entries")
                    for e in entries:
                        print(f"    + {e['title'][:70]}")
                except Exception as e:
                    print(f"  Error in commentary: {e}")

                time.sleep(1)

            if do_incidents:
                print(f"  Searching incidents...")
                try:
                    entries = self.expand_incidents(pid)
                    all_new_incidents.extend(entries)
                    print(f"  Found {len(entries)} new incident entries")
                    for e in entries:
                        print(f"    + {e['title'][:70]}")
                except Exception as e:
                    print(f"  Error in incidents: {e}")

                time.sleep(1)

        # Summary
        print(f"\n{'=' * 60}")
        print(f"SUMMARY")
        print(f"{'=' * 60}")
        print(f"New commentary entries: {len(all_new_commentary)}")
        print(f"New incident entries:   {len(all_new_incidents)}")
        print(f"Commentary skipped (duplicate): {self.stats['commentary_skipped']}")
        print(f"Incidents skipped (duplicate):  {self.stats['incidents_skipped']}")

        if not write:
            print(f"\n[DRY RUN — default] Would write {len(all_new_commentary)} commentary + "
                  f"{len(all_new_incidents)} incidents. Re-run with --write to persist after review.")
            if all_new_commentary:
                print(f"\nNew commentary entries:")
                print(json.dumps(all_new_commentary, indent=2, ensure_ascii=False))
            if all_new_incidents:
                print(f"\nNew incident entries:")
                print(json.dumps(all_new_incidents, indent=2, ensure_ascii=False))
            return

        # Write results
        if all_new_commentary:
            self.commentary.extend(all_new_commentary)
            COMMENTARY_PATH.write_text(
                json.dumps(self.commentary, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8"
            )
            print(f"\nWrote {len(self.commentary)} total entries to {COMMENTARY_PATH}")

        if all_new_incidents:
            self.incidents.extend(all_new_incidents)
            INCIDENTS_PATH.write_text(
                json.dumps(self.incidents, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8"
            )
            print(f"Wrote {len(self.incidents)} total entries to {INCIDENTS_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Expand commentary & incidents via web search")
    parser.add_argument("--provider", type=str, help="Target a single provider ID")
    parser.add_argument("--type", type=str, default="both",
                        choices=["both", "commentary", "incidents"],
                        help="Collection type to expand (default: both)")
    parser.add_argument("--write", action="store_true",
                        help="Persist results to data files. Default is a safe dry run "
                             "(print only) — review the LLM-sourced output before writing (REFACTOR §5.6).")
    parser.add_argument("--model", type=str, default="sonnet",
                        choices=list(MODEL_MAP.keys()),
                        help="Model to use (default: sonnet)")
    args = parser.parse_args()

    expander = CollectionExpander(model=args.model)

    providers = None
    if args.provider:
        if args.provider not in expander.provider_ids:
            print(f"Error: Unknown provider '{args.provider}'")
            print(f"Valid providers: {', '.join(sorted(expander.provider_ids))}")
            sys.exit(1)
        providers = [args.provider]

    expander.run(providers=providers, collection_type=args.type, write=args.write)


if __name__ == "__main__":
    main()
