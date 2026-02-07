# NLU System Evaluation Report

**Date**: 2026-02-06
**Evaluation Type**: Automated NLU predictions vs. Ground Truth labels
**Ground Truth Size**: 484 labeled document-technique pairs
**NLU Predictions**: 242 detected technique mentions

---

## Executive Summary

The automated NLU system (analyze_nlu.py) was evaluated against manually labeled ground truth data. The system shows **low recall (20.4%)** but **moderate precision (48.8%)**, resulting in an **F1 score of 0.288**. This indicates the system is overly conservative, missing most actual implementations while still generating some false positives.

### Key Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Precision** | 0.488 | Of all detections, 48.8% were correct |
| **Recall** | 0.204 | Only 20.4% of actual implementations were detected |
| **F1 Score** | 0.288 | Overall performance is modest |
| **Accuracy** | 0.785 | 78.5% overall (inflated by many true negatives) |

### Confusion Matrix

| | Predicted Positive | Predicted Negative |
|---|---|---|
| **Actually Positive** | 21 (TP) | 82 (FN) |
| **Actually Negative** | 22 (FP) | 359 (TN) |

---

## Performance Breakdown

### Detection Rate by Ground Truth Label

| Ground Truth | Detected | Total | Detection Rate |
|--------------|----------|-------|----------------|
| **YES** (Clear implementation) | 8 | 30 | **26.7%** ⚠️ |
| **PARTIAL** (Partial/mentioned) | 13 | 73 | **17.8%** ⚠️ |
| **UNCLEAR** (Ambiguous) | 5 | 47 | 10.6% |
| **NO** (Not present) | 17 | 334 | 5.1% ⚠️ (false positives) |

**Key Issue**: The system only detects 1 in 4 clear implementations (YES labels) and misses most partial implementations.

---

## Error Analysis

### False Negatives (82 total) - Techniques NLU Missed

**Most Commonly Missed Techniques:**
1. **Access Control Documentation** (9 missed)
2. **Transparency Artifacts** (8 missed)
3. **Red Team Exercises** (7 missed)
4. **System Prompts / Metaprompts** (5 missed)
5. **Refusal / Abstention** (5 missed)
6. **Capability Threshold Monitoring** (4 missed)
7. **Reinforcement Learning from Human Feedback** (4 missed)
8. **Training Data Filtering** (4 missed)
9. **Safety Benchmarking** (4 missed)

**Sources with Most Missed Techniques:**
- Claude Opus 4.5 System Card: 14 missed
- GPT-5 System Card: 13 missed
- GPT-4o System Card: 11 missed
- Anthropic RSP: 11 missed
- Gemini 1.5 Paper: 8 missed

**Label Breakdown:**
- PARTIAL: 60 missed (82% of all PARTIAL labels were missed)
- YES: 22 missed (73% of all YES labels were missed)

### False Positives (22 total) - Incorrect NLU Detections

**Most Commonly Over-Detected Techniques:**
1. **Incident Reporting Systems** (3 false positives)
2. **Automated Red Teaming** (2 false positives)
3. **Contextual Safety Assessment** (2 false positives)
4. **PII Detection & Redaction** (2 false positives)
5. **Input Guardrails** (2 false positives)

**Sources with Most False Positives:**
- Gemini 1.5 Paper: 8 false positives
- Cohere Safety Framework: 5 false positives
- DeepSeek-R1 Paper: 4 false positives

