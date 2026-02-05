#!/usr/bin/env python3
"""
Extract HDL/Hardware errors and Python tracebacks from log files
Extracts Verilog compilation, simulation, linker errors, and Python tracebacks
"""

import sys
import re
from pathlib import Path


def extract_hdl_errors(log_file):
    """Extract Verilog/SystemVerilog compilation, simulation errors, and Python tracebacks"""
    
    if not Path(log_file).exists():
        print(f"Error: File not found: {log_file}")
        sys.exit(1)
    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    error_blocks = []
    
    # Extract Python tracebacks first
    in_traceback = False
    current_traceback = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Start of traceback
        if 'Traceback (most recent call last):' in line:
            in_traceback = True
            current_traceback = [line.rstrip()]
            continue
        
        # Inside traceback - collect indented lines and error lines
        if in_traceback:
            if line.startswith('                                                        ') or \
               line.startswith('  ') or \
               re.match(r'\w+(Error|Exception):', stripped):
                current_traceback.append(line.rstrip())
            else:
                # End of traceback block
                if current_traceback:
                    error_blocks.append(current_traceback)
                    current_traceback = []
                in_traceback = False
    
    # Add last traceback if exists
    if current_traceback:
        error_blocks.append(current_traceback)
    
    # Extract CalledProcessError and other exceptions (without full traceback)
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # CalledProcessError from subprocess
        if 'CalledProcessError:' in line or 'subprocess.CalledProcessError:' in line:
            # Get context around the error
            start = max(0, i-3)
            end = min(len(lines), i+1)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Generic exception lines (Error/Exception at start of line after E marker)
        if re.match(r'^E\s+(\w+)(Error|Exception):', line):
            start = max(0, i-2)
            end = min(len(lines), i+1)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
    
    # Now extract HDL errors
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip lines that are part of Python tracebacks (already captured)
        if 'Traceback (most recent call last)' in line or \
           re.match(r'\s+File "/', line):
            continue
        
        # Verilog/SystemVerilog compilation errors
        # Patterns: "Error:", "error:", "ERROR:", syntax errors, etc.
        if re.search(r'(syntax error|parse error|compilation error)', line, re.IGNORECASE):
            start = max(0, i-2)
            end = min(len(lines), i+3)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Verilog simulator errors (iverilog, verilator, etc.)
        if re.search(r'(iverilog|verilator|vvp).*error', line, re.IGNORECASE):
            start = max(0, i-1)
            end = min(len(lines), i+3)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Undeclared/undefined identifiers
        if re.search(r'(undeclared|undefined|not declared|unknown identifier)', line, re.IGNORECASE):
            start = max(0, i-1)
            end = min(len(lines), i+2)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Type mismatch, width mismatch
        if re.search(r'(type mismatch|width mismatch|incompatible|illegal)', line, re.IGNORECASE):
            start = max(0, i-1)
            end = min(len(lines), i+2)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Linker errors
        if re.search(r'(undefined reference|linker error|ld:|link error)', line, re.IGNORECASE):
            start = max(0, i-1)
            end = min(len(lines), i+2)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Assertion failures (SystemVerilog/simulation)
        if re.search(r'(assertion failed|assert.*failed|\$fatal|\$error)', line, re.IGNORECASE) and \
           not 'File "/src' in line:
            start = max(0, i-1)
            end = min(len(lines), i+2)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Segmentation fault
        if re.search(r'(segmentation fault|segfault|core dumped|signal 11)', line, re.IGNORECASE):
            start = max(0, i-2)
            end = min(len(lines), i+3)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # Module/port errors
        if re.search(r'(module.*not found|port.*not found|missing port|unresolved)', line, re.IGNORECASE):
            start = max(0, i-1)
            end = min(len(lines), i+2)
            block = [lines[j].rstrip() for j in range(start, end) if lines[j].strip()]
            error_blocks.append(block)
            continue
        
        # File not found (for includes, etc.)
        if re.search(r'(cannot open|file not found|no such file).*\.(v|sv|vh|svh)', line, re.IGNORECASE):
            block = [line.rstrip()]
            error_blocks.append(block)
            continue
        
        # Simulation runtime errors (X propagation, etc.)
        if re.search(r'(unknown value|value is x|value is z|tri-state)', line, re.IGNORECASE) and \
           not 'Cannot convert Logic' in line:
            block = [line.rstrip()]
            error_blocks.append(block)
            continue
    
    # Remove duplicates while preserving order
    seen = set()
    unique_blocks = []
    for block in error_blocks:
        block_str = '\n'.join(block)
        if block_str not in seen and block:
            seen.add(block_str)
            unique_blocks.append(block)
    
    # Print all error blocks
    if not unique_blocks:
        print("No errors found in the log file.")
    else:
        for block in unique_blocks:
            for line in block:
                print(line)
            print()  # Blank line between blocks


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_traceback.py <log_file>")
        print("\nExtracts all hardware and software errors:")
        print("  - Python tracebacks")
        print("  - Verilog/SystemVerilog compilation errors")
        print("  - Linker errors")
        print("  - Assertion failures")
        print("  - Segmentation faults")
        print("  - Module/port errors")
        sys.exit(1)
    
    log_file = sys.argv[1]
    extract_hdl_errors(log_file)


if __name__ == "__main__":
    main()
