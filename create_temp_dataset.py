#!/usr/bin/env python3

"""
Script to create a temporary dataset with a single problem, enhanced with error and code
Usage: python create_temp_dataset.py <problem_id> [work_dir] [output_file]
Example: python create_temp_dataset.py cvdp_copilot_64b66b_decoder_0001 work_testing_2
"""

import sys
import json
import os
from pathlib import Path
import argparse


def find_problem_in_dataset(dataset_file, problem_id):
    """Find a specific problem in the dataset JSONL file."""
    if not os.path.exists(dataset_file):
        print(f"Error: Dataset file not found at {dataset_file}")
        sys.exit(1)
    
    with open(dataset_file, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if data.get('id') == problem_id:
                    return data
            except json.JSONDecodeError:
                continue
    
    print(f"Error: Problem ID '{problem_id}' not found in dataset")
    sys.exit(1)


def extract_module_name(problem_data):
    """Extract module name from problem data."""
    # Try to get from output context
    try:
        context = problem_data.get('output', {}).get('context', {})
        if context:
            # Get first key like "rtl/decoder_64b66b.sv"
            first_key = list(context.keys())[0]
            module_name = Path(first_key).stem  # Gets filename without extension
            return module_name
    except (KeyError, IndexError):
        pass
    
    # Try to get from harness files
    try:
        harness_files = problem_data.get('harness', {}).get('files', {})
        for key in harness_files.keys():
            if 'rtl/' in key and key.endswith('.sv'):
                module_name = Path(key).stem
                return module_name
    except (KeyError, IndexError):
        pass
    
    return None


def read_file_safe(filepath):
    """Safely read a file, return empty string if not found."""
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Error reading {filepath}: {e}")
    return ""


def find_error_file(error_dir):
    """Find the first .txt file in the error directory."""
    if not os.path.exists(error_dir):
        return None
    
    error_dir_path = Path(error_dir)
    txt_files = list(error_dir_path.glob("*.txt"))
    
    if txt_files:
        return str(txt_files[0])
    return None


def get_latest_iteration(work_dir, problem_name):
    """Get the latest iteration number for a problem by scanning harness directory."""
    harness_dir = os.path.join(work_dir, problem_name, "harness")
    
    if not os.path.exists(harness_dir):
        print(f"Warning: Harness directory not found at {harness_dir}")
        return None
    
    # Get all numeric directory names
    iterations = []
    for item in os.listdir(harness_dir):
        item_path = os.path.join(harness_dir, item)
        if os.path.isdir(item_path) and item.isdigit():
            iterations.append(int(item))
    
    if not iterations:
        print(f"Warning: No iteration directories found in {harness_dir}")
        return None
    
    # Return the highest iteration number
    latest = max(iterations)
    print(f"Auto-detected iteration: {latest} (found iterations: {sorted(iterations)})")
    return str(latest)


def enhance_prompt(original_prompt, error_content, sim_log_content, code_content):
    """Enhance the prompt with error information and previous code."""
    enhanced_prompt = original_prompt
    
    if error_content:
        enhanced_prompt += "\n\n---\n\n## Previous Iteration Errors\n\n"
        enhanced_prompt += "### Runtime Errors:\n```\n"
        enhanced_prompt += error_content.strip()
        enhanced_prompt += "\n```\n\n"
    
    if code_content:
        enhanced_prompt += "---\n\n## Previous Generated Code (with errors):\n\n```systemverilog\n"
        enhanced_prompt += code_content.strip()
        enhanced_prompt += "\n```\n\n"
        enhanced_prompt += "Please fix the errors in the code above.\n"
    
    return enhanced_prompt


def main():
    parser = argparse.ArgumentParser(
        description='Create a temporary dataset with enhanced prompt including errors and code'
    )
    parser.add_argument('problem_id', help='Problem ID to extract')
    parser.add_argument('work_dir', nargs='?', default='work_testing_2', 
                        help='Work directory (default: work_testing_2)')
    parser.add_argument('output_file', nargs='?', default='dataset/temp_dataset.jsonl',
                        help='Output file path (default: dataset/temp_dataset.jsonl)')
    
    args = parser.parse_args()
    
    # Configuration
    problem_id = args.problem_id
    work_dir = args.work_dir
    output_file = args.output_file
    dataset_file = "dataset/cvdp_v1.0.2_nonagentic_code_generation_no_commercial.jsonl"
    
    print(f"Processing problem: {problem_id}")
    print(f"Work directory: {work_dir}")
    print(f"Output file: {output_file}")
    print()
    
    # Find problem in dataset
    problem_data = find_problem_in_dataset(dataset_file, problem_id)
    
    # Extract problem_name (remove last 5 characters: _0001, _0006, etc.)
    problem_name = problem_id[:-5] if len(problem_id) > 5 else problem_id
    
    # Auto-detect the latest iteration
    iteration = get_latest_iteration(work_dir, problem_name)
    if not iteration:
        print("Error: Could not find any iteration directories")
        sys.exit(1)
    
    # Extract module name
    module_name = extract_module_name(problem_data)
    if not module_name:
        print("Warning: Could not extract module_name from JSON")
        module_name = "unknown"
    else:
        print(f"Module name: {module_name}")
    
    # Construct paths
    error_dir = f"{work_dir}/{problem_name}/extracted_errors"
    code_path = f"{work_dir}/{problem_name}/harness/{iteration}/rtl/{module_name}.sv"
    sim_log_path = f"{work_dir}/{problem_name}/harness/{iteration}/rundir/sim.log"
    
    print(f"\nLooking for:")
    print(f"  Error directory: {error_dir}")
    print(f"  Code file: {code_path}")
    print(f"  Sim log: {sim_log_path}")
    print()
    
    # Find and read error file
    error_file = find_error_file(error_dir)
    error_content = ""
    if error_file:
        print(f"Found error file: {error_file}")
        error_content = read_file_safe(error_file)
    else:
        print(f"Warning: No error file found in {error_dir}")
    
    # Read sim.log
    sim_log_content = ""
    if os.path.exists(sim_log_path):
        print(f"Found sim.log: {sim_log_path}")
        sim_log_content = read_file_safe(sim_log_path)
    else:
        print(f"Warning: sim.log not found at {sim_log_path}")
    
    # Read Verilog code
    code_content = ""
    if os.path.exists(code_path):
        print(f"Found code file: {code_path}")
        code_content = read_file_safe(code_path)
    else:
        print(f"Warning: Code file not found at {code_path}")
    
    # Get original prompt
    original_prompt = problem_data.get('input', {}).get('prompt', '')
    
    # Enhance the prompt
    enhanced_prompt = enhance_prompt(original_prompt, error_content, sim_log_content, code_content)
    
    # Update the problem data
    problem_data['input']['prompt'] = enhanced_prompt
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Append to output file in JSONL format (one JSON object per line)
    with open(output_file, 'a') as f:
        json.dump(problem_data, f)
        f.write('\n')  # JSONL requires newline after each entry
    
    print(f"\n✓ Successfully appended to dataset!")
    print(f"  File location: {os.path.abspath(output_file)}")
    
    # Show preview
    print("\nEnhanced prompt preview:")
    print("=" * 80)
    preview = enhanced_prompt[:1000] + "..." if len(enhanced_prompt) > 1000 else enhanced_prompt
    print(preview)
    print("=" * 80)


if __name__ == "__main__":
    main()
