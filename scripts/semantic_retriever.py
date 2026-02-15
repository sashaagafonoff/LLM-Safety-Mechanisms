import json
import numpy as np
import glob
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
from robust_tokenizer import create_chunks_from_text

# --- CONFIGURATION ---
TECHNIQUES_PATH = Path("data/techniques.json")
CATEGORIES_PATH = Path("data/categories.json")
EVIDENCE_PATH = Path("data/evidence.json")
INPUT_DIR = Path("data/flat_text")
MODEL_NAME = "all-mpnet-base-v2"  # The "Gold Standard" for general semantic search
SIMILARITY_THRESHOLD = 0.45       # Lower = More matches (High Recall), Higher = More Precision
WINDOW_SIZE = 3                   # Number of sentences per chunk
STRIDE = 2                        # Overlap (move 2 sentences forward each time)

class SemanticRetriever:
    def __init__(self, techniques_path: Path, model_name: str):
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)

        # Load taxonomy and metadata
        self.categories = self._load_categories()
        self.evidence_metadata = self._load_evidence_metadata()

        # Load and Index Techniques
        self.technique_index = self._build_technique_index(techniques_path)

    def _load_categories(self) -> Dict[str, Dict]:
        """Load categories for category-aware filtering."""
        with open(CATEGORIES_PATH, 'r', encoding='utf-8') as f:
            cats = json.load(f)
        return {cat['id']: cat for cat in cats}

    def _load_evidence_metadata(self) -> Dict[str, Dict]:
        """Load content_metadata from evidence.json for context-aware filtering."""
        if not EVIDENCE_PATH.exists():
            print(f"⚠️ Evidence file not found at {EVIDENCE_PATH}")
            return {}

        with open(EVIDENCE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metadata_map = {}
        for source in data.get('sources', []):
            doc_id = source.get('id')
            if doc_id and 'content_metadata' in source:
                metadata_map[doc_id] = source['content_metadata']

        print(f"✓ Loaded metadata for {len(metadata_map)} documents")
        return metadata_map

    def _build_technique_index(self, path: Path) -> List[Dict]:
        """
        Creates a Multi-Vector Index with category context.
        Each technique gets multiple vectors: 1 for Primary Concept + N for Anchors.
        """
        with open(path, 'r', encoding='utf-8') as f:
            techniques = json.load(f)

        index = []
        print("Indexing techniques with category context...")

        for tech in techniques:
            profile = tech.get('nlu_profile', {})

            # 1. Embed the Primary Concept (The Definition)
            concept_text = profile.get('primary_concept', tech['description'])

            # 2. Embed the Anchors (The Synonyms)
            anchors = profile.get('semantic_anchors', [])

            # Combine all text targets for this technique
            targets = [concept_text] + anchors

            # Generate embeddings in one batch
            embeddings = self.model.encode(targets, convert_to_tensor=True)

            # Get category for this technique
            category = self.categories.get(tech.get('categoryId'))

            # Store them with category context
            # We treat each anchor as a valid entry point to find the technique
            for i, emb in enumerate(embeddings):
                index.append({
                    "technique_id": tech['id'],
                    "technique_name": tech['name'],
                    "technique_category_id": tech.get('categoryId'),
                    "technique_category_name": category['name'] if category else 'Unknown',
                    "match_source": "concept" if i == 0 else f"anchor: {targets[i]}",
                    "embedding": emb
                })

        print(f"✅ Indexed {len(index)} vector targets for {len(techniques)} techniques.")
        return index

    def _chunk_text(self, text: str) -> List[str]:
        """
        Splits text into sliding windows of sentences.
        """
        return create_chunks_from_text(
            text,
            window_size=WINDOW_SIZE,
            stride=STRIDE,
            min_sentence_length=10,
            min_chunk_length=20
        )

    def scan_document(self, text: str, doc_id: Optional[str] = None) -> List[Dict]:
        """
        Scans a document and returns Candidate Matches with metadata-aware filtering.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return []

        # Get document metadata if available
        doc_metadata = self.evidence_metadata.get(doc_id, {}) if doc_id else {}
        primary_topics = set(doc_metadata.get('primary_topics', []))
        excluded_topics = set(doc_metadata.get('excluded_topics', []))
        temporal_focus = doc_metadata.get('temporal_focus', 'unknown')
        signal_strength = doc_metadata.get('signal_strength', 'medium')

        print(f"\n  Document metadata:")
        if doc_metadata:
            print(f"    Primary topics: {', '.join(primary_topics) if primary_topics else 'none'}")
            print(f"    Excluded topics: {', '.join(excluded_topics) if excluded_topics else 'none'}")
            print(f"    Temporal focus: {temporal_focus}")
            print(f"    Signal strength: {signal_strength}")
        else:
            print(f"    No metadata available")

        # Embed all document chunks at once (Batch processing)
        chunk_embeddings = self.model.encode(chunks, convert_to_tensor=True)

        candidates = []
        filtered_by_metadata = 0

        # Compare every chunk against every technique vector
        # Note: In a large system, we'd use FAISS here. For 50 docs, explicit loop is fine.

        from sentence_transformers.util import cos_sim

        # Iterate through techniques in our index
        for target in self.technique_index:
            # Category-aware filtering using metadata
            tech_cat_id = target['technique_category_id']

            # Map technique category to topic taxonomy
            # This helps filter false positives where document metadata excludes the category
            category_to_topic_map = {
                'cat-model-development': 'cat_model_development',
                'cat-evaluation': 'cat_evaluation',
                'cat-runtime-safety': 'cat_runtime_safety',
                'cat-harm-classification': 'cat_harm_classification',
                'cat-governance': 'cat_governance'
            }

            topic = category_to_topic_map.get(tech_cat_id)

            # Skip if document metadata explicitly excludes this topic
            if topic and excluded_topics and topic in excluded_topics:
                filtered_by_metadata += 1
                continue

            # Calculate similarity of this technique vector vs ALL doc chunks
            scores = cos_sim(target['embedding'], chunk_embeddings)[0]

            # Filter by Threshold
            # indices where score > threshold
            matches = (scores > SIMILARITY_THRESHOLD).nonzero()

            for idx in matches:
                idx = idx.item()
                score = scores[idx].item()

                candidates.append({
                    "technique_id": target['technique_id'],
                    "technique_name": target['technique_name'],
                    "technique_category": target['technique_category_name'],
                    "score": round(score, 3),
                    "chunk_text": chunks[idx],
                    "match_type": target['match_source'],
                    "signal_strength": signal_strength,
                    "temporal_focus": temporal_focus
                })

        if filtered_by_metadata > 0:
            print(f"  Filtered {filtered_by_metadata} technique vectors by metadata exclusions")

        # Deduplication Strategy:
        # A single chunk might match both "RLHF" (Concept) and "PPO" (Anchor).
        # We generally want to keep the highest score per Technique per Chunk.
        return self._deduplicate_candidates(candidates)

    def _deduplicate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        If a chunk matches the same technique multiple times (via different anchors),
        keep only the strongest match.
        """
        unique_hits = {} # Key: (chunk_text, technique_id)
        
        for c in candidates:
            key = (c['chunk_text'], c['technique_id'])
            if key not in unique_hits or c['score'] > unique_hits[key]['score']:
                unique_hits[key] = c
                
        return sorted(list(unique_hits.values()), key=lambda x: x['score'], reverse=True)

# --- EXECUTION ---

def run_retrieval_stage():
    retriever = SemanticRetriever(TECHNIQUES_PATH, MODEL_NAME)

    # Grab one file to test
    files = sorted(INPUT_DIR.glob("*.txt"))
    if not files:
        print("No input files found.")
        return

    test_file = files[0] # Pick the first one for demonstration
    doc_id = test_file.stem
    print(f"\n🔎 Scanning: {test_file.name} (ID: {doc_id})...")

    with open(test_file, 'r', encoding='utf-8') as f:
        text = f.read()

    candidates = retriever.scan_document(text, doc_id=doc_id)

    print(f"\nFound {len(candidates)} candidate matches (Threshold: {SIMILARITY_THRESHOLD}):\n")

    # Group by technique for cleaner display
    by_technique = {}
    for match in candidates:
        tid = match['technique_id']
        if tid not in by_technique:
            by_technique[tid] = {
                'name': match['technique_name'],
                'category': match['technique_category'],
                'max_score': match['score'],
                'match_count': 0,
                'best_match': match
            }
        by_technique[tid]['match_count'] += 1
        if match['score'] > by_technique[tid]['max_score']:
            by_technique[tid]['max_score'] = match['score']
            by_technique[tid]['best_match'] = match

    # Sort by max score
    sorted_techniques = sorted(by_technique.items(), key=lambda x: x[1]['max_score'], reverse=True)

    # Show top 10 techniques
    print("Top detected techniques:\n")
    for tid, info in sorted_techniques[:10]:
        match = info['best_match']
        print(f"[{info['max_score']:.3f}] {info['name']}")
        print(f"   Category: {info['category']}")
        print(f"   Matches: {info['match_count']}")
        print(f"   Signal: {match['signal_strength']} | Focus: {match['temporal_focus']}")
        print(f"   Best trigger: {match['match_type']}")
        print(f"   Context: \"{match['chunk_text'][:120]}...\"")
        print("-" * 80)

if __name__ == "__main__":
    run_retrieval_stage()