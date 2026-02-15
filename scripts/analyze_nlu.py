import json
import glob
import os
import logging
import re
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from robust_tokenizer import create_chunks_from_text

# --- CONFIGURATION ---
INPUT_DIR = Path("data/flat_text")
TECHNIQUES_PATH = Path("data/techniques.json")
CATEGORIES_PATH = Path("data/categories.json")
EVIDENCE_PATH = Path("data/evidence.json")
OUTPUT_FILE = Path("data/model_technique_map.json")

# STAGE 1: Retrieval Model
RETRIEVAL_MODEL_NAME = "all-mpnet-base-v2"
RETRIEVAL_THRESHOLD = 0.35  # Lowered from 0.45 to improve recall

# STAGE 2: Verification Model
VERIFICATION_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"
VERIFICATION_THRESHOLD = 0.65  # Lowered from 0.75 to improve recall

# Text Processing
WINDOW_SIZE = 3
STRIDE = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NLU_Analyzer")

def normalize_string(s: str) -> str:
    """Normalizes strings for matching (lowercase, alphanumeric only)."""
    if not s: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

class NLUAnalyzer:
    def __init__(self):
        logger.info("⏳ Loading Retrieval Model (Bi-Encoder)...")
        self.retriever = SentenceTransformer(RETRIEVAL_MODEL_NAME)

        logger.info("⏳ Loading Verification Model (Cross-Encoder)...")
        self.verifier = CrossEncoder(VERIFICATION_MODEL_NAME)

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
        Enhanced heuristic filter to catch 'Glossary' definitions or weak references.
        Returns True if the text should be discarded.
        """
        text_lower = text.lower()

        # 1. The Glossary/Reference Section Trap
        glossary_patterns = [
            "glossary", "definition:", "definitions:",
            "overview:", "background:", "related work:",
            "literature review:", "references:", "bibliography:"
        ]
        if any(pattern in text_lower[:100] for pattern in glossary_patterns):
            return True

        # 2. The "Future Work" Trap - Expanded
        future_patterns = [
            "future work", "we plan to", "we intend to",
            "planned for", "will implement", "may implement",
            "could implement", "should implement", "might use",
            "proposed approach", "recommended approach",
            "potential use of", "considering", "exploring the use"
        ]
        if any(pattern in text_lower for pattern in future_patterns):
            return True

        # 3. Comparative/Contrastive Mentions
        comparative_patterns = [
            "unlike", "compared to", "in contrast to",
            "as opposed to", "rather than", "instead of"
        ]
        if any(pattern in text_lower for pattern in comparative_patterns):
            return True

        # 4. Discussion vs Implementation
        # Check for implementation indicators
        implementation_keywords = [
            "we use", "we employ", "we implement", "we apply",
            "we deploy", "we utilize", "our system", "our model",
            "we train", "we trained", "incorporated", "deployed",
            "used in", "applied to", "implemented in"
        ]
        has_implementation = any(keyword in text_lower for keyword in implementation_keywords)

        # Check for discussion-only indicators
        discussion_keywords = [
            "discussed in", "described in", "mentioned in",
            "refers to", "defined as", "known as",
            "examples include", "such as", "e.g."
        ]
        has_discussion_only = any(keyword in text_lower for keyword in discussion_keywords)

        # If has discussion markers but no implementation markers, likely not a real implementation
        if has_discussion_only and not has_implementation:
            return True

        # 5. Access Control specific fix
        # "Access Control" must imply permissions/login, NOT "refusal"
        if technique_name == "Access Control Documentation":
            if any(w in text_lower for w in ["refus", "declin", "answer", "abstain"]):
                return True # This is Refusal, not Access Control

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

        # Category to topic mapping for metadata filtering
        # Use unique names that don't collide with old 10-topic excluded_topics
        category_to_topic_map = {
            'cat-model-development': 'cat_model_development',
            'cat-evaluation': 'cat_evaluation',
            'cat-runtime-safety': 'cat_runtime_safety',
            'cat-harm-classification': 'cat_harm_classification',
            'cat-governance': 'cat_governance'
        }

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
        entailment_idx = 1

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
    logger.info(f"  With metadata: {stats['with_metadata']}/{stats['total_docs']}")
    logger.info(f"  Linked to evidence: {stats['linked']}")
    logger.info(f"  Unlinked (using filename): {stats['unlinked']}")
    logger.info(f"  Total techniques detected: {stats['total_techniques']}")
    logger.info(f"  Average per document: {stats['total_techniques']/stats['processed']:.1f}")
    logger.info(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_analysis()
