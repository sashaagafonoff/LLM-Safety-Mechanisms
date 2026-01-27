import json
import glob
import os
import logging
import re
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder, util

# --- CONFIGURATION ---
INPUT_DIR = Path("data/flat_text")
TECHNIQUES_PATH = Path("data/techniques.json")
EVIDENCE_PATH = Path("data/evidence.json")  # Added path to evidence
OUTPUT_FILE = Path("data/model_technique_map.json")

# STAGE 1: Retrieval Model
RETRIEVAL_MODEL_NAME = "all-mpnet-base-v2"
RETRIEVAL_THRESHOLD = 0.40

# STAGE 2: Verification Model
VERIFICATION_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"
VERIFICATION_THRESHOLD = 0.50

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
        
        self.technique_index = self._load_and_index_techniques()
        self.evidence_map = self._load_evidence_map()

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

        logger.info(f"Indexing {len(sources)} evidence sources for linkage...")
        
        for source in sources:
            # Determine the stable Unique Key for the Output Map
            # Preference: URL > Title > ID
            unique_key = source.get('url')
            if not unique_key or unique_key == "<missing>":
                unique_key = source.get('title')

            # create lookup keys pointing to this unique_key
            
            # 1. Map normalized Title
            if source.get('title'):
                lookup[normalize_string(source['title'])] = unique_key
            
            # 2. Map normalized Model IDs
            for model in source.get('models', []):
                if model.get('modelId'):
                    lookup[normalize_string(model['modelId'])] = unique_key
        
        return lookup

    def _load_and_index_techniques(self) -> List[Dict]:
        with open(TECHNIQUES_PATH, 'r', encoding='utf-8') as f:
            techniques = json.load(f)

        index = []
        logger.info(f"Indexing {len(techniques)} techniques...")

        for tech in techniques:
            profile = tech.get('nlu_profile', {})
            hypothesis = profile.get('entailment_hypothesis', f"The model uses {tech['name']}.")
            targets = [profile.get('primary_concept', tech['description'])]
            targets.extend(profile.get('semantic_anchors', []))
            
            embeddings = self.retriever.encode(targets, convert_to_tensor=True)

            index.append({
                "id": tech['id'],
                "name": tech['name'],
                "hypothesis": hypothesis,
                "embeddings": embeddings,
                "targets": targets
            })
            
        return index

    def _chunk_text(self, text: str) -> List[str]:
        sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if len(s.strip()) > 20]
        chunks = []
        for i in range(0, len(sentences), STRIDE):
            window = ". ".join(sentences[i : i + WINDOW_SIZE]) + "."
            chunks.append(window)
        return chunks

    def analyze_document(self, text: str) -> List[Dict]:
        chunks = self._chunk_text(text)
        if not chunks: return []

        chunk_embeddings = self.retriever.encode(chunks, convert_to_tensor=True)
        candidates = []
        
        for tech in self.technique_index:
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

        if not candidates: return []

        verified_matches = []
        pairs = [(c['chunk'], c['technique']['hypothesis']) for c in candidates]
        pred_scores = self.verifier.predict(pairs, apply_softmax=True)
        entailment_idx = 1 

        for i, score_dist in enumerate(pred_scores):
            entailment_score = score_dist[entailment_idx]
            if entailment_score > VERIFICATION_THRESHOLD:
                cand = candidates[i]
                verified_matches.append({
                    "techniqueId": cand['technique']['id'],
                    "confidence": "High" if entailment_score > 0.8 else "Medium",
                    "evidence": [cand['chunk']] # Formatting for aggregation
                })

        return verified_matches

    def _aggregate_results(self, matches: List[Dict]) -> List[Dict]:
        grouped = {}
        for m in matches:
            tid = m['techniqueId']
            if tid not in grouped:
                grouped[tid] = {
                    "techniqueId": tid,
                    "confidence": m['confidence'],
                    "evidence": []
                }
            # Simple dedup and append
            for evid in m['evidence']:
                if evid not in grouped[tid]['evidence']:
                    grouped[tid]['evidence'].append(evid)
                
        # Limit evidence snippets
        for tid in grouped:
            grouped[tid]['evidence'] = grouped[tid]['evidence'][:3]
            
        return list(grouped.values())

def run_analysis():
    analyzer = NLUAnalyzer()
    
    files = glob.glob(str(INPUT_DIR / "*.txt"))
    full_map = {} 
    
    logger.info(f"🚀 Starting analysis on {len(files)} documents...")
    
    for file_path in files:
        filename_id = os.path.basename(file_path).replace(".txt", "")
        if filename_id.startswith("temp_"): continue
        
        logger.info(f"Scanning: {filename_id}...")
        
        # 1. Resolve Filename -> Evidence Key (URL)
        normalized_fname = normalize_string(filename_id)
        # Try finding by title or model ID using the lookup map
        output_key = analyzer.evidence_map.get(normalized_fname, filename_id)
        
        # If we fell back to filename, log a warning
        if output_key == filename_id and filename_id not in analyzer.evidence_map.values():
             logger.warning(f"   ⚠️ Could not link file '{filename_id}' to an evidence entry. Using filename as key.")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            parts = content.split("-" * 20 + "\n", 1)
            body = parts[1] if len(parts) > 1 else content
            
        raw_matches = analyzer.analyze_document(body)
        consolidated = analyzer._aggregate_results(raw_matches)
        
        # 2. Save under the resolved key (URL or Title)
        full_map[output_key] = consolidated
        logger.info(f"   -> Linked to '{output_key}' with {len(consolidated)} verified techniques.")

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(full_map, f, indent=2)
    
    logger.info(f"\n✅ Analysis Complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_analysis()