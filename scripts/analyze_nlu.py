import json
import glob
import os
import logging
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder, util

# --- CONFIGURATION ---
INPUT_DIR = Path("data/flat_text")
TECHNIQUES_PATH = Path("data/techniques.json")
OUTPUT_FILE = Path("data/model_technique_map.json")

# STAGE 1: Retrieval Model (Broad Net)
# Optimized for semantic similarity. 
RETRIEVAL_MODEL_NAME = "all-mpnet-base-v2"
RETRIEVAL_THRESHOLD = 0.40  # Lowered slightly to ensure we don't miss vague references

# STAGE 2: Verification Model (The Judge)
# Trained on NLI (Entailment) tasks. 
VERIFICATION_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"
VERIFICATION_THRESHOLD = 0.50 # >0.5 means "Entailment" is more likely than "Neutral/Contradiction"

# Text Processing
WINDOW_SIZE = 3   # Sentences per chunk
STRIDE = 2        # Overlap

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NLU_Analyzer")

class NLUAnalyzer:
    def __init__(self):
        logger.info("⏳ Loading Retrieval Model (Bi-Encoder)...")
        self.retriever = SentenceTransformer(RETRIEVAL_MODEL_NAME)
        
        logger.info("⏳ Loading Verification Model (Cross-Encoder)...")
        self.verifier = CrossEncoder(VERIFICATION_MODEL_NAME)
        
        self.technique_index = self._load_and_index_techniques()

    def _load_and_index_techniques(self) -> List[Dict]:
        """
        Loads techniques.json and creates embedding vectors for Concepts and Anchors.
        """
        with open(TECHNIQUES_PATH, 'r', encoding='utf-8') as f:
            techniques = json.load(f)

        index = []
        logger.info(f"Indexing {len(techniques)} techniques...")

        for tech in techniques:
            profile = tech.get('nlu_profile', {})
            hypothesis = profile.get('entailment_hypothesis', f"The model uses {tech['name']}.")
            
            # Targets for retrieval (Concept + Anchors)
            targets = [profile.get('primary_concept', tech['description'])]
            targets.extend(profile.get('semantic_anchors', []))
            
            # Embed all targets at once
            embeddings = self.retriever.encode(targets, convert_to_tensor=True)

            index.append({
                "id": tech['id'],
                "name": tech['name'],
                "hypothesis": hypothesis, # Used in Stage 2
                "embeddings": embeddings,  # Used in Stage 1
                "targets": targets # For debug references
            })
            
        return index

    def _chunk_text(self, text: str) -> List[str]:
        """Splits text into sliding windows of sentences."""
        # Simple split by period. For production, use nltk.sent_tokenize
        sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if len(s.strip()) > 20]
        
        chunks = []
        for i in range(0, len(sentences), STRIDE):
            window = ". ".join(sentences[i : i + WINDOW_SIZE]) + "."
            chunks.append(window)
        return chunks

    def analyze_document(self, text: str) -> List[Dict]:
        """
        Runs the 2-Stage Pipeline on a single document.
        """
        chunks = self._chunk_text(text)
        if not chunks: return []

        # --- STAGE 1: SEMANTIC RETRIEVAL ---
        # Embed all chunks
        chunk_embeddings = self.retriever.encode(chunks, convert_to_tensor=True)
        
        candidates = []
        
        # Compare chunks against every technique
        for tech in self.technique_index:
            # Cosine Similarity: Tech Vectors vs Chunk Vectors
            # Returns a matrix [num_targets x num_chunks]
            scores = util.cos_sim(tech['embeddings'], chunk_embeddings)
            
            # Find max similarity for this technique across all chunks
            # We take the max score among the tech's anchors for each chunk
            max_scores_per_chunk, _ = scores.max(dim=0) 
            
            # Filter chunks that pass the threshold
            passing_indices = (max_scores_per_chunk > RETRIEVAL_THRESHOLD).nonzero()
            
            for idx in passing_indices:
                idx = idx.item()
                candidates.append({
                    "chunk": chunks[idx],
                    "technique": tech,
                    "retrieval_score": max_scores_per_chunk[idx].item()
                })

        if not candidates:
            return []

        # Deduplicate candidates (keep highest score per tech/chunk pair)
        # to avoid running verification on same pair multiple times
        # (omitted for brevity, but recommended in prod)

        # --- STAGE 2: ENTAILMENT VERIFICATION ---
        verified_matches = []
        
        # Prepare pairs for Cross-Encoder: (Premise, Hypothesis)
        pairs = [(c['chunk'], c['technique']['hypothesis']) for c in candidates]
        
        # Predict scores (logits) -> Convert to Probabilities (softmax)
        # NLI models usually output 3 classes: [Contradiction, Entailment, Neutral] 
        # OR [Entailment, Contradiction, Neutral]. 
        # cross-encoder/nli-deberta-v3-small outputs: 0:Contradiction, 1:Entailment, 2:Neutral
        
        pred_scores = self.verifier.predict(pairs, apply_softmax=True)
        
        # Map label indices (Specific to nli-deberta-v3-small)
        # If you change the model, check its HuggingFace card for label mapping!
        label_mapping = ["contradiction", "entailment", "neutral"]
        entailment_idx = 1 

        for i, score_dist in enumerate(pred_scores):
            entailment_score = score_dist[entailment_idx]
            
            if entailment_score > VERIFICATION_THRESHOLD:
                cand = candidates[i]
                verified_matches.append({
                    "technique_id": cand['technique']['id'],
                    "confidence": "High" if entailment_score > 0.8 else "Medium",
                    "score": float(f"{entailment_score:.3f}"),
                    "evidence_snippet": cand['chunk']
                })

        return verified_matches

    def _aggregate_results(self, matches: List[Dict]) -> List[Dict]:
        """
        Groups snippets by technique ID.
        """
        grouped = {}
        for m in matches:
            tid = m['technique_id']
            if tid not in grouped:
                grouped[tid] = {
                    "techniqueId": tid,
                    "confidence": m['confidence'],
                    "evidence": []
                }
            # Add snippet if not already present (simple dedup)
            if m['evidence_snippet'] not in grouped[tid]['evidence']:
                grouped[tid]['evidence'].append(m['evidence_snippet'])
                
        # Limit evidence to top 3 snippets per technique to keep JSON clean
        for tid in grouped:
            grouped[tid]['evidence'] = grouped[tid]['evidence'][:3]
            
        return list(grouped.values())

def run_analysis():
    analyzer = NLUAnalyzer()
    
    files = glob.glob(str(INPUT_DIR / "*.txt"))
    full_map = {} # Key: SourceID, Value: List of Techniques
    
    logger.info(f"🚀 Starting analysis on {len(files)} documents...")
    
    for file_path in files:
        source_id = os.path.basename(file_path).replace(".txt", "")
        # Filter out temp files if any remain
        if source_id.startswith("temp_"): continue
        
        logger.info(f"Scanning: {source_id}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip header lines to get to body
            content = f.read()
            parts = content.split("-" * 20 + "\n", 1)
            body = parts[1] if len(parts) > 1 else content
            
        raw_matches = analyzer.analyze_document(body)
        consolidated = analyzer._aggregate_results(raw_matches)
        
        full_map[source_id] = consolidated
        logger.info(f"   -> Found {len(consolidated)} verified techniques.")

    # Save Final Map
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(full_map, f, indent=2)
    
    logger.info(f"\n✅ Analysis Complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_analysis()