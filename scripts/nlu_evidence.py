"""Small NLU-evidence helper with no heavy dependencies, so the logic stays
unit-testable without importing sentence-transformers/torch (mirrors
nli_utils.py's convention).

See docs/workplan/2026-08-execution-plan.md T2.4: NLU detections previously
published only a High/Medium/Low confidence label. This persists the raw
Stage 1 (retrieval) / Stage 2 (verification) scores alongside the existing
provenance fields, so downstream calibration (Phase 4) has real numbers to
work with instead of only the coarse label.
"""

from typing import Dict


def build_nlu_evidence(text: str, retrieval_score: float, verification_score: float) -> Dict:
    """Build a single NLU evidence dict.

    Pure function — no model/state dependency — so it is unit-testable
    without loading any NLU models.
    """
    return {
        "text": text,
        "created_by": "nlu",
        "active": True,
        "deleted_by": None,
        "retrieval_score": round(float(retrieval_score), 4),
        "verification_score": round(float(verification_score), 4),
    }
