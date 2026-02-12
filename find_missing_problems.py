#!/usr/bin/env python3
"""
Script to find missing problems in final_llm_nonagentic directory
compared to the dataset.jsonl file.
"""

import json
import os
from pathlib import Path

def get_dataset_problem_ids(dataset_path):
    """Extract all problem IDs from the dataset JSONL file."""
    problem_ids = []
    with open(dataset_path, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                problem_ids.append(data['id'])
    return problem_ids

def get_processed_problem_ids(results_dir):
    """Extract all problem IDs from folder names in results directory."""
    processed_ids = []
    if not os.path.exists(results_dir):
        print(f"Directory {results_dir} does not exist!")
        return processed_ids
    
    for folder in os.listdir(results_dir):
        folder_path = os.path.join(results_dir, folder)
        if os.path.isdir(folder_path):
            # Extract problem ID from folder name
            # Folder format: work_auto_cvdp_copilot_<problem_id>
            if folder.startswith('work_auto_cvdp_copilot_'):
                problem_id = folder.replace('work_auto_cvdp_copilot_', '')
                # Reconstruct the ID with the prefix
                problem_id = f'cvdp_copilot_{problem_id}'
                processed_ids.append(problem_id)
    
    return processed_ids

def main():
    dataset_file = 'dataset/cvdp_v1.0.2_nonagentic_code_generation_no_commercial.jsonl'
    results_dir = 'final_llm_nonagentic'
    
    print("Reading dataset...")
    dataset_ids = get_dataset_problem_ids(dataset_file)
    print(f"Total problems in dataset: {len(dataset_ids)}")
    
    print("\nScanning results directory...")
    processed_ids = get_processed_problem_ids(results_dir)
    print(f"Total processed problems: {len(processed_ids)}")
    
    # Find missing problems
    dataset_set = set(dataset_ids)
    processed_set = set(processed_ids)
    
    missing = dataset_set - processed_set
    extra = processed_set - dataset_set
    
    print(f"\n{'='*60}")
    print(f"Missing problems: {len(missing)}")
    print(f"{'='*60}")
    
    if missing:
        for problem_id in sorted(missing):
            print(f"  - {problem_id}")
    else:
        print("  None")
    
    if extra:
        print(f"\n{'='*60}")
        print(f"Extra problems (in results but not in dataset): {len(extra)}")
        print(f"{'='*60}")
        for problem_id in sorted(extra):
            print(f"  - {problem_id}")

if __name__ == '__main__':
    main()
