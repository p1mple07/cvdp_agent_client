#!/usr/bin/env python3

"""
Master script to run benchmark on all problems and create enhanced dataset
Usage: python run_all_problems.py [options]
"""

import sys
import json
import os
import subprocess
import argparse
from pathlib import Path
import time
import shutil


def read_dataset(dataset_file):
    """Read all problems from the dataset JSONL file."""
    problems = []
    if not os.path.exists(dataset_file):
        print(f"Error: Dataset file not found at {dataset_file}")
        sys.exit(1)
    cnt = 0
    with open(dataset_file, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                problems.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {e}")
                continue
    
    return problems


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def check_problem_passed(work_dir, problem_name):
    """Check if a problem passed by reading the report.json file."""
    # Try root-level report.json first (this has the aggregated results)
    root_report_path = os.path.join(work_dir, "report.json")
    problem_report_path = os.path.join(work_dir, problem_name, "report.json")
    
    # Prefer root-level report as it has aggregated test results
    report_path = root_report_path if os.path.exists(root_report_path) else problem_report_path
    
    if not os.path.exists(report_path):
        print(f"Warning: Report file not found at {report_path}")
        return False
    
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Check root-level report format first (most reliable)
        if 'test_details' in report:
            failing_tests = report.get('test_details', {}).get('failing_tests', [])
            passing_tests = report.get('test_details', {}).get('passing_tests', [])
            passed = len(failing_tests) == 0 and len(passing_tests) > 0
        # Check if test passed - looking for pass rate or status
        elif 'pass_rate' in report:
            pass_rate = float(report.get('pass_rate', 0))
            passed = pass_rate >= 100.0
        elif 'status' in report:
            passed = report.get('status') == 'passed'
        elif 'test_pass_rate' in report:
            test_pass_rate = float(report.get('test_pass_rate', 0))
            passed = test_pass_rate >= 100.0
        else:
            # Try to infer from test counts
            total = report.get('total_tests', 0)
            passed_tests = report.get('passed_tests', 0)
            passed = (total > 0 and passed_tests == total)
        
        if passed:
            print(f"✓ Problem PASSED - will skip enhancement")
        else:
            print(f"✗ Problem FAILED - will add to enhanced dataset")
        
        return passed
        
    except Exception as e:
        print(f"Warning: Error reading report: {e}")
        return False


def cleanup_work_directory(work_dir):
    """Delete a work directory to save space."""
    if os.path.exists(work_dir):
        try:
            print(f"Cleaning up work directory: {work_dir}")
            shutil.rmtree(work_dir)
            print(f"✓ Deleted {work_dir}")
            return True
        except Exception as e:
            print(f"Warning: Failed to delete {work_dir}: {e}")
            return False
    return False


def get_next_run_number():
    """Find the next available run number by checking existing run_* directories."""
    run_num = 1
    while os.path.exists(f"run_{run_num}"):
        run_num += 1
    return run_num


def main():
    parser = argparse.ArgumentParser(
        description='Run benchmark on all problems and create enhanced dataset'
    )
    parser.add_argument('-d', '--dataset', 
                        default='dataset/cvdp_v1.0.2_nonagentic_code_generation_no_commercial.jsonl',
                        help='Dataset file to process (default: cvdp_v1.0.2_nonagentic_code_generation_no_commercial.jsonl)')
    parser.add_argument('-m', '--model', 
                        default='gpt-4o',
                        help='Model to use (default: gpt-4o)')
    parser.add_argument('-o', '--output', 
                        default='dataset/temp_dataset.jsonl',
                        help='Output temp dataset file (default: dataset/temp_dataset.jsonl)')
    parser.add_argument('-w', '--work-prefix', 
                        default='work_auto',
                        help='Prefix for work directories (default: work_auto)')
    parser.add_argument('--skip-benchmark', 
                        action='store_true',
                        help='Skip benchmark run, only create enhanced dataset')
    parser.add_argument('--clear-output', 
                        action='store_true',
                        help='Clear output file before starting')
    parser.add_argument('-l', '--limit', 
                        type=int,
                        help='Limit number of problems to process')
    parser.add_argument('--start-from', 
                        type=int, 
                        default=0,
                        help='Start from problem index (0-based)')
    parser.add_argument('--keep-failed', 
                        action='store_true',
                        help='Keep work directories for failed problems (default: delete them)')
    parser.add_argument('--run-dir', 
                        type=str,
                        help='Specify run directory name (default: auto-generate run_N)')
    
    args = parser.parse_args()
    
    # Determine run directory
    if args.run_dir:
        run_dir = args.run_dir
    else:
        run_num = get_next_run_number()
        run_dir = f"run_{run_num}"
    
    # Create run directory
    os.makedirs(run_dir, exist_ok=True)
    
    print("="*80)
    print("MASTER SCRIPT: Run All Problems")
    print("="*80)
    print(f"Run directory: {run_dir}")
    print(f"Dataset: {args.dataset}")
    print(f"Model: {args.model}")
    print(f"Output: {args.output}")
    print(f"Work prefix: {args.work_prefix}")
    print()
    
    # Clear output file if requested
    if args.clear_output and os.path.exists(args.output):
        print(f"Clearing output file: {args.output}")
        os.remove(args.output)
    
    # Read dataset
    print("Reading dataset...")
    problems = read_dataset(args.dataset)
    print(f"Found {len(problems)} problems in dataset")
    
    # Apply start and limit
    if args.start_from > 0:
        problems = problems[args.start_from:]
        print(f"Starting from problem index {args.start_from}")
    
    if args.limit:
        problems = problems[:args.limit]
        print(f"Limited to {args.limit} problems")
    
    print(f"Processing {len(problems)} problems")
    print()
    
    # Track statistics
    stats = {
        'total': len(problems),
        'benchmark_success': 0,
        'benchmark_failed': 0,
        'passed': 0,
        'failed': 0,
        'dataset_created': 0,
        'dataset_failed': 0,
        'skipped': 0,
        'cleaned_up': 0
    }
    
    # Process each problem
    for idx, problem in enumerate(problems, 1):
        problem_id = problem.get('id', 'unknown')
        
        print(f"\n{'#'*80}")
        print(f"# Problem {idx}/{len(problems)}: {problem_id}")
        print(f"{'#'*80}")
        
        # Create work directory name inside run directory
        work_dir = os.path.join(run_dir, f"{args.work_prefix}_{problem_id}")
        
        # Extract problem name (remove last 5 characters for directory name)
        problem_name = problem_id[:-5] if len(problem_id) > 5 else problem_id
        
        # Step 1: Run benchmark (unless skipped)
        if not args.skip_benchmark:
            benchmark_cmd = [
                './run_and_extract_errors.sh',
                problem_id,
                work_dir,
                args.model
            ]
            
            success = run_command(
                benchmark_cmd,
                f"Running benchmark for {problem_id}"
            )
            
            if success:
                stats['benchmark_success'] += 1
                print(f"✓ Benchmark completed for {problem_id}")
            else:
                stats['benchmark_failed'] += 1
                print(f"✗ Benchmark failed for {problem_id}")
                
                # Clean up failed benchmark directory
                if not args.keep_failed:
                    if cleanup_work_directory(work_dir):
                        stats['cleaned_up'] += 1
                
                print("Skipping dataset creation for this problem")
                stats['skipped'] += 1
                continue
        else:
            print(f"Skipping benchmark (--skip-benchmark flag set)")
            # Check if work directory exists
            if not os.path.exists(work_dir):
                print(f"Warning: Work directory {work_dir} does not exist")
                stats['skipped'] += 1
                continue
        
        # Step 1.5: Check if problem passed or failed
        problem_passed = check_problem_passed(work_dir, problem_name)
        
        if problem_passed:
            stats['passed'] += 1
            print(f"Skipping enhancement - problem passed all tests")
            continue
        else:
            stats['failed'] += 1
        
        # Step 2: Create enhanced dataset entry (only for failed problems)
        dataset_cmd = [
            './create_temp_dataset.py',
            problem_id,
            work_dir,
            args.output
        ]
        
        success = run_command(
            dataset_cmd,
            f"Creating enhanced dataset entry for {problem_id}"
        )
        
        if success:
            stats['dataset_created'] += 1
            print(f"✓ Enhanced dataset entry created for {problem_id}")
            
            # Clean up work directory after successful dataset creation (for failed tests)
            if not args.keep_failed:
                if cleanup_work_directory(work_dir):
                    stats['cleaned_up'] += 1
        else:
            stats['dataset_failed'] += 1
            print(f"✗ Failed to create dataset entry for {problem_id}")
        
        # Small delay to avoid overwhelming the system
        time.sleep(1)
    
    # Print final statistics
    print("\n" + "="*80)
    print("FINAL STATISTICS")
    print("="*80)
    print(f"Run directory: {os.path.abspath(run_dir)}")
    print(f"Total problems processed: {stats['total']}")
    print(f"Benchmark runs:")
    print(f"  ✓ Successful: {stats['benchmark_success']}")
    print(f"  ✗ Failed: {stats['benchmark_failed']}")
    print(f"Test results:")
    print(f"  ✓ Passed: {stats['passed']} (skipped enhancement)")
    print(f"  ✗ Failed: {stats['failed']} (added to enhanced dataset)")
    print(f"Dataset entries created:")
    print(f"  ✓ Successful: {stats['dataset_created']}")
    print(f"  ✗ Failed: {stats['dataset_failed']}")
    print(f"Work directories cleaned up: {stats['cleaned_up']}")
    print(f"Skipped: {stats['skipped']}")
    print()
    print(f"Enhanced dataset saved to: {os.path.abspath(args.output)}")
    
    # Count lines in output file
    if os.path.exists(args.output):
        with open(args.output, 'r') as f:
            line_count = sum(1 for _ in f)
        print(f"Total entries in dataset: {line_count}")
    
    print("="*80)
    print("DONE!")
    print("="*80)


if __name__ == "__main__":
    main()
