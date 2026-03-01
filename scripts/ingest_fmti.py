#!/usr/bin/env python3
"""Ingest Stanford Foundation Model Transparency Index (FMTI) data.

Downloads the Dec 2025 FMTI scores and indicators from GitHub,
maps indicators to our technique IDs where possible, and writes
supplementary evidence entries to evidence.json.

Source: https://github.com/stanford-crfm/fmti
License: CC-BY
"""

import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
THIRD_PARTY_DIR = DATA_DIR / "third_party" / "fmti"
EVIDENCE_FILE = DATA_DIR / "evidence.json"

SCORES_URL = "https://raw.githubusercontent.com/stanford-crfm/fmti/main/Dec2025/Dec2025_scores.csv"
INDICATORS_URL = "https://raw.githubusercontent.com/stanford-crfm/fmti/main/Dec2025/Dec2025_indicators.csv"

# Map FMTI company column names → our provider IDs
COMPANY_TO_PROVIDER = {
    "Amazon": "amazon",
    "Anthropic": "anthropic",
    "Google": "google",
    "Meta": "meta",
    "Mistral": "mistral",
    "OpenAI": "openai",
}

# Map FMTI indicator names → our technique IDs
# Only includes indicators where there's a meaningful correspondence.
# FMTI measures disclosure/transparency, not implementation — so these
# are supplementary evidence of engagement with the technique area.
# Exact indicator names from Dec2025_scores.csv → our technique IDs.
# FMTI measures disclosure/transparency, not implementation — so these
# are supplementary evidence of engagement with the technique area.
INDICATOR_TO_TECHNIQUE = {
    # Risks & evaluation
    "Risks taxonomy": "tech-safety-benchmarks",
    "Risks evaluation": "tech-safety-benchmarks",
    "Pre-deployment risk evaluation": "tech-safety-benchmarks",
    "External risk evaluation": "tech-community-evaluation",
    "Capabilities evaluation": None,  # about capabilities, not safety
    # Model mitigations
    "Mitigations taxonomy": None,  # too generic
    "Mitigations taxonomy mapped to risk taxonomy": None,
    "Mitigations efficacy": None,
    "Model theft prevention measures": "tech-model-weight-security",
    # Release & governance
    "Release stages": "tech-responsible-release",
    "Risk thresholds": "tech-responsible-release",
    "Terms of use": "tech-configurable-policies",
    "Government commitments": "tech-voluntary-commitments",
    "Whistleblower protection": "tech-whistleblower-protections",
    "Oversight mechanism": "tech-safety-advisory",
    # Downstream safety
    "AI bug bounty": "tech-red-teaming",
    "Safe harbor": "tech-red-teaming",
    "Security incident reporting protocol": "tech-incident-reporting",
    "Misuse incident reporting protocol": "tech-incident-reporting",
    "Post-deployment coordination with government": "tech-regulatory-compliance",
    "Detection of machine-generated content": "tech-watermarking",
    "Internal product and service mitigations": "tech-output-filtering-systems",
    "External developer mitigations": "tech-enterprise-integration",
    "Enterprise mitigations": "tech-enterprise-integration",
    "Feedback mechanisms": "tech-stakeholder-engagement",
    "Documentation for responsible use": "tech-access-control-documentation",
    "Responsible disclosure policy": "tech-incident-reporting",
    # Model behavior
    "Permitted, restricted, and prohibited model behaviors": "tech-output-filtering-systems",
    "System prompt": "tech-system-prompts",
    # Usage policies
    "Permitted, restricted, and prohibited uses": "tech-configurable-policies",
    "AUP enforcement process": "tech-configurable-policies",
    "Regional policy variations": "tech-data-sovereignty",
    "Data retention and deletion policy": "tech-data-retention-policies",
}


