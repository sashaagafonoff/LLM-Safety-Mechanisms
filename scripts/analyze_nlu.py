"""
NLU-Based Technique Extraction (RAG Retrieval + Verification Stage)

Implements the Retrieval-Augmented Generation pattern for safety technique
detection using a two-stage neural pipeline:

  Stage 1 — RETRIEVAL: A bi-encoder (bge-large-en-v1.5) embeds document
            chunks and technique descriptions into the same vector space.
            Cosine similarity retrieves candidate chunks above RETRIEVAL_THRESHOLD.

  Stage 2 — VERIFICATION: A cross-encoder (nli-deberta-v3-large) scores
            each (chunk, entailment_hypothesis) pair. Only pairs exceeding
            VERIFICATION_THRESHOLD are accepted as detections.

This pipeline forms the 'R' (retrieval) layer of the project's RAG
architecture. Its output feeds into the LLM extraction pipeline
(llm_assisted_extraction.py) as context for Claude's augmented generation.

See also: run_extraction_pipeline.py for the full orchestrated pipeline.
"""

import json
import glob
import os
import logging
import re
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from robust_tokenizer import create_chunks_from_text
from nli_utils import resolve_entailment_index
from taxonomy_maps import CATEGORY_TO_TOPIC

# --- CONFIGURATION ---
INPUT_DIR = Path("data/flat_text")
TECHNIQUES_PATH = Path("data/techniques.json")
CATEGORIES_PATH = Path("data/categories.json")
EVIDENCE_PATH = Path("data/evidence.json")
OUTPUT_FILE = Path("data/model_technique_map.json")

# STAGE 1: Retrieval Model
RETRIEVAL_MODEL_NAME = "BAAI/bge-large-en-v1.5"
RETRIEVAL_THRESHOLD = 0.40  # Raised from 0.35 to reduce FPs with bge-large

# STAGE 2: Verification Model
VERIFICATION_MODEL_NAME = "cross-encoder/nli-deberta-v3-large"
VERIFICATION_THRESHOLD = 0.85  # Raised from 0.65; large cross-encoder needs higher bar

# Reproducibility: pin model revisions to a HF commit SHA to freeze scores.
# None = latest (not reproducible). TODO: pin these (see docs/WORKPLAN.md B.0.4).
RETRIEVAL_MODEL_REVISION = None
VERIFICATION_MODEL_REVISION = None
RANDOM_SEED = 42

# Text Processing
WINDOW_SIZE = 3
STRIDE = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NLU_Analyzer")

def normalize_string(s: str) -> str:
    """Normalizes strings for matching (lowercase, alphanumeric only)."""
    if not s: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

def _set_determinism(seed: int = RANDOM_SEED) -> None:
    """Seed RNGs for reproducible scores (best-effort; deps may be absent)."""
    try:
        import random
        import numpy as np
        import torch
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception as e:  # pragma: no cover - depends on optional heavy deps
        logger.warning(f"Could not fully set determinism: {e}")

