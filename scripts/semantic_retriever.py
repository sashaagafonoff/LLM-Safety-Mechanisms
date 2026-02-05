import json
import numpy as np
import glob
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
from robust_tokenizer import create_chunks_from_text

# --- CONFIGURATION ---
TECHNIQUES_PATH = "data/techniques.json"
INPUT_DIR = "data/flat_text"
MODEL_NAME = "all-mpnet-base-v2"  # The "Gold Standard" for general semantic search
SIMILARITY_THRESHOLD = 0.45       # Lower = More matches (High Recall), Higher = More Precision
WINDOW_SIZE = 3                   # Number of sentences per chunk
STRIDE = 2                        # Overlap (move 2 sentences forward each time)

class SemanticRetriever:
    def __init__(self, techniques_path: str, model_name: str):
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        # Load and Index Techniques
        self.technique_index = self._build_technique_index(techniques_path)

    def _build_technique_index(self, path: str) -> List[Dict]:
        """
        Creates a Multi-Vector Index.
        Each technique gets multiple vectors: 1 for Primary Concept + N for Anchors.
        """
        with open(path, 'r') as f:
            techniques = json.load(f)
            
        index = []
        print("Indexing techniques...")
        
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
            
            # Store them
            # We treat each anchor as a valid entry point to find the technique
            for i, emb in enumerate(embeddings):
                index.append({
                    "technique_id": tech['id'],
                    "technique_name": tech['name'],
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

    def scan_document(self, text: str) -> List[Dict]:
        """
        Scans a document and returns Candidate Matches.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return []
            
        # Embed all document chunks at once (Batch processing)
        chunk_embeddings = self.model.encode(chunks, convert_to_tensor=True)
        
        candidates = []
        
        # Compare every chunk against every technique vector
        # Note: In a large system, we'd use FAISS here. For 50 docs, explicit loop is fine.
        
        from sentence_transformers.util import cos_sim
        
        # Iterate through techniques in our index
        for target in self.technique_index:
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
                    "score": round(score, 3),
                    "chunk_text": chunks[idx],
                    "match_type": target['match_source']
                })
        
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
    files = glob.glob(f"{INPUT_DIR}/*.txt")
    if not files:
        print("No input files found.")
        return

    test_file = files[0] # Pick the first one for demonstration
    print(f"\n🔎 Scanning: {os.path.basename(test_file)}...")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        text = f.read()
        
    candidates = retriever.scan_document(text)
    
    print(f"\nFound {len(candidates)} candidate matches (Threshold: {SIMILARITY_THRESHOLD}):\n")
    
    # Show top 5 findings
    for match in candidates[:5]:
        print(f"[{match['score']}] ID: {match['technique_id']}")
        print(f"   Trigger: {match['match_type']}")
        print(f"   Context: \"{match['chunk_text'][:100]}...\"")
        print("-" * 50)

if __name__ == "__main__":
    run_retrieval_stage()