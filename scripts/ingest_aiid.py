"""
Ingest incidents from the AI Incident Database (AIID) into incidents.json.

Data source: https://incidentdatabase.ai/research/snapshots/
License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)

This script:
1. Downloads the latest AIID snapshot (or uses a local copy)
2. Parses incidents.csv, reports.csv, and classifications_CSETv1.csv
3. Maps AIID fields to our incidents.json schema
4. Writes the result to data/incidents.json

Usage:
    python scripts/ingest_aiid.py                     # Use local snapshot
    python scripts/ingest_aiid.py --download           # Download latest from AIID
    python scripts/ingest_aiid.py --check              # Check if a newer snapshot exists
"""

import argparse
import csv
import json
import logging
import os
import re
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Canonical technique-id resolution. The keyword table below may carry legacy
# technique ids; routing matches through taxonomy_aliases (the single source of
# truth for renames/merges) keeps regenerated incidents on the current taxonomy
# so a re-ingest can't reintroduce dangling references after a rename.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxonomy_aliases import canonical_techniques

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("AIID-Ingest")

# ── Paths ──

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
AIID_DIR = DATA_DIR / "third_party" / "aiid"
INCIDENTS_PATH = DATA_DIR / "incidents.json"
PROVIDERS_PATH = DATA_DIR / "providers.json"
RISK_AREAS_PATH = DATA_DIR / "risk_areas.json"
AIID_META_PATH = AIID_DIR / "aiid_meta.json"

# AIID snapshots page and download pattern
AIID_SNAPSHOTS_URL = "https://incidentdatabase.ai/research/snapshots/"
AIID_DOWNLOAD_BASE = "https://incidentdatabase.ai/research/snapshots/"

# Max reports (sources) to include per incident
MAX_SOURCES_PER_INCIDENT = 3
TECHNIQUES_PATH = DATA_DIR / "techniques.json"

# ── Provider entity mapping ──
# Maps AIID entity names (lowercase) to our provider IDs
ENTITY_TO_PROVIDER = {
    "openai": "openai",
    "chatgpt": "openai",
    "dall-e": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "google-deepmind": "google",
    "deepmind": "google",
    "youtube": "google",
    "meta": "meta",
    "facebook": "meta",
    "instagram": "meta",
    "amazon": "amazon",
    "amazon-web-services": "amazon",
    "aws": "amazon",
    "microsoft": "microsoft",
    "nvidia": "nvidia",
    "xai": "xai",
    "x": "xai",
    "twitter": "xai",
    "alibaba": "alibaba",
    "tencent": "tencent",
    "deepseek": "deepseek",
    "cohere": "cohere",
    "mistral": "mistral",
    "tii": "tii",
}

# ── CSETv1 harm → risk area mapping ──
# Maps CSETv1 classification signals to our risk_areas.json IDs

CSET_HARM_TO_RISK = {
    # Tangible Harm field values
    "tangible_harm": {
        "tangible harm definitively occurred": ["harmful_content"],
        "imminent risk of tangible harm (near miss) did occur": ["harmful_content"],
    },
    # Special interest fields (boolean yes/no/maybe)
    "special_interest": {
        "Rights Violation": "bias_and_fairness",
        "Protected Characteristic": "bias_and_fairness",
        "Detrimental Content": "harmful_content",
        "Involving Minor": "harmful_content",
        "Impact on Critical Services": "security_and_misuse",
    },
}

# ── Severity mapping from CSETv1 ──
CSET_SEVERITY_MAP = {
    "tangible harm definitively occurred": "high",
    "imminent risk of tangible harm (near miss) did occur": "high",
    "non-imminent risk of tangible harm (an issue) occurred": "medium",
    "no tangible harm, near-miss, or issue": "low",
}


