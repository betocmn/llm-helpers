#!/usr/bin/env python3
"""
Print directory tree with customizable options.
"""
import os
import argparse
import collections
from shared.fs_utils import (
    COMMON_IGNORE_DIRS,
    parse_gitignore,
    is_ignored_by_gitignore,
    walk_filtered_files
)

def build_tree_structure(root_dir, dirs_only=False, show_hidden=False, 
                        show_deps=False, respect_gitignore=True):
    """
    Build a tree structure from the directory.
    
    Args:
        root_dir (str): Root directory to start from
        dirs_only (bool): Only include directories if True
        show_hidden (bool): Show hidden files and directories
        show_deps (bool): Show dependency directories
        respect_gitignore (bool): Whether to respect gitignore patterns
        
    Returns:
        dict: A nested dictionary representing the tree structure
    """
    # Create a tree structure using defaultdict
    tree = collections.defaultdict(dict)
    
    # If we only want directories, we need to walk the directory structure ourselves
    if dirs_only:
        # Load gitignore patterns if needed
        gitignore_patterns = None
        if respect_gitignore:
            gitignore_path = os.path.join(root_dir, '.gitignore')
            gitignore_patterns = parse_gitignore(gitignore_path)
            
        # Walk the directory structure
        for dirpath, dirnames, _ in os.walk(root_dir):
            # Filter directories in-place
            i = 0
            while i < len(dirnames):
                dirname = dirnames[i]
                dir_path = os.path.join(dirpath, dirname)
                rel_path = os.path.relpath(dir_path, root_dir)
                
                # Skip hidden directories
                if dirname.startswith('.') and not show_hidden:
                    dirnames.pop(i)
                    continue
                    
                # Skip common dependency directories
                if dirname in COMMON_IGNORE_DIRS and not show_deps:
                    dirnames.pop(i)
                    continue
                    
                # Skip directories ignored by gitignore
                if respect_gitignore and gitignore_patterns and is_ignored_by_gitignore(rel_path, True, gitignore_patterns):
                    dirnames.pop(i)
                    continue
                    
                # Add directory to tree
                rel_dir = os.path.relpath(dirpath, root_dir)
                if rel_dir == '.':
                    # Root directory
                    tree[dirname] = collections.defaultdict(dict)
                else:
                    # Nested directory - navigate to the right spot in the tree
                    parts = rel_dir.split(os.sep)
                    current = tree
                    for part in parts:
                        if part != '.':
                            current = current[part]
                    current[dirname] = collections.defaultdict(dict)
                
                i += 1
    else:
        # Use walk_filtered_files to get all files
        for abs_path, rel_path in walk_filtered_files(
            root_dir, show_hidden, show_deps, respect_gitignore, binary_check=False
        ):
            # Skip the .gitignore file if we're not showing hidden files
            if os.path.basename(rel_path) == '.gitignore' and not show_hidden:
                continue
                
            # Split the path into parts
            parts = rel_path.split(os.sep)
            
            # Navigate to the right spot in the tree
            current = tree
            for i, part in enumerate(parts):
                if i < len(parts) - 1:  # Directory
                    if part not in current:
                        current[part] = collections.defaultdict(dict)
                    current = current[part]
                else:  # File
                    current[part] = None
    
    return tree

def print_tree_structure(tree, prefix=''):
    """
    Print the tree structure with formatting.
    
    Args:
        tree (dict): The tree structure to print
        prefix (str): Prefix for the current line
    """
    # Get sorted items (directories first, then files)
    items = sorted(tree.items(), key=lambda x: (x[1] is None, x[0]))
    
    for i, (name, subtree) in enumerate(items):
        is_last = i == len(items) - 1
        branch = "└── " if is_last else "├── "
        
        # Add slash to directories for better visibility
        display_name = name + "/" if subtree is not None else name
        print(f"{prefix}{branch}{display_name}")
        
        if subtree is not None:
            # Create appropriate prefix for next level
            next_prefix = prefix + ("    " if is_last else "│   ")
            print_tree_structure(subtree, next_prefix)

def main():
    parser = argparse.ArgumentParser(
        description="Print directory tree with customizable options.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "path", 
        nargs="?", 
        default=".", 
        help="Directory path to start from"
    )
    parser.add_argument(
        "-d", "--dirs-only", 
        action="store_true", 
        help="Only display directories, not files"
    )
    parser.add_argument(
        "-n", "--no-recursive", 
        action="store_true", 
        help="Don't recursively display subdirectories"
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
    
    args = parser.parse_args()
    
    # Display root directory name
    root_path = args.path.rstrip(os.sep)
    display_root = os.path.basename(root_path) or root_path
    print(f"{display_root}/")
    
    # Handle non-recursive case
    if args.no_recursive:
        # For non-recursive, we'll just list the top-level entries
        try:
            entries = os.listdir(root_path)
            
            # Filter and sort entries
            dirs = []
            files = []
            
            for entry in sorted(entries):
                path = os.path.join(root_path, entry)
                is_dir = os.path.isdir(path)
                
                # Apply basic filtering
                if entry.startswith('.') and not args.all:
                    continue
                    
                if is_dir and entry in COMMON_IGNORE_DIRS and not args.show_deps:
                    continue
                    
                if is_dir:
                    dirs.append(entry)
                elif not args.dirs_only:
                    files.append(entry)
            
            # Print entries
            all_entries = dirs + files
            for i, entry in enumerate(all_entries):
                is_last = i == len(all_entries) - 1
                branch = "└── " if is_last else "├── "
                path = os.path.join(root_path, entry)
                
                # Add slash to directories for better visibility
                display_name = entry + "/" if os.path.isdir(path) else entry
                print(f"{branch}{display_name}")
                
        except Exception as e:
            print(f"Error reading directory: {e}")
    else:
        # Build and print the tree structure
        tree = build_tree_structure(
            root_path,
            dirs_only=args.dirs_only,
            show_hidden=args.all,
            show_deps=args.show_deps,
            respect_gitignore=not args.no_gitignore
        )
        print_tree_structure(tree)

if __name__ == "__main__":
    main()