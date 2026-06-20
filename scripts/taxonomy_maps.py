"""Single source of truth for the category -> excluded-topic-key mapping.

De-duplicated from analyze_nlu.py and semantic_retriever.py (REFACTOR.md §1.9),
which previously each carried their own copy that could silently drift.
The topic keys use unique names that don't collide with the legacy 10-topic
`excluded_topics` values in evidence.json.
"""

CATEGORY_TO_TOPIC = {
    "cat-model-development": "cat_model_development",
    "cat-evaluation": "cat_evaluation",
    "cat-runtime-safety": "cat_runtime_safety",
    "cat-harm-classification": "cat_harm_classification",
    "cat-governance": "cat_governance",
}


def assert_categories_mapped(category_ids) -> list:
    """Return the list of category ids that have no topic mapping (for CI checks)."""
    return [cid for cid in category_ids if cid not in CATEGORY_TO_TOPIC]