# ── LLM/GenAI classification keywords ──
# Incidents matching any of these in title+description are tagged isLLMRelated=true
LLM_KEYWORDS = [
    # Model types
    "llm", "large language model", "language model", "foundation model",
    "frontier model", "generative ai", "gen ai", "genai",
    # Products and models
    "chatgpt", "gpt-3", "gpt-4", "gpt-5", "dall-e", "dalle", "sora",
    "gemini", "bard", "palm", "lamda",
    "claude", "copilot", "bing chat", "sydney",
    "grok", "llama", "mistral", "mixtral", "command r",
    "stable diffusion", "midjourney", "flux",
    "whisper", "codex",
    # Categories
    "chatbot", "chat bot", "ai chatbot", "ai assistant", "virtual assistant",
    "text generation", "image generation", "video generation",
    "content generation", "code generation",
    "voice cloning", "speech synthesis", "text-to-speech", "text to speech",
    "deepfake", "deep fake", "ai-generated", "ai generated",
    "ai image", "ai video", "ai audio", "ai voice", "ai text",
    # Safety concepts
    "hallucination", "prompt injection", "jailbreak", "prompt attack",
    "ai alignment", "ai safety",
    # Companies (as indicators of LLM incidents when mentioned)
    "openai", "anthropic",
    # NLP
    "natural language processing", "nlp", "transformer model",
    "neural network text", "token generation",
]

# CSETv1 AI tools/tasks that indicate LLM/GenAI
CSET_LLM_INDICATORS = {
    "large language model", "large language models",
    "natural language processing", "Natural Language Processesing",
    "text generation", "chat bot", "chatbot",
    "human language technology", "generative ai",
    "image generation", "content moderation",
}


def classify_llm_related(title, description, cset_row=None):
    """Determine if an incident relates to LLMs/GenAI."""
    text = (title + " " + description).lower()
    # Keyword match
    for kw in LLM_KEYWORDS:
        if kw in text:
            return True
    # CSETv1 AI task/tools match
    if cset_row:
        for field in ["AI Task", "AI tools and methods"]:
            val = (cset_row.get(field, "") or "").strip().lower()
            if val and any(ind.lower() in val for ind in CSET_LLM_INDICATORS):
                return True
    return False


def load_technique_keywords():
    """Load technique keywords from NLU profiles for incident mapping."""
    if not TECHNIQUES_PATH.exists():
        return {}
    techniques = load_json(TECHNIQUES_PATH)
    keyword_map = {}  # keyword -> (technique_id, risk_area_ids)
    for tech in techniques:
        tid = tech["id"]
        risk_areas = tech.get("riskAreaIds", [])
        nlu = tech.get("nlu_profile", {})
        anchors = nlu.get("semantic_anchors", [])
        # Use only distinctive anchors (skip very generic ones)
        for anchor in anchors:
            anchor_lower = anchor.lower()
            # Skip anchors that are too short or generic
            if len(anchor_lower) < 4 or anchor_lower in (
                "ai", "model", "data", "test", "safe", "bias",
                "risk", "harm", "fair", "train", "audit",
            ):
                continue
            if tid not in keyword_map:
                keyword_map[tid] = {
                    "risk_areas": risk_areas,
                    "anchors": [],
                }
            keyword_map[tid]["anchors"].append(anchor_lower)
    return keyword_map


