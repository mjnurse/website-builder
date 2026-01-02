#!/usr/bin/env python3
"""
NAME
  gen_bash_web_pgs - Creates web pages for bash scripts

USAGE
  gen_bash_web_pgs.py

DESCRIPTION
  Creates web pages for bash scripts.

AUTHOR
  mjnurse.github.io - 2020
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
    
    output_dir = '../mjnurse-website/linuxbash'
    bash_dir = '../bash'
    
    # Remove existing Script* files
    for f in glob.glob(os.path.join(output_dir, 'script_*')):
        os.remove(f)
        print(f"Removed: {f}")
    
    # Change to bash directory
    if not os.path.isdir(bash_dir):
        print(f"Error: Directory not found: {bash_dir}")
        return 1
    
    os.chdir(bash_dir)
    
    # Process bash scripts with web_desc_line
    for filepath in glob.glob('*'):
        if not os.path.isfile(filepath):
            continue
        
        # Check if file contains web_desc_line
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '^web_desc_line' not in content and 'web_desc_line=' not in content:
                    continue
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue
        
        # Extract web_desc_line value
        dl = None
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('web_desc_line='):
                    dl = extract_value(line, r'web_desc_line=(.+)')
                    break
        
        if not dl:
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
            out.write("```bash\n")
            
            # Read and write the bash script content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as src:
                out.write(src.read())
            
            out.write("```\n")
        
        # Preserve modification time
        mtime = get_file_mtime(filepath)
        set_file_mtime(dest_path, mtime)
    
    # Create bash script packs and pack pages
    print("\nCreate bash script packs and pack pages")
    
    # Remove existing pack files
    for f in glob.glob(os.path.join(output_dir, 'Linux_bash*Pack.md')):
        os.remove(f)
        print(f"Removed: {f}")
    
    # Process packs
    for pack_name in ['default']:
        # Find files with pack_member containing the pack name
        file_list = []
        for filepath in glob.glob('*'):
            if not os.path.isfile(filepath):
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if re.search(rf'pack_member.*{pack_name}', content):
                        file_list.append(filepath)
            except Exception:
                continue
        
        if not file_list:
            print(f"No files found for pack: {pack_name}")
            continue
        
        # Run pack command
        pack_cmd = ['pack', '-s', '-f', '-n', pack_name] + file_list
        try:
            subprocess.run(pack_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running pack command: {e}")
            continue
        except FileNotFoundError:
            print("Warning: 'pack' command not found, skipping pack creation")
            continue
        
        # Create pack markdown file
        dest_path = os.path.join(output_dir, f'Linux_bash_{pack_name}_pack.md')
        
        print(f"\npack-file: {dest_path}")
        print(f"pack-file: {' '.join(file_list)}")
        
        pack_file = f"{pack_name}.pack"
        
        with open(dest_path, 'w', encoding='utf-8') as out:
            out.write("---\n")
            out.write(f"title: Linux bash {pack_name} Pack\n")
            out.write("---\n")
            out.write("\n")
            out.write("Packs contain bash scripts which have been compressed and converted to a\n")
            out.write("base64 string.  This is a convenient wat to copy a set of bash scripts\n")
            out.write("into a linux environment using only a command line terminal.\n")
            out.write("\n")
            out.write("<script>\n")
            
            # Read pack file content
            if os.path.isfile(pack_file):
                with open(pack_file, 'r', encoding='utf-8', errors='ignore') as pf:
                    pack_content = pf.read()
                out.write(f"  let packText=`{pack_content}\n")
            else:
                out.write(f"  let packText=`\n")
            
            out.write("`;\n")
            out.write("</script>\n")
            out.write("\n")
            out.write("## Contents\n")
            out.write("```bash\n")
            
            # Run h -m command for file list
            try:
                result = subprocess.run(['h', '-m'] + file_list, 
                                      capture_output=True, text=True, check=True)
                out.write(result.stdout)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # If h command fails or doesn't exist, just list files
                for f in file_list:
                    out.write(f"{f}\n")
            
            out.write("```\n")
            out.write("\n")
            out.write("<button onCLick='copyToClipboard(packText)'>Copy To Clipboard</button>\n")
            out.write("\n")
            out.write("```bash\n")
            
            # Write pack content
            if os.path.isfile(pack_file):
                with open(pack_file, 'r', encoding='utf-8', errors='ignore') as pf:
                    out.write(pf.read())
            
            out.write("```\n")
    
    return 0

if __name__ == '__main__':
    exit(main())
