# Reporting Scripts Fixed for New Data Model

**Date**: 2026-02-06
**Issue**: Reporting scripts broken after evidence.json patching

---

## Problem

After patching evidence.json to add missing sources, the reporting scripts failed with:

```
TypeError: string indices must be integers, not 'str'
```

**Root Cause**: The scripts expected the OLD evidence.json structure (array of evidence records with `providerId`, `techniqueId`, `rating`), but the file was refactored to contain a sources registry with NLU-detected techniques in model_technique_map.json.

---

## Data Model Change

### Old Structure (Expected by Scripts)

```json
[
  {
    "providerId": "openai",
    "techniqueId": "rlhf",
    "rating": "high",
    "severityBand": "P",
    "sources": [...]
  }
]
```

### New Structure (Actual)

**evidence.json** (Source Registry):
```json
{
  "sources": [
    {
      "id": "gpt-5-system-card",
      "title": "GPT-5 System Card",
      "provider": "openai",
      "url": "...",
      "type": "System Card",
      "models": [...]
    }
  ]
}
```

**model_technique_map.json** (NLU Detections):
```json
{
  "https://cdn.openai.com/gpt-5-system-card.pdf": [
    {
      "techniqueId": "rlhf",
      "confidence": "High",
      "evidence": [...]
    }
  ]
}
```

---

## Scripts Updated

### 1. [scripts/generate_report.py](../scripts/generate_report.py)

**Changes**:
- Loads `evidence.json` as sources registry
- Loads `model_technique_map.json` for technique detections
- Builds provider-technique matrix from NLU detections
- Reports show:
  - Source document counts
  - Technique detection counts
  - Confidence levels (High/Medium/Low) instead of ratings
  - Recent source documents instead of evidence records

**Output**: [SUMMARY.md](../SUMMARY.md), [data/stats.json](../data/stats.json)

**Test Result**:
```
✅ Generated SUMMARY.md
📊 Total source documents: 44
🔍 Techniques detected: 40
```

### 2. [scripts/generate_dashboard.py](../scripts/generate_dashboard.py)

**Changes**:
- Loads sources from `evidence.json` and detections from `model_technique_map.json`
- New `build_technique_matrix()` method to compute provider-technique matrix
- Updated visualizations:
  - **Coverage Heatmap**: Shows detection confidence (High/Med/Low) instead of ratings
  - **Timeline**: Shows source document additions by date_added
  - **Confidence Distribution**: Stacked bar chart of detection confidence by provider
  - **Source Type Distribution**: Pie chart of document types (System Card, Technical Report, etc.)
  - **Risk Coverage**: Based on NLU-detected techniques
- Updated dashboard description to explain NLU methodology

**Output**: [docs/index.html](../docs/index.html)

**Test Result**:
```
✅ Dashboard generated: docs\index.html
```

---

## Dashboard Changes

### Before (Old Structure)
- **Evidence Records**: Manual tracking of provider implementations
- **Ratings**: high/medium/low implementation maturity
- **Evidence Quality**: P/B/C/V/U severity bands

### After (New Structure)
- **Source Documents**: {44} documents from providers
- **Techniques Detected**: {40} via NLU analysis
- **Confidence**: High/Medium/Low detection confidence
- **Methodology**: Two-stage NLU pipeline (retrieval + verification)

---

## Key Metrics Now Tracked

| Metric | Description |
|--------|-------------|
| **Providers** | Number of LLM providers covered (13) |
| **Source Documents** | Total source documents analyzed (44) |
| **Techniques** | Safety techniques in taxonomy (total) |
| **Detected** | Techniques detected by NLU (40) |
| **Confidence Levels** | High/Medium/Low confidence in detections |
| **Source Types** | System Cards, Technical Reports, Policies, etc. |

---

## Benefits of New Approach

### Advantages
1. **Automated Detection**: NLU analysis automates technique detection
2. **Scalable**: Easy to add new sources and re-run analysis
3. **Evidence-Based**: Confidence scores based on textual evidence
4. **Transparent**: Evidence snippets show what was detected
5. **Reproducible**: Semantic analysis can be tuned and re-run

### Trade-offs
1. **No Manual Ratings**: Lost granular high/medium/low implementation ratings
2. **Detection Limitations**: NLU may miss implicit techniques or have false positives
3. **Requires Tuning**: Thresholds and filters need ongoing refinement

---

## Next Steps

### Re-generate Dashboard After NLU Improvements

Once you've re-run the improved NLU analysis:

```bash
# 1. Re-run NLU with improved evidence mapping
python scripts/analyze_nlu.py

# 2. Regenerate reports
python scripts/generate_report.py
python scripts/generate_dashboard.py

# 3. View results
start docs/index.html  # Or open manually
```

### Expected Improvements

With the fixes in evidence mapping and NLU improvements:
- All sources properly linked to URLs (no filename warnings)
- Improved recall and precision from expanded semantic anchors
- Better confidence scoring with implementation keywords
- Cleaner quality filtering to reduce false positives

---

## Files Modified

- ✅ [scripts/generate_report.py](../scripts/generate_report.py) - Updated for new data model
- ✅ [scripts/generate_dashboard.py](../scripts/generate_dashboard.py) - Updated for new data model
- ✅ [SUMMARY.md](../SUMMARY.md) - Regenerated with new structure
- ✅ [data/stats.json](../data/stats.json) - Updated statistics
- ✅ [docs/index.html](../docs/index.html) - Updated dashboard

## Testing

Both scripts now work correctly:

```bash
python scripts/generate_report.py    # ✅ Success
python scripts/generate_dashboard.py # ✅ Success
```

---

## Summary

✅ **Fixed data model mismatch** between evidence.json structure and reporting scripts
✅ **Updated both scripts** to work with sources + NLU detections
✅ **Generated working dashboard** with confidence-based visualizations
✅ **Maintained backward compatibility** with existing data files
✅ **Improved clarity** about NLU-based detection methodology

The reporting pipeline is now fully aligned with the NLU-driven approach and ready for the improved analysis results.