def download_csv(url):
    """Download a CSV file and return parsed rows."""
    print(f"  Downloading {url.split('/')[-1]}...")
    req = Request(url, headers={"User-Agent": "LLM-Safety-Mechanisms/1.0"})
    with urlopen(req) as resp:
        text = resp.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def main():
    print("=== FMTI Ingestion ===\n")

    # Ensure output directory
    THIRD_PARTY_DIR.mkdir(parents=True, exist_ok=True)

    # Download data
    scores_rows = download_csv(SCORES_URL)
    indicators_rows = download_csv(INDICATORS_URL)

    # Save raw CSVs locally
    for name, rows in [("scores", scores_rows), ("indicators", indicators_rows)]:
        if not rows:
            print(f"  WARNING: No data in {name}")
            continue
        outpath = THIRD_PARTY_DIR / f"Dec2025_{name}.csv"
        with open(outpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Saved {outpath.name} ({len(rows)} rows)")

    # Identify company columns in scores
    if not scores_rows:
        print("ERROR: No scores data downloaded")
        sys.exit(1)

    all_columns = list(scores_rows[0].keys())
    indicator_col = all_columns[0]  # First column is the indicator name
    company_cols = [c for c in all_columns[1:] if c.strip()]
    print(f"\n  Companies in FMTI: {', '.join(company_cols)}")
    print(f"  Mapped to our providers: {', '.join(COMPANY_TO_PROVIDER.keys())}")

    # Build technique evidence from scores
    technique_hits = {}  # (provider_id, technique_id) → indicator names
    unmapped_indicators = set()
    mapped_indicators = set()

    for row in scores_rows:
        indicator_name = row[indicator_col].strip()
        technique_id = INDICATOR_TO_TECHNIQUE.get(indicator_name)

        if technique_id is None and indicator_name in INDICATOR_TO_TECHNIQUE:
            continue  # Explicitly mapped to None (too generic)
        if technique_id is None:
            unmapped_indicators.add(indicator_name)
            continue

        mapped_indicators.add(indicator_name)

        for company, provider_id in COMPANY_TO_PROVIDER.items():
            score = row.get(company, "").strip()
            if score == "1":
                key = (provider_id, technique_id)
                if key not in technique_hits:
                    technique_hits[key] = []
                technique_hits[key].append(indicator_name)

    print(f"\n  Mapped indicators: {len(mapped_indicators)}")
    print(f"  Unmapped indicators: {len(unmapped_indicators)}")
    print(f"  Technique-provider pairs found: {len(technique_hits)}")

    # Group by provider for summary
    by_provider = {}
    for (pid, tid), indicators in technique_hits.items():
        if pid not in by_provider:
            by_provider[pid] = []
        by_provider[pid].append((tid, indicators))

    print("\n  Per-provider technique signals:")
    for pid in sorted(by_provider):
        techs = by_provider[pid]
        print(f"    {pid}: {len(techs)} techniques")

    # Load existing evidence
    with open(EVIDENCE_FILE, "r", encoding="utf-8") as f:
        evidence_data = json.load(f)

    sources = evidence_data.get("sources", [])
    existing_ids = {s["id"] for s in sources}

    # Check if FMTI source already exists
    fmti_source_id = "fmti-dec-2025"
    if fmti_source_id in existing_ids:
        print(f"\n  Source '{fmti_source_id}' already exists in evidence.json, updating...")
        sources = [s for s in sources if s["id"] != fmti_source_id]

    # Build technique detections grouped by provider
    fmti_detections = {}
    for (pid, tid), indicators in sorted(technique_hits.items()):
        if pid not in fmti_detections:
            fmti_detections[pid] = []
        fmti_detections[pid].append({
            "techniqueId": tid,
            "indicators": indicators,
        })

    # Create one evidence source entry per provider
    new_sources = []
    for provider_id, detections in sorted(fmti_detections.items()):
        source_id = f"fmti-dec-2025-{provider_id}"
        technique_ids = [d["techniqueId"] for d in detections]

        # Remove existing entry if updating
        sources = [s for s in sources if s["id"] != source_id]

        entry = {
            "id": source_id,
            "title": f"FMTI Dec 2025 — {provider_id.capitalize()}",
            "provider": provider_id,
            "url": "https://crfm.stanford.edu/fmti/",
            "type": "Third-party Assessment",
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "origin": "third-party",
            "evidenceQuality": "secondary",
            "content_metadata": {
                "document_purpose": "transparency_assessment",
                "signal_strength": "medium",
                "temporal_focus": "implemented",
                "scope": "provider",
                "technical_depth": "low",
                "primary_topics": ["transparency", "governance"],
                "excluded_topics": [],
                "confidence_weight": 0.6,
                "language": "en",
                "notes": (
                    "Stanford Foundation Model Transparency Index (Dec 2025). "
                    "Binary transparency scores — indicates disclosure, not necessarily implementation depth. "
                    f"Mapped {len(detections)} indicators to techniques."
                ),
                "no_safety_content": False,
            },
            "fmti_techniques": technique_ids,
        }
        new_sources.append(entry)

    sources.extend(new_sources)
    evidence_data["sources"] = sources

    with open(EVIDENCE_FILE, "w", encoding="utf-8") as f:
        json.dump(evidence_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\n  Added {len(new_sources)} FMTI source entries to evidence.json")

    # Write metadata
    meta = {
        "source": "Stanford Foundation Model Transparency Index (FMTI)",
        "source_url": "https://crfm.stanford.edu/fmti/",
        "github_url": "https://github.com/stanford-crfm/fmti",
        "license": "CC-BY",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "edition": "December 2025",
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "total_companies": len(company_cols),
        "mapped_companies": len(COMPANY_TO_PROVIDER),
        "total_indicators": len(scores_rows),
        "mapped_indicators": len(mapped_indicators),
        "technique_provider_pairs": len(technique_hits),
        "indicator_mapping": {k: v for k, v in INDICATOR_TO_TECHNIQUE.items() if v is not None},
    }
    meta_path = THIRD_PARTY_DIR / "fmti_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"  Wrote metadata to {meta_path.name}")
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
