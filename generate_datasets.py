#!/usr/bin/env python3
"""
Script to generate legal datasets for judgment summarization.
Generates IPC, CrPC, Evidence Act, Constitution, and Sample Judgments datasets.
"""

import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Import dataset generators
import sys
from pathlib import Path

# Add datasets directory to path
sys.path.insert(0, str(Path(__file__).parent / "datasets"))

from ipc_generator import generate_ipc_dataset
from crpc_generator import generate_crpc_dataset
from evidence_generator import generate_evidence_dataset
from constitution_generator import generate_constitution_dataset
from judgments_generator import generate_judgments_dataset


def main():
    parser = argparse.ArgumentParser(description='Generate legal datasets for judgment summarization')
    parser.add_argument('--dataset', type=str, choices=['ipc', 'crpc', 'evidence', 'constitution', 'judgments', 'all'],
                       default='all', help='Dataset to generate')
    parser.add_argument('--output-dir', type=str, default='datasets', help='Output directory')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    datasets_to_generate = []
    if args.dataset == 'all':
        datasets_to_generate = ['ipc', 'crpc', 'evidence', 'constitution', 'judgments']
    else:
        datasets_to_generate = [args.dataset]
    
    print(f"Generating datasets: {', '.join(datasets_to_generate)}")
    
    for dataset_name in datasets_to_generate:
        print(f"\n{'='*60}")
        print(f"Generating {dataset_name.upper()} dataset...")
        print(f"{'='*60}")
        
        try:
            if dataset_name == 'ipc':
                generate_ipc_dataset(args.output_dir)
            elif dataset_name == 'crpc':
                generate_crpc_dataset(args.output_dir)
            elif dataset_name == 'evidence':
                generate_evidence_dataset(args.output_dir)
            elif dataset_name == 'constitution':
                generate_constitution_dataset(args.output_dir)
            elif dataset_name == 'judgments':
                generate_judgments_dataset(args.output_dir)
            
            print(f"[SUCCESS] {dataset_name.upper()} dataset generated successfully!")
        except Exception as e:
            print(f"[ERROR] Error generating {dataset_name.upper()} dataset: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Dataset generation complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