# Incident-specific keyword → technique mapping
# These map incident description patterns to technique failures
INCIDENT_TECHNIQUE_KEYWORDS = {
    "tech-prompt-injection-defense": [
        "prompt injection", "prompt attack", "jailbreak",
        "system prompt", "prompt leak", "prompt extraction",
    ],
    "tech-refusal-training": [
        "refused to", "failed to refuse", "bypass safety",
        "safety bypass", "circumvent", "override safety",
    ],
    "tech-output-filtering-systems": [
        "harmful output", "toxic output", "inappropriate content",
        "offensive content", "generated harmful", "produced harmful",
    ],
    "tech-pii-detection": [
        "personal data", "pii", "personal information",
        "data leak", "privacy breach", "data exposure",
        "leaked personal", "exposed personal",
    ],
    "tech-data-retention-policies": [
        "data breach", "data leak", "unauthorized access to data",
        "data exposure", "data collection",
    ],
    "tech-bias-mitigation": [
        "bias", "discriminat", "racial", "gender bias",
        "unfair", "stereotyp", "prejudic",
    ],
    "tech-watermarking": [
        "deepfake", "deep fake", "synthetic media",
        "ai-generated image", "ai generated image",
        "ai-generated video", "ai generated video",
        "fake image", "fake video", "manipulated image",
    ],
    "tech-hallucination-grounding": [
        "hallucination", "fabricat", "made up",
        "false information", "inaccurate information",
        "invented", "confabul",
    ],
    "tech-copyright-ip-violation": [
        "copyright", "intellectual property", "ip violation",
        "copyrighted", "plagiari", "reproduction of",
    ],
    "tech-regulatory-compliance": [
        "gdpr", "regulation", "compliance", "banned",
        "fined", "penalty", "enforcement", "legal action",
    ],
    "tech-observability-monitoring": [
        "outage", "malfunction", "system failure",
        "unintended behavior", "unexpected behavior",
        "monitoring failure",
    ],
    "tech-age-verification": [
        "children", "minors", "underage", "child safety",
        "kids", "young users",
    ],
}


def map_techniques_from_text(title, description):
    """Map incident text to likely failed techniques and risk areas."""
    text = (title + " " + description).lower()
    matched_techniques = set()
    matched_risks = set()

    for tech_id, keywords in INCIDENT_TECHNIQUE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matched_techniques.add(tech_id)
                break

    # Derive additional risk areas from matched techniques
    # (load technique risk areas if available)
    # Canonicalize so legacy ids in the keyword table can't produce dangling refs.
    return sorted(canonical_techniques(matched_techniques)), sorted(matched_risks)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote {path}")


def find_latest_snapshot_dir():
    """Find the most recent extracted snapshot directory."""
    if not AIID_DIR.exists():
        return None

    # Look for backup-* directories
    dirs = sorted(
        [d for d in AIID_DIR.iterdir() if d.is_dir() and d.name.startswith("backup-")],
        key=lambda d: d.name,
        reverse=True,
    )
    if not dirs:
        return None

    snapshot_dir = dirs[0] / "mongodump_full_snapshot"
    if snapshot_dir.exists():
        return snapshot_dir

    return None


def find_latest_archive():
    """Find the most recent .tar.bz2 archive."""
    if not AIID_DIR.exists():
        return None

    archives = sorted(
        [f for f in AIID_DIR.iterdir() if f.name.endswith(".tar.bz2")],
        key=lambda f: f.name,
        reverse=True,
    )
    return archives[0] if archives else None


def extract_snapshot_version(snapshot_dir):
    """Extract the version date from the snapshot directory name."""
    # e.g. backup-20260223102103 → 2026-02-23
    match = re.search(r"backup-(\d{4})(\d{2})(\d{2})", str(snapshot_dir))
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return "unknown"


