#!/usr/bin/env python3
"""
Simple script to merge individual raw_result.json files and generate a complete report.
"""

import json
from pathlib import Path
import sys
import os

# Add parent directory to path to import Report
sys.path.insert(0, str(Path(__file__).parent))
from src.report import Report


def merge_raw_results(base_dir):
    """Collect all individual raw_result.json files and create a consolidated report."""
    base_path = Path(base_dir)
    
    # Collect all problem results into a dictionary (raw_logs format)
    raw_logs = {}
    problem_folders = sorted([d for d in base_path.iterdir() 
                             if d.is_dir() and d.name.startswith('work_auto_cvdp')])
    
    print(f"Found {len(problem_folders)} problem folders")
    
    for folder in problem_folders:
        raw_result_path = folder / 'raw_result.json'
        if raw_result_path.exists():
            with open(raw_result_path, 'r') as f:
                result = json.load(f)
                # Merge the dictionary (each file has one problem ID as key)
                raw_logs.update(result)
                # Get the problem ID from the result
                problem_id = list(result.keys())[0]
                print(f"  ✓ {problem_id}")
        else:
            print(f"  ✗ Missing: {folder.name}")
    
    # Write consolidated raw_result.json
    output_path = base_path / 'raw_result.json'
    with open(output_path, 'w') as f:
        json.dump(raw_logs, f, indent=2)
    
    print(f"\n✓ Created {output_path} with {len(raw_logs)} problems")
    
    # Now generate the report using the Report class
    print("\nGenerating report...")
    report = Report(raw_logs=raw_logs, prefix=str(base_path))
    report.report_categories()
    
    print(f"✓ Created {base_path}/report.json")
    print(f"✓ Created {base_path}/report.txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python merge_raw_results.py <directory>")
        sys.exit(1)
    
    merge_raw_results(sys.argv[1])