class NLUAnalyzer:
    def __init__(self):
        _set_determinism(RANDOM_SEED)

        logger.info("⏳ Loading Retrieval Model (Bi-Encoder)...")
        st_kwargs = {} if RETRIEVAL_MODEL_REVISION is None else {"revision": RETRIEVAL_MODEL_REVISION}
        self.retriever = SentenceTransformer(RETRIEVAL_MODEL_NAME, **st_kwargs)

        logger.info("⏳ Loading Verification Model (Cross-Encoder)...")
        ce_kwargs = {} if VERIFICATION_MODEL_REVISION is None else {"revision": VERIFICATION_MODEL_REVISION}
        self.verifier = CrossEncoder(VERIFICATION_MODEL_NAME, **ce_kwargs)

        # Resolve the entailment class index from the checkpoint config (REFACTOR §1.3);
        # do not hard-code index 1.
        cfg_labels = getattr(getattr(self.verifier, "model", None), "config", None)
        cfg_labels = getattr(cfg_labels, "id2label", None)
        self.entailment_idx = resolve_entailment_index(cfg_labels)
        if not cfg_labels:
            logger.warning("Could not read id2label from verifier; defaulting entailment index to %s",
                           self.entailment_idx)
        else:
            logger.info("Entailment class index resolved to %s (id2label=%s)",
                        self.entailment_idx, cfg_labels)

        self.categories = self._load_categories()
        self.technique_index = self._load_and_index_techniques()
        self.evidence_map = self._load_evidence_map()
        self.document_metadata = self._load_document_metadata()

    def _load_categories(self) -> Dict[str, Dict]:
        """Load categories for category-aware filtering."""
        with open(CATEGORIES_PATH, 'r', encoding='utf-8') as f:
            cats = json.load(f)
        logger.info(f"✓ Loaded {len(cats)} categories")
        return {cat['id']: cat for cat in cats}

    def _load_document_metadata(self) -> Dict[str, Dict]:
        """
        Load content_metadata from evidence.json for context-aware analysis.
        Maps document ID -> content_metadata dict.
        """
        metadata_map = {}
        if not EVIDENCE_PATH.exists():
            logger.warning(f"⚠️ Evidence file not found at {EVIDENCE_PATH}")
            return metadata_map

        with open(EVIDENCE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sources = data.get('sources', [])

        for source in sources:
            doc_id = source.get('id')
            if doc_id and 'content_metadata' in source:
                metadata_map[doc_id] = source['content_metadata']

        logger.info(f"✓ Loaded content_metadata for {len(metadata_map)} documents")
        return metadata_map

    def _load_evidence_map(self) -> Dict[str, str]:
        """
        Loads evidence.json and creates a lookup map.
        Maps normalized IDs/Titles -> Target Unique Key (URL or Title).
        """
        lookup = {}
        if not EVIDENCE_PATH.exists():
            logger.warning(f"⚠️ Evidence file not found at {EVIDENCE_PATH}. Linkage may fail.")
            return lookup

        with open(EVIDENCE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sources = data.get('sources', [])

        logger.info(f"📋 Indexing {len(sources)} evidence sources for linkage...")

        for source in sources:
            # Determine the stable Unique Key for the Output Map
            # Preference: URL > Title > ID
            unique_key = source.get('url')
            if not unique_key or unique_key == "<missing>":
                unique_key = source.get('title')

            # create lookup keys pointing to this unique_key

            # 1. Map normalized Source ID (PRIMARY - matches flat text filenames!)
            if source.get('id'):
                lookup[normalize_string(source['id'])] = unique_key

            # 2. Map normalized Title
            if source.get('title'):
                lookup[normalize_string(source['title'])] = unique_key

            # 3. Map normalized Model IDs
            for model in source.get('models', []):
                if model.get('modelId'):
                    lookup[normalize_string(model['modelId'])] = unique_key

        logger.info(f"✓ Created {len(lookup)} lookup entries")
        return lookup

    def _is_low_quality_match(self, text: str, technique_name: str) -> bool:
        """
        Heuristic filter to catch glossary definitions, future-work mentions,
        and discussion-only references. Returns True if the text should be discarded.
        """
        text_lower = text.lower()

        # 1. Glossary/Reference Section
        glossary_patterns = [
            "glossary", "definitions:", "bibliography:",
            "literature review:", "references:"
        ]
        if any(pattern in text_lower[:100] for pattern in glossary_patterns):
            return True

        # 2. Future Work — explicit future-tense phrases
        future_patterns = [
            "future work", "we plan to", "we intend to",
            "planned for", "will implement", "may implement",
            "could implement", "should implement",
            "exploring the use of"
        ]
        if any(pattern in text_lower for pattern in future_patterns):
            return True

        # 3. Comparative/Contrastive — only filter when no implementation context
        comparative_patterns = [
            "unlike", "compared to", "in contrast to",
            "as opposed to", "rather than", "instead of"
        ]
        implementation_keywords = [
            "we use", "we employ", "we implement", "we apply",
            "we deploy", "we utilize", "our system", "our model",
            "we train", "we trained", "incorporated", "deployed",
            "used in", "applied to", "implemented in",
            "the model uses", "the system uses", "is trained",
            "was trained", "is deployed", "was deployed",
            "we evaluate", "we assessed", "we tested",
            "achieves", "performs"
        ]
        has_implementation = any(keyword in text_lower for keyword in implementation_keywords)

        if any(pattern in text_lower for pattern in comparative_patterns) and not has_implementation:
            return True

        # 4. Discussion vs Implementation
        discussion_keywords = [
            "discussed in", "described in the literature",
            "mentioned in", "refers to", "defined as", "known as"
        ]
        has_discussion_only = any(keyword in text_lower for keyword in discussion_keywords)

        if has_discussion_only and not has_implementation:
            return True

        # 5. Access Control specific fix
        if technique_name == "Access Control Documentation":
            if any(w in text_lower for w in ["refus", "declin", "answer", "abstain"]):
                return True

        # 6. Proposed/Recommended (not implemented)
        if re.search(r'\b(proposed|recommended|suggested)\s+(by|in|approach)', text_lower):
            return True

        return False

    def _load_and_index_techniques(self) -> List[Dict]:
        with open(TECHNIQUES_PATH, 'r', encoding='utf-8') as f:
            techniques = json.load(f)

        index = []
        logger.info(f"Indexing {len(techniques)} techniques with category context...")

        for tech in techniques:
            profile = tech.get('nlu_profile', {})
            hypothesis = profile.get('entailment_hypothesis', f"The model uses {tech['name']}.")
            targets = [profile.get('primary_concept', tech['description'])]
            targets.extend(profile.get('semantic_anchors', []))

            embeddings = self.retriever.encode(targets, convert_to_tensor=True)

            # Get category info for metadata filtering
            category_id = tech.get('categoryId')
            category = self.categories.get(category_id, {})

            index.append({
                "id": tech['id'],
                "name": tech['name'],
                "category_id": category_id,
                "category_name": category.get('name', 'Unknown'),
                "hypothesis": hypothesis,
                "embeddings": embeddings,
                "targets": targets
            })

        return index

    def _chunk_text(self, text: str) -> List[str]:
        return create_chunks_from_text(
            text,
            window_size=WINDOW_SIZE,
            stride=STRIDE,
            min_sentence_length=20,
            min_chunk_length=20
        )

    def analyze_document(self, text: str, doc_id: str = "") -> List[Dict]:
        chunks = self._chunk_text(text)
        if not chunks:
            logger.debug(f"   No chunks generated for {doc_id}")
            return []

        # Load document metadata for category-aware filtering
        doc_metadata = self.document_metadata.get(doc_id, {})
        primary_topics = set(doc_metadata.get('primary_topics', []))
        excluded_topics = set(doc_metadata.get('excluded_topics', []))
        temporal_focus = doc_metadata.get('temporal_focus', 'unknown')
        signal_strength = doc_metadata.get('signal_strength', 'medium')
        technical_depth = doc_metadata.get('technical_depth', 'moderate')

        if doc_metadata:
            logger.debug(f"   Using metadata: signal={signal_strength}, depth={technical_depth}, focus={temporal_focus}")
            logger.debug(f"   Excluded topics: {excluded_topics if excluded_topics else 'none'}")

        logger.debug(f"   Generated {len(chunks)} chunks")
        chunk_embeddings = self.retriever.encode(chunks, convert_to_tensor=True)
        candidates = []
        metadata_filtered = 0

        # Category to topic mapping for metadata filtering (single source of truth:
        # taxonomy_maps.CATEGORY_TO_TOPIC — de-duplicated per REFACTOR §1.9).
        category_to_topic_map = CATEGORY_TO_TOPIC

        for tech in self.technique_index:
            # Category-aware filtering using document metadata
            if excluded_topics:
                tech_topic = category_to_topic_map.get(tech['category_id'])
                if tech_topic and tech_topic in excluded_topics:
                    metadata_filtered += 1
                    continue

            scores = util.cos_sim(tech['embeddings'], chunk_embeddings)
            max_scores_per_chunk, _ = scores.max(dim=0)
            passing_indices = (max_scores_per_chunk > RETRIEVAL_THRESHOLD).nonzero()

            for idx in passing_indices:
                idx = idx.item()
                candidates.append({
                    "chunk": chunks[idx],
                    "technique": tech,
                    "retrieval_score": max_scores_per_chunk[idx].item()
                })

        if metadata_filtered > 0:
            logger.debug(f"   Metadata filtering excluded {metadata_filtered} techniques")

        if not candidates:
            logger.debug(f"   No candidates passed retrieval threshold")
            return []

        logger.debug(f"   {len(candidates)} candidates passed Stage 1 (retrieval)")

        verified_matches = []
        pairs = [(c['chunk'], c['technique']['hypothesis']) for c in candidates]
        pred_scores = self.verifier.predict(pairs, apply_softmax=True)
        entailment_idx = self.entailment_idx

        filtered_count = 0
        for i, score_dist in enumerate(pred_scores):
            entailment_score = score_dist[entailment_idx]

            if entailment_score > VERIFICATION_THRESHOLD:
                cand = candidates[i]
                chunk_text = cand['chunk']
                tech_name = cand['technique']['name']

                # --- Quality Filter Check ---
                if self._is_low_quality_match(chunk_text, tech_name):
                    logger.debug(f"   -> Filtered: '{tech_name}' (Quality Filter)")
                    filtered_count += 1
                    continue
                # ---------------------------

                # Enhanced confidence scoring with multiple factors
                text_lower = chunk_text.lower()
                implementation_keywords = [
                    "we use", "we employ", "we implement", "we apply",
                    "we deploy", "we utilize", "our system", "our model",
                    "we train", "we trained", "incorporated", "deployed"
                ]
                has_strong_implementation = any(kw in text_lower for kw in implementation_keywords)

                # Multi-factor confidence scoring
                confidence_score = entailment_score

                # Factor 1: Implementation language
                if has_strong_implementation:
                    confidence_score += 0.05

                # Factor 2: Document signal strength
                if signal_strength == 'high':
                    confidence_score += 0.03
                elif signal_strength == 'low':
                    confidence_score -= 0.03

                # Factor 3: Technical depth
                if technical_depth == 'deep':
                    confidence_score += 0.02
                elif technical_depth == 'shallow':
                    confidence_score -= 0.02

                # Factor 4: Temporal focus (implemented > mixed > planned/research)
                if temporal_focus == 'implemented':
                    confidence_score += 0.02
                elif temporal_focus in ['planned', 'research']:
                    confidence_score -= 0.03

                # Map to confidence labels
                if confidence_score > 0.85:
                    confidence = "High"
                elif confidence_score > 0.70:
                    confidence = "Medium"
                else:
                    confidence = "Low"

                verified_matches.append({
                    "techniqueId": cand['technique']['id'],
                    "confidence": confidence,
                    "active": True,
                    "deleted_by": None,
                    "evidence": [{
                        "text": chunk_text,
                        "created_by": "nlu",
                        "active": True,
                        "deleted_by": None
                    }]
                })

        if filtered_count > 0:
            logger.debug(f"   Quality filter removed {filtered_count} candidates")
        logger.debug(f"   {len(verified_matches)} matches passed Stage 2 (verification)")

        return verified_matches

    def score_candidates(self, text: str, doc_id: str = "",
                         retrieval_floor: float = 0.30) -> List[Dict]:
        """Return per-(technique, best-chunk) raw scores for threshold calibration.

        Unlike analyze_document, this applies NO verification gate and NO quality
        filter — it emits every technique whose best chunk clears `retrieval_floor`
        (kept below the production RETRIEVAL_THRESHOLD so the calibrator can explore
        operating points beneath the current one), with both raw scores. Metadata
        category exclusion is still honoured, matching production retrieval.

        Each record: {techniqueId, retrieval_score, verification_score, chunk}.
        The caller attaches the gold label (B.1.3 calibrate_thresholds.py).
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return []
        doc_metadata = self.document_metadata.get(doc_id, {})
        excluded_topics = set(doc_metadata.get('excluded_topics', []))

        chunk_embeddings = self.retriever.encode(chunks, convert_to_tensor=True)
        candidates = []
        for tech in self.technique_index:
            if excluded_topics:
                tech_topic = CATEGORY_TO_TOPIC.get(tech['category_id'])
                if tech_topic and tech_topic in excluded_topics:
                    continue
            scores = util.cos_sim(tech['embeddings'], chunk_embeddings)
            max_scores_per_chunk, _ = scores.max(dim=0)
            best_idx = int(max_scores_per_chunk.argmax().item())
            best_score = float(max_scores_per_chunk[best_idx].item())
            if best_score >= retrieval_floor:
                candidates.append({
                    "technique": tech,
                    "chunk": chunks[best_idx],
                    "retrieval_score": best_score,
                })
        if not candidates:
            return []

        pairs = [(c['chunk'], c['technique']['hypothesis']) for c in candidates]
        pred_scores = self.verifier.predict(pairs, apply_softmax=True)
        out = []
        for i, dist in enumerate(pred_scores):
            out.append({
                "techniqueId": candidates[i]['technique']['id'],
                "retrieval_score": candidates[i]['retrieval_score'],
                "verification_score": float(dist[self.entailment_idx]),
                "chunk": candidates[i]['chunk'][:200],
            })
        return out

    def _aggregate_results(self, matches: List[Dict]) -> List[Dict]:
        grouped = {}
        for m in matches:
            tid = m['techniqueId']
            if tid not in grouped:
                grouped[tid] = {
                    "techniqueId": tid,
                    "confidence": m['confidence'],
                    "active": True,
                    "deleted_by": None,
                    "evidence": []
                }
            # Simple dedup by text and append evidence objects
            existing_texts = {e['text'] for e in grouped[tid]['evidence']}
            for evid in m['evidence']:
                evid_text = evid['text'] if isinstance(evid, dict) else evid
                if evid_text not in existing_texts:
                    if isinstance(evid, dict):
                        grouped[tid]['evidence'].append(evid)
                    else:
                        # Legacy format fallback
                        grouped[tid]['evidence'].append({
                            "text": evid,
                            "created_by": "nlu",
                            "active": True,
                            "deleted_by": None
                        })
                    existing_texts.add(evid_text)

        # Limit evidence snippets
        for tid in grouped:
            grouped[tid]['evidence'] = grouped[tid]['evidence'][:3]

        return list(grouped.values())

def run_analysis():
    logger.info("="*70)
    logger.info("NLU ANALYSIS PIPELINE (WITH METADATA-AWARE FILTERING)")
    logger.info("="*70)

    analyzer = NLUAnalyzer()

    files = glob.glob(str(INPUT_DIR / "*.txt"))
    files = [f for f in files if not os.path.basename(f).startswith("temp_")]

    logger.info(f"\n🚀 Starting analysis on {len(files)} documents...")
    logger.info(f"Retrieval threshold: {RETRIEVAL_THRESHOLD}")
    logger.info(f"Verification threshold: {VERIFICATION_THRESHOLD}")
    logger.info(f"Metadata-aware filtering: ENABLED\n")

    full_map = {}
    stats = {
        'total_docs': len(files),
        'processed': 0,
        'skipped_no_safety': 0,
        'linked': 0,
        'unlinked': 0,
        'with_metadata': 0,
        'total_techniques': 0
    }

    for i, file_path in enumerate(files, 1):
        filename_id = os.path.basename(file_path).replace(".txt", "")

        logger.info(f"[{i}/{len(files)}] Scanning: {filename_id}")

        # Track metadata availability
        if filename_id in analyzer.document_metadata:
            stats['with_metadata'] += 1
            metadata = analyzer.document_metadata[filename_id]
            logger.info(f"   Metadata: {metadata.get('document_purpose')} | " +
                       f"Signal: {metadata.get('signal_strength')} | " +
                       f"Depth: {metadata.get('technical_depth')}")

            # Skip documents explicitly marked as having no safety content
            if metadata.get('no_safety_content', False):
                logger.info(f"   ⏭️ SKIPPED: marked as no_safety_content in evidence.json")
                stats['skipped_no_safety'] += 1
                continue

        # Use document ID as the output key (consistent with LLM extraction)
        output_key = filename_id

        # Check if document exists in evidence.json
        normalized_fname = normalize_string(filename_id)
        if normalized_fname in analyzer.evidence_map:
            logger.info(f"   ✓ Found in evidence.json")
            stats['linked'] += 1
        else:
            logger.warning(f"   ⚠️ '{filename_id}' not found in evidence.json")
            stats['unlinked'] += 1

        # Read document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            parts = content.split("-" * 20 + "\n", 1)
            body = parts[1] if len(parts) > 1 else content

        # Analyze
        raw_matches = analyzer.analyze_document(body, filename_id)
        consolidated = analyzer._aggregate_results(raw_matches)

        # Save results
        full_map[output_key] = consolidated
        stats['processed'] += 1
        stats['total_techniques'] += len(consolidated)

        logger.info(f"   → Found {len(consolidated)} verified techniques\n")

    # Save results
    logger.info("="*70)
    logger.info("SAVING RESULTS")
    logger.info("="*70)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(full_map, f, indent=2)

    # Print summary
    logger.info(f"\n✅ Analysis Complete!")
    logger.info(f"\nSummary:")
    logger.info(f"  Documents processed: {stats['processed']}/{stats['total_docs']}")
    if stats['skipped_no_safety'] > 0:
        logger.info(f"  Skipped (no safety content): {stats['skipped_no_safety']}")
    logger.info(f"  With metadata: {stats['with_metadata']}/{stats['total_docs']}")
    logger.info(f"  Linked to evidence: {stats['linked']}")
    logger.info(f"  Unlinked (using filename): {stats['unlinked']}")
    logger.info(f"  Total techniques detected: {stats['total_techniques']}")
    logger.info(f"  Average per document: {stats['total_techniques']/max(stats['processed'],1):.1f}")
    logger.info(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_analysis()
