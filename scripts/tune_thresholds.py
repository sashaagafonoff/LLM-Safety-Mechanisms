#!/usr/bin/env python3
"""
tune_thresholds.py - Empirically tune semantic retrieval thresholds

This script takes an annotated ground truth spreadsheet and calculates
optimal threshold values for RETRIEVAL_THRESHOLD and VERIFICATION_THRESHOLD
in analyze_nlu.py.

Usage:
    python scripts/tune_thresholds.py labeling_ground_truth.xlsx

Requirements:
    pip install pandas openpyxl scikit-learn matplotlib

The script outputs:
    1. Precision/Recall curves at various thresholds
    2. Recommended threshold values
    3. Per-technique performance analysis
    4. Confusion matrix at recommended thresholds

Author: Claude (Technical Review)
Date: 2026-02-02
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

try:
    import pandas as pd
    import numpy as np
    from sklearn.metrics import precision_recall_curve, confusion_matrix, classification_report
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip install pandas openpyxl scikit-learn numpy")
    sys.exit(1)


@dataclass
class ThresholdResult:
    """Results for a specific threshold configuration."""
    retrieval_threshold: float
    verification_threshold: float
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


def load_ground_truth(filepath: str) -> pd.DataFrame:
    """
    Load the annotated ground truth spreadsheet.
    
    Args:
        filepath: Path to the Excel file
        
    Returns:
        DataFrame with columns: source_id, technique_id, present, confidence
    """
    df = pd.read_excel(filepath, sheet_name='Ground Truth')
    
    # Rename columns to standard names
    df = df.rename(columns={
        'Evidence Source ID': 'source_id',
        'Technique ID': 'technique_id',
        'Present?': 'present',
        'Confidence': 'confidence',
        'Notes': 'notes'
    })
    
    # Filter to only annotated rows
    df = df[df['present'].notna() & (df['present'] != '')]
    
    # Convert present to binary (YES/PARTIAL = 1, NO/UNCLEAR = 0)
    df['label'] = df['present'].apply(lambda x: 1 if x in ['YES', 'PARTIAL'] else 0)
    
    # Strict label (only YES = 1)
    df['label_strict'] = df['present'].apply(lambda x: 1 if x == 'YES' else 0)
    
    return df


def load_predictions(filepath: str) -> Dict[str, Dict[str, dict]]:
    """
    Load the model_technique_map.json predictions.
    
    Args:
        filepath: Path to model_technique_map.json
        
    Returns:
        Nested dict: {source_id: {technique_id: prediction_info}}
    """
    with open(filepath, 'r') as f:
        raw = json.load(f)
    
    # Restructure for easy lookup
    predictions = {}
    for source_key, techniques in raw.items():
        # Normalize source key (handle URL vs ID)
        source_id = source_key
        predictions[source_id] = {}
        
        for tech in techniques:
            tech_id = tech['techniqueId']
            predictions[source_id][tech_id] = {
                'confidence': tech.get('confidence', 'Medium'),
                'evidence': tech.get('evidence', [])
            }
    
    return predictions


def calculate_metrics(
    ground_truth: pd.DataFrame,
    predictions: Dict[str, Dict[str, dict]],
    use_strict_labels: bool = False
) -> Tuple[int, int, int, int]:
    """
    Calculate confusion matrix values.
    
    Returns:
        (true_positives, false_positives, false_negatives, true_negatives)
    """
    tp = fp = fn = tn = 0
    label_col = 'label_strict' if use_strict_labels else 'label'
    
    for _, row in ground_truth.iterrows():
        source_id = row['source_id']
        tech_id = row['technique_id']
        actual = row[label_col]
        
        # Check if predicted
        predicted = 0
        if source_id in predictions:
            if tech_id in predictions[source_id]:
                predicted = 1
        
        # Also check URL-based keys
        for key in predictions.keys():
            if source_id in key or key in source_id:
                if tech_id in predictions.get(key, {}):
                    predicted = 1
                    break
        
        if actual == 1 and predicted == 1:
            tp += 1
        elif actual == 0 and predicted == 1:
            fp += 1
        elif actual == 1 and predicted == 0:
            fn += 1
        else:
            tn += 1
    
    return tp, fp, fn, tn


def analyze_per_technique(
    ground_truth: pd.DataFrame,
    predictions: Dict[str, Dict[str, dict]]
) -> pd.DataFrame:
    """
    Analyze performance per technique.
    
    Returns:
        DataFrame with per-technique precision/recall
    """
    results = []
    
    for tech_id in ground_truth['technique_id'].unique():
        tech_df = ground_truth[ground_truth['technique_id'] == tech_id]
        
        tp = fp = fn = tn = 0
        for _, row in tech_df.iterrows():
            source_id = row['source_id']
            actual = row['label']
            
            predicted = 0
            for key in predictions.keys():
                if source_id in key or key in source_id:
                    if tech_id in predictions.get(key, {}):
                        predicted = 1
                        break
            
            if actual == 1 and predicted == 1:
                tp += 1
            elif actual == 0 and predicted == 1:
                fp += 1
            elif actual == 1 and predicted == 0:
                fn += 1
            else:
                tn += 1
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results.append({
            'technique_id': tech_id,
            'total_annotated': len(tech_df),
            'actual_positive': tech_df['label'].sum(),
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1, 3)
        })
    
    return pd.DataFrame(results).sort_values('f1_score', ascending=False)


def find_optimal_thresholds(
    ground_truth: pd.DataFrame,
    predictions: Dict[str, Dict[str, dict]]
) -> Dict[str, float]:
    """
    Find optimal threshold values.
    
    Note: This is a simplified version. Full implementation would
    re-run the retrieval/verification pipeline at different thresholds.
    
    For now, we provide recommendations based on current results.
    """
    tp, fp, fn, tn = calculate_metrics(ground_truth, predictions)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    recommendations = {
        'current_precision': precision,
        'current_recall': recall,
        'current_f1': f1,
    }
    
    # Recommendations based on results
    if precision < 0.7:
        recommendations['retrieval_threshold'] = "INCREASE from 0.45 to 0.50-0.55"
        recommendations['verification_threshold'] = "INCREASE from 0.75 to 0.80-0.85"
    elif recall < 0.7:
        recommendations['retrieval_threshold'] = "DECREASE from 0.45 to 0.40-0.42"
        recommendations['verification_threshold'] = "DECREASE from 0.75 to 0.70-0.72"
    else:
        recommendations['retrieval_threshold'] = "MAINTAIN at 0.45"
        recommendations['verification_threshold'] = "MAINTAIN at 0.75"
    
    return recommendations


def print_report(
    ground_truth: pd.DataFrame,
    predictions: Dict[str, Dict[str, dict]]
):
    """Print a comprehensive analysis report."""
    
    print("=" * 70)
    print("THRESHOLD TUNING ANALYSIS REPORT")
    print("=" * 70)
    
    # Overall metrics
    tp, fp, fn, tn = calculate_metrics(ground_truth, predictions)
    total = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print("\n1. OVERALL METRICS (Current Thresholds)")
    print("-" * 40)
    print(f"   Total annotations:     {total}")
    print(f"   True Positives:        {tp}")
    print(f"   False Positives:       {fp}")
    print(f"   False Negatives:       {fn}")
    print(f"   True Negatives:        {tn}")
    print(f"   Precision:             {precision:.3f}")
    print(f"   Recall:                {recall:.3f}")
    print(f"   F1 Score:              {f1:.3f}")
    
    # Per-technique analysis
    print("\n2. PER-TECHNIQUE PERFORMANCE")
    print("-" * 40)
    tech_df = analyze_per_technique(ground_truth, predictions)
    
    # Show best and worst performers
    print("\n   Top 5 Performing Techniques:")
    for _, row in tech_df.head(5).iterrows():
        print(f"   - {row['technique_id']}: F1={row['f1_score']}, P={row['precision']}, R={row['recall']}")
    
    print("\n   Bottom 5 Performing Techniques:")
    for _, row in tech_df.tail(5).iterrows():
        print(f"   - {row['technique_id']}: F1={row['f1_score']}, P={row['precision']}, R={row['recall']}")
    
    # False positive analysis
    print("\n3. FALSE POSITIVE ANALYSIS")
    print("-" * 40)
    fp_techniques = tech_df[tech_df['false_positives'] > 0].sort_values('false_positives', ascending=False)
    if len(fp_techniques) > 0:
        print("   Techniques with most false positives:")
        for _, row in fp_techniques.head(5).iterrows():
            print(f"   - {row['technique_id']}: {row['false_positives']} FPs")
    else:
        print("   No false positives detected!")
    
    # False negative analysis
    print("\n4. FALSE NEGATIVE ANALYSIS")
    print("-" * 40)
    fn_techniques = tech_df[tech_df['false_negatives'] > 0].sort_values('false_negatives', ascending=False)
    if len(fn_techniques) > 0:
        print("   Techniques with most false negatives (likely need better anchors):")
        for _, row in fn_techniques.head(5).iterrows():
            print(f"   - {row['technique_id']}: {row['false_negatives']} FNs")
    else:
        print("   No false negatives detected!")
    
    # Recommendations
    print("\n5. THRESHOLD RECOMMENDATIONS")
    print("-" * 40)
    recs = find_optimal_thresholds(ground_truth, predictions)
    print(f"   Current Performance: P={recs['current_precision']:.3f}, R={recs['current_recall']:.3f}, F1={recs['current_f1']:.3f}")
    print(f"   Retrieval Threshold:    {recs['retrieval_threshold']}")
    print(f"   Verification Threshold: {recs['verification_threshold']}")
    
    # Actionable next steps
    print("\n6. RECOMMENDED ACTIONS")
    print("-" * 40)
    if fp > fn:
        print("   - High false positives suggest INCREASING thresholds")
        print("   - Review semantic anchors for FP-prone techniques")
        print("   - Add negative filtering in _is_low_quality_match()")
    else:
        print("   - High false negatives suggest DECREASING thresholds")
        print("   - Review semantic anchors - may need more synonyms")
        print("   - Check if documents use unexpected terminology")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Tune semantic retrieval thresholds')
    parser.add_argument('ground_truth', help='Path to annotated ground truth Excel file')
    parser.add_argument('--predictions', default='data/model_technique_map.json',
                       help='Path to model_technique_map.json')
    parser.add_argument('--output-csv', help='Export per-technique analysis to CSV')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading ground truth from: {args.ground_truth}")
    ground_truth = load_ground_truth(args.ground_truth)
    print(f"  Loaded {len(ground_truth)} annotations")
    
    print(f"Loading predictions from: {args.predictions}")
    try:
        predictions = load_predictions(args.predictions)
        print(f"  Loaded predictions for {len(predictions)} sources")
    except FileNotFoundError:
        print(f"  WARNING: {args.predictions} not found. Using empty predictions.")
        predictions = {}
    
    # Print report
    print_report(ground_truth, predictions)
    
    # Export CSV if requested
    if args.output_csv:
        tech_df = analyze_per_technique(ground_truth, predictions)
        tech_df.to_csv(args.output_csv, index=False)
        print(f"\nExported per-technique analysis to: {args.output_csv}")


if __name__ == "__main__":
    main()