**Label Breakdown:**
- NO: 17 false positives (detecting techniques that aren't present)
- UNCLEAR: 5 false positives (detecting ambiguous cases)

**Example False Positive Patterns:**
- Detecting techniques in glossaries or reference sections
- Confusing "discussion of" with "implementation of"
- Picking up on "future work" or "recommendations" mentions

### True Positives (21 total) - What NLU Gets Right

**Successfully Detected Techniques:**
- Contextual Safety Assessment (3x)
- Capability Threshold Monitoring (3x)
- Jailbreak & Injection Defense (3x)
- Safety Benchmarking (3x)
- Reinforcement Learning from Human Feedback (2x)
- Red Team Exercises (2x)

**Success Rate by Label:**
- PARTIAL: 13 correctly detected (17.8% of all PARTIAL)
- YES: 8 correctly detected (26.7% of all YES)

---

## Threshold Sensitivity Analysis

| Min Confidence | Predictions | Precision | Recall | F1 Score |
|----------------|-------------|-----------|--------|----------|
| **High only** | 194 | 0.444 | 0.155 | 0.230 |
| **Medium+** | 242 | 0.488 | 0.204 | 0.288 |

**Finding**: Restricting to high-confidence predictions makes performance worse, not better. The confidence calibration may need improvement.

---

## Recommendations for Improvement

### 1. Address Low Recall (Priority: HIGH)

**Problem**: Missing 80% of actual implementations (82 false negatives)

**Recommendations:**
- ✅ **Expand semantic anchors** in [techniques.json](../data/techniques.json) with more varied terminology
  - Review missed techniques (Access Control, Transparency Artifacts, Red Team Exercises)
  - Add implementation-specific phrases for each technique

- ✅ **Lower entailment threshold** in [analyze_nlu.py](../scripts/analyze_nlu.py)
  - Current threshold may be too strict
  - Test thresholds between 0.5-0.7 for cross-encoder verification

- ✅ **Add implementation keywords** to detection logic
  - "incorporate", "utilize", "leverage", "deploy", "apply", "enforce"
  - Look for system-level implementation language

- ✅ **Adjust retrieval thresholds**
  - Stage 1 (all-mpnet-base-v2) may be filtering out too many candidates
  - Lower the similarity threshold to capture more potential matches

### 2. Reduce False Positives (Priority: MEDIUM)

**Problem**: 22 incorrect detections (48.8% precision)

**Recommendations:**
- ✅ **Strengthen quality filters** in [analyze_nlu.py](../scripts/analyze_nlu.py):150-180
  - Add patterns for: "overview", "background", "related work", "literature review"
  - Filter out glossary sections more aggressively
  - Detect and exclude comparative mentions ("unlike X", "compared to Y")

- ✅ **Improve context analysis**
  - Distinguish "discusses technique" vs "implements technique"
  - Look for first-person implementation language ("we use", "our system")

- ✅ **Add negative exclusion patterns**
  - "proposed by", "suggested by", "recommended approach"
  - "could implement", "should consider", "might use"
  - "alternative approaches", "other methods"

### 3. Improve Specific Technique Detection (Priority: HIGH)

**Problem**: Poor detection of common techniques

**Action Items:**

For **Access Control Documentation** (9 missed):
- Add semantic anchors: "access control", "authentication", "authorization", "permission model", "role-based access"
- Look for security and governance language

For **Transparency Artifacts** (8 missed):
- Add anchors: "model card", "system card", "documentation", "disclosure", "transparency report"
- Technical report titles often count as transparency artifacts

For **Red Team Exercises** (7 missed):
- Add anchors: "adversarial testing", "security assessment", "penetration testing", "stress testing"
- Look for methodology descriptions, not just the term "red team"

For **System Prompts / Metaprompts** (5 missed):
- Add anchors: "system message", "system instruction", "preamble", "metaprompt"
- Look for prompt engineering language

For **Refusal / Abstention** (5 missed):
- Add anchors: "decline", "refuse to answer", "cannot assist", "content policy enforcement"
- Look for refusal examples and policy language

### 4. Source-Specific Improvements (Priority: MEDIUM)

**Problem**: Major system cards have high miss rates

**Recommendations:**
- **Claude Opus 4.5 System Card** (14 missed): Review for overlooked safety sections
- **GPT-5 System Card** (13 missed): Check if safety methodology sections are being analyzed
- **Anthropic RSP** (11 missed): RSP uses unique terminology - update semantic anchors accordingly

### 5. Reduce Gemini 1.5 Paper False Positives (Priority: LOW)

**Problem**: 8 false positives in Gemini 1.5 Paper

**Recommendations:**
- Review this document's structure - may have extensive related work section
- Add filters for academic paper patterns (citations, references)
- Improve detection of "evaluation" vs "implementation"

---

## Next Steps

1. **Update [techniques.json](../data/techniques.json)**:
   - Expand semantic anchors for top 10 missed techniques
   - Add implementation-specific phrases
   - Review and validate nlu_profiles

2. **Adjust [analyze_nlu.py](../scripts/analyze_nlu.py) thresholds**:
   - Lower Stage 1 retrieval threshold from current value
   - Lower Stage 2 entailment threshold to ~0.6
   - Test on ground truth subset before full re-run

3. **Strengthen quality filters**:
   - Add patterns identified in false positive analysis
   - Improve exclusion logic for non-implementation contexts

4. **Re-run evaluation**:
   - After changes, run: `python scripts/analyze_nlu.py`
   - Then re-evaluate: `python scripts/compare_nlu_vs_groundtruth.py`
   - Target metrics: Recall > 40%, Precision > 60%, F1 > 0.45

5. **Iterate**:
   - Review remaining errors
   - Continue refining semantic anchors and filters
   - Consider human-in-the-loop for high-uncertainty cases

---

## Conclusion

The current NLU system demonstrates a **conservative approach** with low recall but moderate precision. The primary issue is **missing most actual implementations** (80% miss rate), which significantly limits the system's utility for automated dataset population.

Addressing recall through expanded semantic anchors and adjusted thresholds should be the top priority, followed by precision improvements through better quality filters. With these improvements, the system could become a valuable tool for semi-automated technique detection, requiring human review primarily for UNCLEAR cases rather than comprehensive manual labeling.

**Current State**: Semi-automated detection with high manual review burden
**Target State**: Automated detection with human review for edge cases (PARTIAL/UNCLEAR)
**Path Forward**: Improve recall first, then precision, then iterate

---

## Files Generated

- [nlu_vs_groundtruth_comparison.json](nlu_vs_groundtruth_comparison.json) - Detailed comparison results
- [labeling_ground_truth.xlsx](../data/flat_text/labeling_ground_truth.xlsx) - Ground truth labels with excerpts
