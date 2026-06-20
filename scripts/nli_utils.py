"""Small NLI helper with no heavy dependencies, so the logic stays unit-testable
without importing sentence-transformers/torch.

See REFACTOR.md §1.3: the entailment class index must be read from the model's
`id2label` config, not hard-coded.
"""


def resolve_entailment_index(id2label, default: int = 1) -> int:
    """Return the index of the 'entailment' class from a model's id2label map.

    `cross-encoder/nli-deberta-v3-*` conventionally uses
    ``{0: 'contradiction', 1: 'entailment', 2: 'neutral'}`` — but that is a
    property of the checkpoint config, not a guarantee. Resolve it dynamically
    and fall back to `default` only if the config is unavailable.
    """
    if id2label:
        for idx, label in id2label.items():
            if str(label).strip().lower() == "entailment":
                return int(idx)
    return default
