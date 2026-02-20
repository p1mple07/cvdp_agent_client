#!/usr/bin/env python3
"""
Script to filter dataset by specific problem IDs
Usage: python filter_dataset.py
"""

import json
import argparse

def filter_dataset(input_file, output_file, problem_ids):
    """Filter dataset to include only specified problem IDs."""
    
    # Convert list to set for faster lookup
    target_ids = set(problem_ids)
    
    found_count = 0
    found_ids = set()
    
    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    print(f"Looking for {len(target_ids)} problem IDs...\n")
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line.strip():
                data = json.loads(line)
                problem_id = data.get('id')
                
                if problem_id in target_ids:
                    # Write matching entry to output file
                    json.dump(data, outfile)
                    outfile.write('\n')
                    found_count += 1
                    found_ids.add(problem_id)
                    print(f"✓ Found: {problem_id}")
    
    print(f"\n{'='*60}")
    print(f"Results:")
    print(f"  Total IDs requested: {len(target_ids)}")
    print(f"  Total IDs found: {found_count}")
    print(f"  Output file: {output_file}")
    
    # Check for missing IDs
    missing_ids = target_ids - found_ids
    if missing_ids:
        print(f"\n{'='*60}")
        print(f"Warning: {len(missing_ids)} IDs not found in dataset:")
        for missing_id in sorted(missing_ids):
            print(f"  - {missing_id}")
    else:
        print(f"\n✓ All requested IDs were found!")
    
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='Filter dataset to include only specific problem IDs'
    )
    parser.add_argument('-i', '--input', 
                        default='dataset/cvdp_v1.0.2_nonagentic_code_generation_no_commercial.jsonl',
                        help='Input dataset file')
    parser.add_argument('-o', '--output', 
                        default='dataset/filtered_dataset.jsonl',
                        help='Output dataset file')
    
    args = parser.parse_args()
    
    # List of problem IDs to filter
    problem_ids = [
        'cvdp_copilot_sigma_delta_audio_0007',
        'cvdp_copilot_signal_correlator_0015',
        'cvdp_copilot_signed_adder_0001',
        'cvdp_copilot_simple_spi_0001',
        'cvdp_copilot_single_number_0001',
        'cvdp_copilot_skid_buffer_0001',
        'cvdp_copilot_sobel_filter_0011',
        'cvdp_copilot_sorter_0001',
        'cvdp_copilot_sorter_0003',
        'cvdp_copilot_sorter_0009',
        'cvdp_copilot_sorter_0031',
        'cvdp_copilot_sorter_0051',
        'cvdp_copilot_sorter_0057',
        'cvdp_copilot_sorter_0059',
        'cvdp_copilot_sound_generator_0001',
        'cvdp_copilot_sprite_0004',
        'cvdp_copilot_sprite_0010',
    ]
    
    filter_dataset(args.input, args.output, problem_ids)


if __name__ == '__main__':
    main()
