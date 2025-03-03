#!/usr/bin/env python3
"""
Generate source code previews for files in a directory.
Outputs the first N lines of each file, prepended with file paths.
"""
import os
import argparse
import sys
from shared.fs_utils import walk_filtered_files

def read_file_preview(file_path, max_lines=200):
    """Read the first max_lines from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"... [truncated after {max_lines} lines] ...\n")
                    break
                lines.append(line)
            return ''.join(lines)
    except UnicodeDecodeError:
        return f"[WARNING: File appears to be binary or uses an unsupported encoding]\n"
    except Exception as e:
        return f"[ERROR: Could not read file: {str(e)}]\n"

def generate_preview(root_dir, max_lines=200, show_hidden=False, 
                    show_deps=False, respect_gitignore=True, output_file=None):
    """
    Generate a preview of source files with their relative paths.
    
    Args:
        root_dir (str): Root directory to start traversal
        max_lines (int): Maximum number of lines to include per file
        show_hidden (bool): Whether to include hidden files
        show_deps (bool): Whether to include dependency directories
        respect_gitignore (bool): Whether to respect .gitignore patterns
        output_file (str): Path to output file (or None for stdout)
    """
    # Open output file if specified
    out = sys.stdout
    if output_file:
        out = open(output_file, 'w', encoding='utf-8')
    
    try:
        # Print header
        root_dir_abs = os.path.abspath(root_dir)
        print(f"SOURCE CODE PREVIEW FOR: {root_dir_abs}", file=out)
        print(f"{"=" * 80}", file=out)
        print(f"", file=out)
        
        # Walk through filtered files
        for abs_path, rel_path in walk_filtered_files(
            root_dir, show_hidden, show_deps, respect_gitignore, binary_check=True
        ):
            # Print file header
            print(f"FILE: {rel_path}", file=out)
            print(f"{'-' * 80}", file=out)
            
            # Print file content preview
            content = read_file_preview(abs_path, max_lines)
            print(content, file=out)
            
            # Print separator
            print(f"\n{'=' * 80}\n", file=out)
    finally:
        # Close the output file if opened
        if output_file and out != sys.stdout:
            out.close()

def main():
    parser = argparse.ArgumentParser(
        description="Generate source code previews for files in a directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "path", 
        nargs="?", 
        default=".", 
        help="Directory path to start from"
    )
    parser.add_argument(
        "-n", "--max-lines",
        type=int,
        default=200,
        help="Maximum number of lines to include per file"
    )
    parser.add_argument(
        "-a", "--all", 
        action="store_true", 
        help="Show hidden files and directories (starting with '.')"
    )
    parser.add_argument(
        "--show-deps", 
        action="store_true", 
        help="Show dependency and build directories (node_modules, __pycache__, etc.)"
    )
    parser.add_argument(
        "--no-gitignore", 
        action="store_true", 
        help="Don't respect .gitignore patterns"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: print to stdout)"
    )
    
    args = parser.parse_args()
    
    # Generate preview with specified options
    generate_preview(
        args.path,
        max_lines=args.max_lines,
        show_hidden=args.all,
        show_deps=args.show_deps,
        respect_gitignore=not args.no_gitignore,
        output_file=args.output
    )

if __name__ == "__main__":
    main()