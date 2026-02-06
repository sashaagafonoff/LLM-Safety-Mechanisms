#!/usr/bin/env python3
"""
Compare NLU automated predictions against ground truth labels.
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent.parent
SPREADSHEET_PATH = BASE_DIR / "data" / "flat_text" / "labeling_ground_truth.xlsx"
MODEL_TECHNIQUE_MAP_PATH = BASE_DIR / "data" / "model_technique_map.json"

def load_ground_truth():
    """Load ground truth labels from spreadsheet."""
    df = pd.read_excel(SPREADSHEET_PATH, sheet_name="Ground Truth")

    # Create a dictionary for quick lookup: (source_id, technique_id) -> label
    ground_truth = {}
    for _, row in df.iterrows():
        source_id = row['Evidence Source ID']
        technique_id = row['Technique ID']
        present = row['Present?']
        confidence = row['Confidence']

        # Skip rows with missing technique IDs
        if pd.isna(technique_id):
            continue

        key = (source_id, technique_id)
        ground_truth[key] = {
            'present': present,
            'confidence': confidence,
            'technique_name': row['Technique Name'],
            'source_title': row['Evidence Source Title']
        }

    return ground_truth

def load_nlu_predictions():
    """Load NLU predictions from model_technique_map.json."""
    with open(MODEL_TECHNIQUE_MAP_PATH, 'r', encoding='utf-8') as f:
        model_map = json.load(f)

    # Create a dictionary: (source_id, technique_id) -> confidence
    predictions = {}
    for source_id, techniques in model_map.items():
        for tech in techniques:
            technique_id = tech['techniqueId']
            confidence = tech.get('confidence', 'Unknown')
            key = (source_id, technique_id)
            predictions[key] = {
                'confidence': confidence,
                'evidence_count': len(tech.get('evidence', []))
            }

    return predictions

def classify_for_metrics(present_label):
    """
    Convert ground truth labels to binary classification.
    YES, PARTIAL -> Positive (technique present)
    NO -> Negative (technique not present)
    UNCLEAR -> Negative (conservative approach)
    """
    if present_label in ['YES', 'PARTIAL']:
        return 'positive'
    else:  # NO or UNCLEAR
        return 'negative'

def calculate_metrics(ground_truth, predictions):
    """Calculate precision, recall, F1, accuracy."""

    # Get all keys from both ground truth and predictions
    all_keys = set(ground_truth.keys()) | set(predictions.keys())

    tp = 0  # True Positives
    fp = 0  # False Positives
    tn = 0  # True Negatives
    fn = 0  # False Negatives

    details = {
        'tp': [],
        'fp': [],
        'fn': [],
        'tn': []
    }

    for key in all_keys:
        source_id, technique_id = key

        # Get ground truth
        gt = ground_truth.get(key)
        if gt:
            gt_class = classify_for_metrics(gt['present'])
            gt_label = gt['present']
        else:
            # Not in ground truth, skip
            continue

        # Get prediction
        pred = predictions.get(key)
        pred_class = 'positive' if pred else 'negative'

        # Compare
        if gt_class == 'positive' and pred_class == 'positive':
            tp += 1
            details['tp'].append({
                'source': source_id,
                'technique': technique_id,
                'gt_label': gt_label,
                'nlu_confidence': pred['confidence'] if pred else None
            })
        elif gt_class == 'negative' and pred_class == 'positive':
            fp += 1
            details['fp'].append({
                'source': source_id,
                'technique': technique_id,
                'gt_label': gt_label,
                'nlu_confidence': pred['confidence'] if pred else None
            })
        elif gt_class == 'positive' and pred_class == 'negative':
            fn += 1
            details['fn'].append({
                'source': source_id,
                'technique': technique_id,
                'gt_label': gt_label
            })
        else:  # gt_class == 'negative' and pred_class == 'negative'
            tn += 1
            details['tn'].append({
                'source': source_id,
                'technique': technique_id,
                'gt_label': gt_label
            })

    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0

    return {
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'accuracy': accuracy,
        'details': details
    }

def analyze_by_label_type(ground_truth, predictions):
    """Analyze NLU performance for each ground truth label type."""
    label_stats = defaultdict(lambda: {'total': 0, 'detected': 0})

    for key, gt in ground_truth.items():
        label = gt['present']
        label_stats[label]['total'] += 1

        if key in predictions:
            label_stats[label]['detected'] += 1

    return dict(label_stats)

def main():
    print("Loading data...")
    ground_truth = load_ground_truth()
    predictions = load_nlu_predictions()

    print(f"\nGround truth entries: {len(ground_truth)}")
    print(f"NLU predictions: {len(predictions)}")

    # Calculate metrics
    print("\n" + "="*60)
    print("PERFORMANCE METRICS")
    print("="*60)

    metrics = calculate_metrics(ground_truth, predictions)

    print(f"\nConfusion Matrix:")
    print(f"  True Positives (TP):  {metrics['tp']:4d}  (Correctly detected)")
    print(f"  False Positives (FP): {metrics['fp']:4d}  (Incorrectly detected)")
    print(f"  True Negatives (TN):  {metrics['tn']:4d}  (Correctly not detected)")
    print(f"  False Negatives (FN): {metrics['fn']:4d}  (Missed)")

    print(f"\nMetrics:")
    print(f"  Precision: {metrics['precision']:.3f}  (Of all detections, how many were correct?)")
    print(f"  Recall:    {metrics['recall']:.3f}  (Of all actual positives, how many were detected?)")
    print(f"  F1 Score:  {metrics['f1']:.3f}  (Harmonic mean of precision and recall)")
    print(f"  Accuracy:  {metrics['accuracy']:.3f}  (Overall correctness)")

    # Analyze by label type
    print("\n" + "="*60)
    print("DETECTION RATE BY GROUND TRUTH LABEL")
    print("="*60)

    label_stats = analyze_by_label_type(ground_truth, predictions)
    for label, stats in sorted(label_stats.items()):
        detection_rate = stats['detected'] / stats['total'] if stats['total'] > 0 else 0
        print(f"  {label:10s}: {stats['detected']:3d}/{stats['total']:3d} detected ({detection_rate:.1%})")

    # Sample false positives
    print("\n" + "="*60)
    print("SAMPLE FALSE POSITIVES (NLU detected, but not in ground truth)")
    print("="*60)

    for i, fp in enumerate(metrics['details']['fp'][:10]):
        print(f"\n{i+1}. {fp['source']} + {fp['technique']}")
        print(f"   Ground truth: {fp['gt_label']} | NLU confidence: {fp['nlu_confidence']}")

    if len(metrics['details']['fp']) > 10:
        print(f"\n... and {len(metrics['details']['fp']) - 10} more false positives")

    # Sample false negatives
    print("\n" + "="*60)
    print("SAMPLE FALSE NEGATIVES (In ground truth, but NLU missed)")
    print("="*60)

    for i, fn in enumerate(metrics['details']['fn'][:10]):
        print(f"\n{i+1}. {fn['source']} + {fn['technique']}")
        print(f"   Ground truth: {fn['gt_label']}")

    if len(metrics['details']['fn']) > 10:
        print(f"\n... and {len(metrics['details']['fn']) - 10} more false negatives")

    # Export detailed results
    print("\n" + "="*60)
    print("EXPORTING DETAILED RESULTS")
    print("="*60)

    output_file = BASE_DIR / "reports" / "nlu_vs_groundtruth_comparison.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': {
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1': metrics['f1'],
                'accuracy': metrics['accuracy'],
                'confusion_matrix': {
                    'tp': metrics['tp'],
                    'fp': metrics['fp'],
                    'tn': metrics['tn'],
                    'fn': metrics['fn']
                }
            },
            'label_statistics': label_stats,
            'false_positives': metrics['details']['fp'],
            'false_negatives': metrics['details']['fn']
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
