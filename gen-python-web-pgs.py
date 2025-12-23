#!/usr/bin/env python3
"""
NAME
  gen_python_web_pgs - Creates web pages for python programs

USAGE
  gen_python_web_pgs.py

DESCRIPTION
  Creates web pages for python programs.

AUTHOR
  mjnurse.dev - 2025
"""

import os
import re
import glob
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

def extract_value(line, pattern):
    """Extract value from a line matching the pattern."""
    match = re.match(pattern, line)
    if match:
        value = match.group(1).strip()
        # Remove quotes if present
        value = value.strip('"').strip("'")
        # Remove trailing spaces
        value = value.rstrip()
        return value
    return None

def get_file_mtime(filepath):
    """Get the modification time of a file."""
    return os.path.getmtime(filepath)

def set_file_mtime(filepath, mtime):
    """Set the modification time of a file."""
    os.utime(filepath, (mtime, mtime))

def main():
    
    output_dir = '../mjnurse-website/python'
    python_dir = '../python'
    
    # Remove existing program* files
    for f in glob.glob(os.path.join(output_dir, 'script_*')):
        os.remove(f)
        print(f"Removed: {f}")
    
    # Change to python directory
    if not os.path.isdir(python_dir):
        print(f"Error: Directory not found: {python_dir}")
        return 1
    
    os.chdir(python_dir)
    
    # Process python programs with web_desc_line
    for filepath in glob.glob('*'):
        print(f"Processing: {filepath}")
        if not os.path.isfile(filepath):
            continue
        
        # Extract web_desc_line value
        pattern = re.compile(r'web_desc_line\s*=\s*(.+)', re.IGNORECASE)
        dl = None
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = pattern.search(line)
                    if match:
                        dl = match.group(1).strip().replace('"', '').replace("'", '')
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue

        if dl is None:
            print(f"Skipping: {filepath} - no web_desc_line found")
            continue
        
        # Create destination filename
        dest_filename = f"script_{filepath}_-_{dl}.md"
        dest_filename = dest_filename.replace(' ', '_')
        dest_path = os.path.join(output_dir, dest_filename)
        
        if dl == "tbc":
            print(f"Skipping: {filepath} - web_desc_line: {dl}")
            continue
        
        print(f"dest_file: {os.path.basename(dest_path)}")
        
        # Create markdown file
        with open(dest_path, 'w', encoding='utf-8') as out:
            out.write("---\n")
            out.write(f"title: {filepath} - {dl}\n")
            out.write("---\n")
            out.write("\n")
            out.write("```python\n")
            
            # Read and write the python program content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as src:
                out.write(src.read())
            
            out.write("```\n")
        
        # Preserve modification time
        mtime = get_file_mtime(filepath)
        set_file_mtime(dest_path, mtime)
    
    return 0

if __name__ == '__main__':
    exit(main())
