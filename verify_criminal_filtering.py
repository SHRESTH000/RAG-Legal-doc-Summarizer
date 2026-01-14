#!/usr/bin/env python3
"""
Verification script to analyze and report on filtered criminal cases.
Provides detailed statistics and sample verification.
"""

import os
import json
from pathlib import Path
from collections import defaultdict, Counter
from filter_criminal_cases import extract_text, is_criminal_case

def analyze_criminal_cases(criminal_folder: str, sample_size: int = 20):
    """
    Analyze filtered criminal cases and generate a detailed report.
    
    Args:
        criminal_folder: Path to folder containing filtered criminal cases
        sample_size: Number of sample files to analyze in detail
    """
    criminal_path = Path(criminal_folder)
    
    if not criminal_path.exists():
        print(f"Error: Criminal cases folder '{criminal_folder}' does not exist.")
        return
    
    pdf_files = list(criminal_path.glob("*.pdf"))
    total_criminal = len(pdf_files)
    
    if total_criminal == 0:
        print(f"No PDF files found in '{criminal_folder}'")
        return
    
    print("=" * 70)
    print("CRIMINAL CASES FILTERING - VERIFICATION REPORT")
    print("=" * 70)
    print(f"\nTotal Criminal Cases Found: {total_criminal}")
    print(f"Sample Analysis Size: {min(sample_size, total_criminal)}")
    print("-" * 70)
    
    # Statistics
    confidence_scores = []
    all_indicators = []
    indicator_counts = Counter()
    high_confidence_count = 0
    medium_confidence_count = 0
    low_confidence_count = 0
    
    # Analyze sample files
    sample_files = pdf_files[:sample_size] if len(pdf_files) >= sample_size else pdf_files
    
    print(f"\nAnalyzing {len(sample_files)} sample files for verification...\n")
    
    for i, pdf_file in enumerate(sample_files, 1):
        try:
            text = extract_text(str(pdf_file), max_pages=5)
            is_criminal, confidence, indicators = is_criminal_case(text)
            
            confidence_scores.append(confidence)
            all_indicators.extend(indicators)
            
            for indicator in indicators:
                indicator_counts[indicator] += 1
            
            # Categorize by confidence
            if confidence >= 0.7:
                high_confidence_count += 1
            elif confidence >= 0.5:
                medium_confidence_count += 1
            else:
                low_confidence_count += 1
            
            # Show first few with details
            if i <= 10:
                print(f"[{i:2d}] {pdf_file.name}")
                print(f"     Confidence: {confidence:.2f} ({confidence*100:.0f}%)")
                print(f"     Indicators: {', '.join(indicators[:5])}")
                if len(indicators) > 5:
                    print(f"                ... and {len(indicators)-5} more")
                print()
        
        except Exception as e:
            print(f"Error analyzing {pdf_file.name}: {e}")
    
    # Calculate statistics
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        min_confidence = min(confidence_scores)
        max_confidence = max(confidence_scores)
        
        print("-" * 70)
        print("\nSTATISTICS (from sample analysis):")
        print(f"  Average Confidence Score: {avg_confidence:.2f} ({avg_confidence*100:.0f}%)")
        print(f"  Minimum Confidence: {min_confidence:.2f} ({min_confidence*100:.0f}%)")
        print(f"  Maximum Confidence: {max_confidence:.2f} ({max_confidence*100:.0f}%)")
        print(f"\nConfidence Distribution (sample):")
        print(f"  High Confidence (>=70%): {high_confidence_count} ({high_confidence_count/len(sample_files)*100:.1f}%)")
        print(f"  Medium Confidence (50-69%): {medium_confidence_count} ({medium_confidence_count/len(sample_files)*100:.1f}%)")
        print(f"  Low Confidence (30-49%): {low_confidence_count} ({low_confidence_count/len(sample_files)*100:.1f}%)")
    
    # Top indicators
    print(f"\nTOP DETECTION INDICATORS (from sample):")
    for indicator, count in indicator_counts.most_common(15):
        percentage = (count / len(sample_files)) * 100
        print(f"  {indicator:30s}: {count:3d} files ({percentage:5.1f}%)")
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    
    # Save report to file
    report_data = {
        "total_criminal_cases": total_criminal,
        "sample_size": len(sample_files),
        "average_confidence": avg_confidence if confidence_scores else 0,
        "min_confidence": min_confidence if confidence_scores else 0,
        "max_confidence": max_confidence if confidence_scores else 0,
        "confidence_distribution": {
            "high": high_confidence_count,
            "medium": medium_confidence_count,
            "low": low_confidence_count
        },
        "top_indicators": dict(indicator_counts.most_common(20))
    }
    
    report_file = Path("criminal_filtering_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")


def compare_with_original(original_folder: str, criminal_folder: str):
    """Compare criminal folder with original to show what was filtered."""
    original_path = Path(original_folder)
    criminal_path = Path(criminal_folder)
    
    if not original_path.exists() or not criminal_path.exists():
        print("Error: Both folders must exist for comparison.")
        return
    
    original_files = set(f.name for f in original_path.glob("*.pdf"))
    criminal_files = set(f.name for f in criminal_path.glob("*.pdf"))
    
    total_original = len(original_files)
    total_criminal = len(criminal_files)
    non_criminal = total_original - total_criminal
    
    print("\n" + "=" * 70)
    print("FILTERING SUMMARY")
    print("=" * 70)
    print(f"Original Folder: {original_folder}")
    print(f"  Total PDFs: {total_original}")
    print(f"\nCriminal Cases Folder: {criminal_folder}")
    print(f"  Criminal Cases: {total_criminal} ({total_criminal/total_original*100:.1f}%)")
    print(f"  Non-Criminal Cases: {non_criminal} ({non_criminal/total_original*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    CRIMINAL_FOLDER = "criminal_2019"
    ORIGINAL_FOLDER = "judgments_2019"
    SAMPLE_SIZE = 30  # Analyze 30 samples for detailed report
    
    # Compare folders
    compare_with_original(ORIGINAL_FOLDER, CRIMINAL_FOLDER)
    
    # Detailed analysis
    analyze_criminal_cases(CRIMINAL_FOLDER, sample_size=SAMPLE_SIZE)
