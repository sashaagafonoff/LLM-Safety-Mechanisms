# Next Steps for NLU System Improvements

**Date**: 2026-02-06
**Status**: Improvements Applied, Testing Pending

---

## What Was Completed

### ✅ Ground Truth Labeling
- Completed 436 unlabeled document-technique pairs
- Added "Excerpt" column with supporting evidence
- Results saved to [labeling_ground_truth.xlsx](../data/flat_text/labeling_ground_truth.xlsx)

### ✅ NLU System Evaluation
- Ran comprehensive comparison against ground truth
- Identified performance issues: 20.4% recall, 48.8% precision
- Detailed findings in [NLU_EVALUATION_REPORT.md](NLU_EVALUATION_REPORT.md)
- Error analysis in [nlu_vs_groundtruth_comparison.json](nlu_vs_groundtruth_comparison.json)

### ✅ Improvements Applied

**1. Semantic Anchor Expansion**
- Updated 11 techniques in [techniques.json](../data/techniques.json)
- Added 90+ new semantic anchors
- Backup created at [techniques.json.backup](../data/techniques.json.backup)

**2. Threshold Adjustments in analyze_nlu.py**
- `RETRIEVAL_THRESHOLD`: 0.45 → 0.35 (-22%)
- `VERIFICATION_THRESHOLD`: 0.75 → 0.65 (-13%)

**3. Enhanced Quality Filters**
- Added 15+ new exclusion patterns
- Improved glossary/reference detection
- Added comparative mention filtering
- Enhanced discussion vs implementation detection

**4. Implementation-Aware Confidence Scoring**
- Added first-person implementation keyword detection
- Dynamic confidence boosting for strong implementation language

Full details in [IMPROVEMENTS_APPLIED.md](IMPROVEMENTS_APPLIED.md)

---

## What Needs to Be Done

### 🔧 Environment Fix Required

The NLU analysis script requires PyTorch 2.4+, but the current environment has PyTorch 1.13.1.

**Option 1: Upgrade PyTorch (Recommended if GPU available)**
```bash
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Option 2: Install CPU-only PyTorch**
```bash
pip install --upgrade torch torchvision torchaudio
```

**Option 3: Downgrade sentence-transformers (Quick fix)**
```bash
pip install sentence-transformers==2.7.0 transformers==4.41.0
```

### 📊 Re-run NLU Analysis

Once the environment is fixed:

```bash
# 1. Run improved NLU analysis
cd c:\LLM-Safety-Mechanisms
python scripts/analyze_nlu.py

# 2. Re-evaluate against ground truth
python scripts/compare_nlu_vs_groundtruth.py

# 3. Detailed error analysis
python scripts/analyze_nlu_errors.py
```

### 📈 Expected Results

With the improvements, we're targeting:

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| **Recall** | 20.4% | >40% | +2x |
| **Precision** | 48.8% | >55% | +15% |
| **F1 Score** | 0.288 | >0.45 | +56% |

### 🔄 Iteration Plan

If targets aren't met:

1. **Review new false positives/negatives**
   - Run: `python scripts/analyze_nlu_errors.py`
   - Identify patterns in remaining errors

2. **Further refine semantic anchors**
   - Update [techniques.json](../data/techniques.json) for worst-performing techniques
   - Add more implementation-specific phrases

3. **Adjust thresholds incrementally**
   - If recall still low: lower thresholds further (RETRIEVAL_THRESHOLD: 0.30, VERIFICATION_THRESHOLD: 0.60)
   - If precision drops: tighten filters or raise thresholds slightly

4. **Consider hybrid approach**
   - Use NLU for initial screening
   - Manual review for Medium confidence detections
   - Auto-accept High confidence with implementation keywords

---

## Files Modified

### Data Files
- ✅ [data/techniques.json](../data/techniques.json) - Expanded semantic anchors (backup: techniques.json.backup)
- ✅ [data/flat_text/labeling_ground_truth.xlsx](../data/flat_text/labeling_ground_truth.xlsx) - Completed ground truth

### Scripts
- ✅ [scripts/analyze_nlu.py](../scripts/analyze_nlu.py) - Improved thresholds and filters
- ✅ [scripts/complete_labeling.py](../scripts/complete_labeling.py) - Ground truth labeling script
- ✅ [scripts/compare_nlu_vs_groundtruth.py](../scripts/compare_nlu_vs_groundtruth.py) - Evaluation script
- ✅ [scripts/analyze_nlu_errors.py](../scripts/analyze_nlu_errors.py) - Error analysis script
- ✅ [scripts/improve_nlu_system.py](../scripts/improve_nlu_system.py) - Improvement automation

### Reports
- ✅ [reports/NLU_EVALUATION_REPORT.md](NLU_EVALUATION_REPORT.md) - Comprehensive evaluation
- ✅ [reports/IMPROVEMENTS_APPLIED.md](IMPROVEMENTS_APPLIED.md) - Implementation details
- ✅ [reports/nlu_vs_groundtruth_comparison.json](nlu_vs_groundtruth_comparison.json) - Detailed metrics
- ✅ [reports/NEXT_STEPS.md](NEXT_STEPS.md) - This document

---

## Quick Command Reference

```bash
# Fix PyTorch compatibility (choose one):
pip install sentence-transformers==2.7.0 transformers==4.41.0  # Quick fix
pip install --upgrade torch  # Full upgrade

# Run analysis pipeline:
python scripts/analyze_nlu.py                          # Generate detections
python scripts/compare_nlu_vs_groundtruth.py           # Evaluate performance
python scripts/analyze_nlu_errors.py                   # Analyze errors

# Rollback if needed:
cp data/techniques.json.backup data/techniques.json    # Restore semantic anchors
git checkout scripts/analyze_nlu.py                    # Restore original thresholds
```

---

## Summary

**Status**: All improvements successfully applied and ready for testing
**Blocker**: PyTorch version incompatibility (easy fix)
**Next Action**: Fix PyTorch, re-run analysis, evaluate results
**Expected Outcome**: 2x improvement in recall, modest precision improvement

The groundwork is complete. Once the environment is fixed, running the three analysis scripts will show whether the improvements achieve the target metrics.
