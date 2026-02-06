#!/usr/bin/env python3
"""
Detailed analysis of NLU errors to identify patterns and improvement opportunities.
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict, Counter

# Paths
BASE_DIR = Path(__file__).parent.parent
SPREADSHEET_PATH = BASE_DIR / "data" / "flat_text" / "labeling_ground_truth.xlsx"
MODEL_TECHNIQUE_MAP_PATH = BASE_DIR / "data" / "model_technique_map.json"
TECHNIQUES_PATH = BASE_DIR / "data" / "techniques.json"
COMPARISON_RESULTS = BASE_DIR / "reports" / "nlu_vs_groundtruth_comparison.json"

def load_all_data():
    """Load all necessary data."""
    # Ground truth
    df = pd.read_excel(SPREADSHEET_PATH, sheet_name="Ground Truth")

    # Model technique map
    with open(MODEL_TECHNIQUE_MAP_PATH, 'r', encoding='utf-8') as f:
        model_map = json.load(f)

    # Techniques
    with open(TECHNIQUES_PATH, 'r', encoding='utf-8') as f:
        techniques = json.load(f)
    tech_dict = {t['id']: t for t in techniques}

    # Comparison results
    with open(COMPARISON_RESULTS, 'r', encoding='utf-8') as f:
        comparison = json.load(f)

    return df, model_map, tech_dict, comparison

def analyze_false_negatives(fn_list, df, tech_dict):
    """Analyze false negative patterns."""
    print("\n" + "="*70)
    print("FALSE NEGATIVE ANALYSIS (Techniques the NLU system missed)")
    print("="*70)

    # Count by technique
    technique_counts = Counter(fn['technique'] for fn in fn_list)
    print("\nMost commonly missed techniques:")
    for tech_id, count in technique_counts.most_common(15):
        tech_name = tech_dict.get(tech_id, {}).get('name', tech_id)
        print(f"  {count:2d}x - {tech_name}")

    # Count by source
    source_counts = Counter(fn['source'] for fn in fn_list)
    print("\nSources with most missed techniques:")
    for source_id, count in source_counts.most_common(10):
        # Get source title
        source_title = df[df['Evidence Source ID'] == source_id]['Evidence Source Title'].iloc[0] if len(df[df['Evidence Source ID'] == source_id]) > 0 else source_id
        print(f"  {count:2d}x - {source_id} ({source_title})")

    # Analyze by ground truth label
    label_counts = Counter(fn['gt_label'] for fn in fn_list)
    print("\nMissed by ground truth label:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label:10s}: {count:2d} missed")

def analyze_false_positives(fp_list, df, tech_dict, model_map):
    """Analyze false positive patterns."""
    print("\n" + "="*70)
    print("FALSE POSITIVE ANALYSIS (Incorrect NLU detections)")
    print("="*70)

    # Count by technique
    technique_counts = Counter(fp['technique'] for fp in fp_list)
    print("\nMost commonly over-detected techniques:")
    for tech_id, count in technique_counts.most_common(15):
        tech_name = tech_dict.get(tech_id, {}).get('name', tech_id)
        print(f"  {count:2d}x - {tech_name}")

    # Count by source
    source_counts = Counter(fp['source'] for fp in fp_list)
    print("\nSources with most false positives:")
    for source_id, count in source_counts.most_common(10):
        source_title = df[df['Evidence Source ID'] == source_id]['Evidence Source Title'].iloc[0] if len(df[df['Evidence Source ID'] == source_id]) > 0 else source_id
        print(f"  {count:2d}x - {source_id} ({source_title})")

    # Analyze ground truth labels for false positives
    label_counts = Counter(fp['gt_label'] for fp in fp_list)
    print("\nFalse positives by ground truth label:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label:10s}: {count:2d} false positives")

    # Look at a few examples with evidence
    print("\n" + "="*70)
    print("SAMPLE FALSE POSITIVE EVIDENCE EXCERPTS")
    print("="*70)

    for i, fp in enumerate(fp_list[:3]):
        source_id = fp['source']
        tech_id = fp['technique']
        tech_name = tech_dict.get(tech_id, {}).get('name', tech_id)

        print(f"\n{i+1}. {source_id} + {tech_name}")
        print(f"   Ground truth: {fp['gt_label']} | NLU confidence: {fp['nlu_confidence']}")

        # Get evidence from model_map
        if source_id in model_map:
            for detection in model_map[source_id]:
                if detection['techniqueId'] == tech_id:
                    evidence = detection.get('evidence', [])
                    if evidence:
                        print(f"   NLU evidence excerpt:")
                        excerpt = evidence[0][:200] + "..." if len(evidence[0]) > 200 else evidence[0]
                        print(f"   '{excerpt}'")
                    break

def analyze_true_positives(tp_list, tech_dict):
    """Analyze what the NLU system gets right."""
    print("\n" + "="*70)
    print("TRUE POSITIVE ANALYSIS (What NLU gets right)")
    print("="*70)

    # Count by technique
    technique_counts = Counter(tp['technique'] for tp in tp_list)
    print("\nTechniques successfully detected:")
    for tech_id, count in technique_counts.most_common():
        tech_name = tech_dict.get(tech_id, {}).get('name', tech_id)
        print(f"  {count:2d}x - {tech_name}")

    # Breakdown by ground truth label
    label_counts = Counter(tp['gt_label'] for tp in tp_list)
    print("\nTrue positives by ground truth label:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label:10s}: {count:2d} correctly detected")

def analyze_threshold_sensitivity(df, model_map):
    """Analyze how confidence thresholds affect performance."""
    print("\n" + "="*70)
    print("THRESHOLD SENSITIVITY ANALYSIS")
    print("="*70)

    # Create lookup for all predictions with confidence
    predictions = {}
    for source_id, techniques in model_map.items():
        for tech in techniques:
            key = (source_id, tech['techniqueId'])
            predictions[key] = tech.get('confidence', 'Unknown')

    # Analyze for different confidence filters
    for min_confidence in ['High', 'Medium']:
        # Filter predictions
        if min_confidence == 'High':
            filtered_preds = {k: v for k, v in predictions.items() if v == 'High'}
        else:  # Medium or higher
            filtered_preds = predictions  # All predictions

        # Calculate metrics
        tp = fp = tn = fn = 0
        for _, row in df.iterrows():
            if pd.isna(row['Technique ID']):
                continue

            key = (row['Evidence Source ID'], row['Technique ID'])
            gt_label = row['Present?']

            # Ground truth classification
            gt_positive = gt_label in ['YES', 'PARTIAL']

            # Prediction
            pred_positive = key in filtered_preds

            if gt_positive and pred_positive:
                tp += 1
            elif not gt_positive and pred_positive:
                fp += 1
            elif gt_positive and not pred_positive:
                fn += 1
            else:
                tn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        print(f"\nMin confidence: {min_confidence}")
        print(f"  Predictions: {len(filtered_preds)}")
        print(f"  Precision: {precision:.3f} | Recall: {recall:.3f} | F1: {f1:.3f}")

def generate_recommendations():
    """Generate recommendations for improving NLU system."""
    print("\n" + "="*70)
    print("RECOMMENDATIONS FOR IMPROVING NLU SYSTEM")
    print("="*70)

    recommendations = [
        {
            "issue": "Low Recall (20.4%)",
            "description": "The system misses most actual implementations (82 false negatives)",
            "recommendations": [
                "Expand semantic anchors in techniques.json with more varied terminology",
                "Lower the entailment threshold for the cross-encoder verification stage",
                "Add more implementation-related keywords (e.g., 'incorporate', 'utilize', 'leverage')",
                "Consider using a more sensitive retrieval model or adjust retrieval thresholds"
            ]
        },
        {
            "issue": "Moderate Precision (48.8%)",
            "description": "About half of detections are false positives (22 incorrect detections)",
            "recommendations": [
                "Strengthen quality filters to avoid glossary/definition mentions",
                "Improve context analysis to distinguish 'discussing' vs 'implementing'",
                "Add more exclusion patterns for non-implementation contexts",
                "Consider requiring multiple strong semantic matches instead of single weak matches"
            ]
        },
        {
            "issue": "Poor YES detection (26.7%)",
            "description": "Missing 22 out of 30 clear implementations",
            "recommendations": [
                "Review semantic anchors for the most commonly missed techniques",
                "Add technique-specific implementation phrases to nlu_profiles",
                "Consider manual review of high-value YES cases to identify missing patterns",
                "Test with different embedding models that may better capture implementation language"
            ]
        },
        {
            "issue": "High NO false positives (5.1%)",
            "description": "Incorrectly detecting 17 techniques marked as NO",
            "recommendations": [
                "Strengthen filters for 'future work', 'recommendations', 'could use' patterns",
                "Add negative examples to help distinguish discussion from implementation",
                "Review false positive examples to identify common misleading patterns",
                "Improve handling of comparative/contrastive mentions (e.g., 'unlike X which uses Y')"
            ]
        }
    ]

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['issue']}")
        print(f"   Problem: {rec['description']}")
        print(f"   Recommendations:")
        for suggestion in rec['recommendations']:
            print(f"   - {suggestion}")

def main():
    print("Loading data...")
    df, model_map, tech_dict, comparison = load_all_data()

    # Analyze false negatives
    analyze_false_negatives(comparison['false_negatives'], df, tech_dict)

    # Analyze false positives
    analyze_false_positives(comparison['false_positives'], df, tech_dict, model_map)

    # Analyze true positives
    analyze_true_positives(
        [item for item in comparison.get('true_positives', [])],
        tech_dict
    )

    # Need to reconstruct true positives since they weren't exported
    # Re-calculate for analysis
    all_tp = []
    for source_id, techniques in model_map.items():
        for tech in techniques:
            tech_id = tech['techniqueId']
            # Find in ground truth
            gt_row = df[(df['Evidence Source ID'] == source_id) & (df['Technique ID'] == tech_id)]
            if not gt_row.empty:
                gt_label = gt_row.iloc[0]['Present?']
                if gt_label in ['YES', 'PARTIAL']:
                    all_tp.append({
                        'technique': tech_id,
                        'gt_label': gt_label
                    })

    if all_tp:
        analyze_true_positives(all_tp, tech_dict)

    # Threshold sensitivity
    analyze_threshold_sensitivity(df, model_map)

    # Generate recommendations
    generate_recommendations()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