def download_latest_snapshot():
    """Download the latest AIID snapshot archive."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("requests and beautifulsoup4 required for download. pip install requests beautifulsoup4")
        sys.exit(1)

    logger.info(f"Fetching snapshot list from {AIID_SNAPSHOTS_URL}")
    resp = requests.get(AIID_SNAPSHOTS_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find all .tar.bz2 links
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".tar.bz2"):
            links.append(href)

    if not links:
        logger.error("No .tar.bz2 download links found on snapshots page")
        sys.exit(1)

    # Sort and pick latest
    links.sort(reverse=True)
    download_url = links[0]
    if not download_url.startswith("http"):
        download_url = AIID_DOWNLOAD_BASE.rstrip("/") + "/" + download_url.lstrip("/")

    filename = download_url.split("/")[-1]
    archive_path = AIID_DIR / filename

    # Check if already downloaded
    if archive_path.exists():
        logger.info(f"Archive already exists: {archive_path}")
        return archive_path

    AIID_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {download_url} ...")
    resp = requests.get(download_url, stream=True, timeout=300)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(archive_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded * 100 // total
                print(f"\r  {pct}% ({downloaded // (1024*1024)} MB)", end="", flush=True)
    print()
    logger.info(f"Downloaded to {archive_path}")
    return archive_path


def extract_archive(archive_path):
    """Extract a .tar.bz2 archive."""
    extract_dir = archive_path.parent / archive_path.name.replace(".tar.bz2", "")
    if extract_dir.exists():
        logger.info(f"Already extracted: {extract_dir}")
        return extract_dir / "mongodump_full_snapshot"

    logger.info(f"Extracting {archive_path} ...")
    with tarfile.open(archive_path, "r:bz2") as tar:
        tar.extractall(path=extract_dir)
    logger.info(f"Extracted to {extract_dir}")
    return extract_dir / "mongodump_full_snapshot"


def parse_json_array(raw):
    """Parse a JSON array string from CSV, handling edge cases."""
    if not raw or raw.strip() in ("", "[]"):
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try cleaning up common issues
        cleaned = raw.strip().strip("[]")
        if not cleaned:
            return []
        return [s.strip().strip('"').strip("'") for s in cleaned.split(",")]


def load_incidents_csv(snapshot_dir):
    """Load and parse incidents.csv."""
    path = snapshot_dir / "incidents.csv"
    incidents = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            incidents.append({
                "incident_id": int(row["incident_id"]),
                "date": row.get("date", ""),
                "title": row.get("title", ""),
                "description": row.get("description", ""),
                "deployers": parse_json_array(row.get("Alleged deployer of AI system", "[]")),
                "developers": parse_json_array(row.get("Alleged developer of AI system", "[]")),
                "harmed_parties": parse_json_array(row.get("Alleged harmed or nearly harmed parties", "[]")),
                "report_ids": parse_json_array(row.get("reports", "[]")),
            })
    logger.info(f"Loaded {len(incidents)} incidents from CSV")
    return incidents


def load_reports_csv(snapshot_dir):
    """Load reports.csv into a lookup by report_number."""
    path = snapshot_dir / "reports.csv"
    reports = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            report_num = row.get("report_number", "")
            if report_num:
                reports[int(report_num)] = {
                    "url": row.get("url", ""),
                    "title": row.get("title", ""),
                    "date_published": row.get("date_published", ""),
                    "source_domain": row.get("source_domain", ""),
                }
    logger.info(f"Loaded {len(reports)} reports from CSV")
    return reports


def load_duplicates_csv(snapshot_dir):
    """Load duplicates.csv to filter out duplicate incidents."""
    path = snapshot_dir / "duplicates.csv"
    duplicates = set()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dup_id = row.get("duplicate_incident_number", "")
                if dup_id:
                    duplicates.add(int(dup_id))
    logger.info(f"Loaded {len(duplicates)} duplicate incident IDs to exclude")
    return duplicates


def load_csetv1_classifications(snapshot_dir):
    """Load CSETv1 classifications keyed by incident_id."""
    path = snapshot_dir / "classifications_CSETv1.csv"
    classifications = {}
    if not path.exists():
        logger.warning("classifications_CSETv1.csv not found, skipping enrichment")
        return classifications

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inc_id_str = row.get("Incident Number") or row.get("Incident ID", "")
            if not inc_id_str:
                continue
            try:
                inc_id = int(inc_id_str)
            except ValueError:
                continue
            classifications[inc_id] = row
    logger.info(f"Loaded {len(classifications)} CSETv1 classifications")
    return classifications


def map_entities_to_providers(entities, provider_ids):
    """Map AIID entity names to our provider IDs."""
    matched = set()
    for entity in entities:
        entity_lower = entity.lower().strip()
        provider_id = ENTITY_TO_PROVIDER.get(entity_lower)
        if provider_id and provider_id in provider_ids:
            matched.add(provider_id)
    return sorted(matched)


def derive_severity(cset_row):
    """Derive severity from CSETv1 Tangible Harm field."""
    if not cset_row:
        return "medium"
    tangible = cset_row.get("Tangible Harm", "").strip().lower()
    for key, severity in CSET_SEVERITY_MAP.items():
        if tangible == key.lower():
            return severity
    return "medium"


def derive_risk_areas(cset_row):
    """Derive risk area IDs from CSETv1 classification fields."""
    if not cset_row:
        return []

    risk_areas = set()

    # Map tangible harm
    tangible = cset_row.get("Tangible Harm", "").strip().lower()
    for key, areas in CSET_HARM_TO_RISK["tangible_harm"].items():
        if tangible == key.lower():
            risk_areas.update(areas)

    # Map special interest fields
    for field, risk_id in CSET_HARM_TO_RISK["special_interest"].items():
        val = cset_row.get(field, "").strip().lower()
        if val == "yes":
            risk_areas.add(risk_id)

    return sorted(risk_areas)


def get_sources_for_incident(report_ids, reports_lookup):
    """Get source URLs from reports for an incident."""
    sources = []
    for rid in report_ids:
        rid_int = int(rid) if not isinstance(rid, int) else rid
        report = reports_lookup.get(rid_int)
        if report and report["url"]:
            sources.append({
                "url": report["url"],
                "title": report["title"] or report["source_domain"] or "",
                "date": report["date_published"] or "",
                "type": "news",
            })
        if len(sources) >= MAX_SOURCES_PER_INCIDENT:
            break
    return sources


def transform_incidents(aiid_incidents, reports_lookup, duplicates, cset_classifications, provider_ids, techniques):
    """Transform AIID incidents into our schema."""
    results = []
    tech_risk_map = {t["id"]: t.get("riskAreaIds", []) for t in techniques}

    for inc in aiid_incidents:
        inc_id = inc["incident_id"]

        # Skip duplicates
        if inc_id in duplicates:
            continue

        # Map developers/deployers to our providers
        all_entities = inc["developers"] + inc["deployers"]
        provider_matches = map_entities_to_providers(all_entities, provider_ids)

        # Derive severity and risk areas from CSETv1 if available
        cset_row = cset_classifications.get(inc_id)
        severity = derive_severity(cset_row)
        risk_areas = set(derive_risk_areas(cset_row))

        # Classify as LLM-related
        is_llm = classify_llm_related(inc["title"], inc["description"], cset_row)

        # Map techniques from incident text
        technique_ids, _ = map_techniques_from_text(inc["title"], inc["description"])

        # Enrich risk areas from matched techniques
        for tid in technique_ids:
            for rid in tech_risk_map.get(tid, []):
                risk_areas.add(rid)

        # Get source URLs from reports
        sources = get_sources_for_incident(inc["report_ids"], reports_lookup)

        # Build the incident record
        record = {
            "id": f"aiid-{inc_id}",
            "aiidIncidentId": inc_id,
            "title": inc["title"],
            "date": inc["date"] or "",
            "description": inc["description"] or "",
            "severity": severity,
            "providerIds": provider_matches,
            "modelIds": [],
            "techniqueIds": technique_ids,
            "riskAreaIds": sorted(risk_areas),
            "sources": sources,
            "status": "confirmed",
            "aiidUrl": f"https://incidentdatabase.ai/cite/{inc_id}",
            "isLLMRelated": is_llm,
        }

        results.append(record)

    # Sort by date descending
    results.sort(key=lambda r: r["date"] or "0000-00-00", reverse=True)
    logger.info(f"Transformed {len(results)} incidents (excluded {len(duplicates)} duplicates)")

    # Stats
    with_providers = sum(1 for r in results if r["providerIds"])
    with_severity = sum(1 for r in results if r["severity"] != "medium")
    with_risk = sum(1 for r in results if r["riskAreaIds"])
    with_techniques = sum(1 for r in results if r["techniqueIds"])
    llm_related = sum(1 for r in results if r["isLLMRelated"])
    logger.info(f"  Matched to our providers: {with_providers}")
    logger.info(f"  With CSETv1 severity: {with_severity}")
    logger.info(f"  With risk areas: {with_risk}")
    logger.info(f"  With technique mappings: {with_techniques}")
    logger.info(f"  LLM/GenAI related: {llm_related}")

    return results


def check_for_updates():
    """Check if a newer AIID snapshot is available."""
    meta = {}
    if AIID_META_PATH.exists():
        meta = load_json(AIID_META_PATH)

    current_version = meta.get("snapshot_version", "none")
    current_archive = meta.get("archive_filename", "none")

    local_archive = find_latest_archive()
    if local_archive:
        local_version = extract_snapshot_version(local_archive)
    else:
        local_version = "none"

    logger.info(f"Current ingested version: {current_version}")
    logger.info(f"Latest local archive:     {local_version}")

    if current_version == local_version and current_version != "none":
        logger.info("Already up to date with local archive.")
        return False

    if local_version != "none" and local_version != current_version:
        logger.info(f"Newer local archive available: {local_version}")
        return True

    logger.info("No newer local archive found. Use --download to fetch latest from AIID.")
    return False


def main():
    parser = argparse.ArgumentParser(description="Ingest AIID incidents into incidents.json")
    parser.add_argument("--download", action="store_true", help="Download latest snapshot from AIID")
    parser.add_argument("--check", action="store_true", help="Check if a newer snapshot is available")
    args = parser.parse_args()

    # Check mode
    if args.check:
        check_for_updates()
        return

    # Download mode
    if args.download:
        archive = download_latest_snapshot()
        snapshot_dir = extract_archive(archive)
    else:
        snapshot_dir = find_latest_snapshot_dir()
        if not snapshot_dir:
            logger.error(f"No extracted snapshot found in {AIID_DIR}")
            logger.error("Run with --download to fetch latest, or extract an archive manually")
            sys.exit(1)

    logger.info(f"Using snapshot: {snapshot_dir}")
    version = extract_snapshot_version(snapshot_dir)
    logger.info(f"Snapshot version: {version}")

    # Load our provider IDs and techniques
    providers = load_json(PROVIDERS_PATH)
    provider_ids = {p["id"] for p in providers}
    techniques = load_json(TECHNIQUES_PATH) if TECHNIQUES_PATH.exists() else []

    # Load AIID data
    aiid_incidents = load_incidents_csv(snapshot_dir)
    reports_lookup = load_reports_csv(snapshot_dir)
    duplicates = load_duplicates_csv(snapshot_dir)
    cset_classifications = load_csetv1_classifications(snapshot_dir)

    # Transform
    incidents = transform_incidents(
        aiid_incidents, reports_lookup, duplicates,
        cset_classifications, provider_ids, techniques
    )

    # Save
    save_json(INCIDENTS_PATH, incidents)

    # Save metadata
    llm_count = sum(1 for i in incidents if i.get("isLLMRelated"))
    tech_count = sum(1 for i in incidents if i.get("techniqueIds"))
    meta = {
        "source": "AI Incident Database (AIID)",
        "source_url": "https://incidentdatabase.ai/",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "snapshot_version": version,
        "archive_filename": find_latest_archive().name if find_latest_archive() else "",
        "ingested_at": datetime.now().isoformat(),
        "total_incidents": len(incidents),
        "llm_related_incidents": llm_count,
        "incidents_with_known_providers": sum(1 for i in incidents if i["providerIds"]),
        "incidents_with_technique_mappings": tech_count,
        "incidents_with_cset_classification": sum(1 for i in incidents if i["riskAreaIds"]),
    }
    save_json(AIID_META_PATH, meta)

    # Summary
    print(f"\n{'='*60}")
    print(f"AIID Ingestion Complete")
    print(f"{'='*60}")
    print(f"  Snapshot version:           {version}")
    print(f"  Total incidents:            {len(incidents)}")
    print(f"  LLM/GenAI related:          {llm_count}")
    print(f"  Matched to our providers:   {meta['incidents_with_known_providers']}")
    print(f"  With technique mappings:    {tech_count}")
    print(f"  With CSET classification:   {meta['incidents_with_cset_classification']}")
    print(f"  Output:                     {INCIDENTS_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
