#!/usr/bin/env python3
import os
import glob
from pathlib import Path
import subprocess

mjnroot = os.path.join("/home", "martin", "mjnurse")
cli_home = os.path.join(mjnroot, "cli-builder")
web_base = os.path.join(mjnroot, "mjnurse-website", "other", "cli_builder")

# Clean up previous files
for f in glob.glob(os.path.join(web_base, "definition*")):
    os.remove(f)
for f in glob.glob(os.path.join(web_base, "cli-builder-script*")):
    os.remove(f)

cli_builder_dir = os.path.join(mjnroot, "cli-builder")
os.chdir(cli_builder_dir)

# Generate CLI_Builder_script.md
dest = os.path.join(web_base, "cli-builder-script.md")
with open(dest, "w") as f:
    f.write("---\n")
    f.write("title: CLI builder\n")
    f.write("---\n")
    f.write("\n")
    f.write("This bash script generates a cli (command line interface) bash script from a\n")
    f.write("definition file.  The structure of the definition file is code header below. \n")
    f.write("This script also generates an alias file which contains a set of alias\n")
    f.write("commands which run each command in the definition file using the associated\n")
    f.write("shortcut prepended with an '@'.\n")
    f.write("\n")
    f.write("```bash\n")
    with open("cli-builder", "r") as cli_builder_file:
        f.write(cli_builder_file.read())
    f.write("```\n")

cli_builder_stat = os.stat("cli-builder")
os.utime(dest, (cli_builder_stat.st_atime, cli_builder_stat.st_mtime))

# Create the definition file pages
for f_path in glob.glob("*.def"):
    print(f"Generating: {f_path} page")
    with open(f_path, "r") as f:
        first_line = f.readline()
        title = first_line.lstrip("# ").strip()

    dest_fname = f"definition-file-{title.replace(' ', '-')}-{os.path.basename(f_path).replace(' ', '-')}.md"
    dest = os.path.join(web_base, dest_fname)

    with open(dest, "w") as f:
        f.write("---\n")
        f.write(f"title: {os.path.basename(f_path)}\n")
        f.write("---\n")
        f.write("\n")
        f.write("```bash\n")
        with open(f_path, "r") as def_file:
            f.write(def_file.read())
        f.write("\n")
        f.write("```\n")

    f_stat = os.stat(f_path)
    os.utime(dest, (f_stat.st_atime, f_stat.st_mtime))

print("Done.")
