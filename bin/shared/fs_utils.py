#!/usr/bin/env python3
"""
File system utilities for traversing and filtering files/directories.
"""
import os
import re
import fnmatch

# Common dependency/build directories to ignore by default
COMMON_IGNORE_DIRS = {
    # JavaScript/TypeScript
    'node_modules', 'dist', 'build', '.next', '.nuxt', 'coverage',
    
    # Python
    '__pycache__', 'venv', 'env', '.env', '.venv', '.pytest_cache',
    '.mypy_cache', 'site-packages', '.tox', '.eggs', 'egg-info',
    
    # Go
    'vendor', 'bin',
    
    # PHP
    'vendor', 'composer.phar',
    
    # Java/JVM
    'target', 'build', 'out', '.gradle', '.mvn', 'classes',
    
    # Ruby/Rails
    'vendor', 'tmp', 'log', '.bundle',
    
    # Django
    'migrations', 'staticfiles',
    
    # .NET/C#
    'bin', 'obj', 'packages',
    
    # Common cache directories
    '.cache', 'cache', '.sass-cache'
}

class GitIgnorePattern:
    def __init__(self, pattern):
        self.pattern = pattern
        self.is_negated = pattern.startswith('!')
        if self.is_negated:
            pattern = pattern[1:]
        
        self.is_dir_only = pattern.endswith('/')
        if self.is_dir_only:
            pattern = pattern[:-1]
            
        self.is_absolute = pattern.startswith('/')
        if self.is_absolute:
            pattern = pattern[1:]
            
        # Convert gitignore pattern to a regex pattern
        self.regex_pattern = self._pattern_to_regex(pattern)
    
    def _pattern_to_regex(self, pattern):
        # Escape all regex special characters except * and ?
        pattern = re.escape(pattern)
        
        # Convert gitignore glob patterns to regex
        pattern = pattern.replace('\\*\\*', '.*')  # ** -> .*
        pattern = pattern.replace('\\*', '[^/]*')  # * -> [^/]*
        pattern = pattern.replace('\\?', '[^/]')   # ? -> [^/]
        
        # Add start/end anchors based on pattern type
        if self.is_absolute:
            pattern = '^' + pattern
        else:
            pattern = '(^|/)' + pattern
            
        if self.is_dir_only:
            pattern = pattern + '(/|$)'
        else:
            pattern = pattern + '($|/)'
            
        return re.compile(pattern)
    
    def matches(self, path, is_dir=False):
        # Directory-only patterns can only match directories
        if self.is_dir_only and not is_dir:
            return False
            
        return bool(self.regex_pattern.search(path))

def parse_gitignore(gitignore_path):
    """Parse a .gitignore file and return a list of patterns"""
    if not os.path.exists(gitignore_path):
        return []
        
    patterns = []
    with open(gitignore_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            patterns.append(GitIgnorePattern(line))
    
    return patterns

def is_ignored_by_gitignore(rel_path, is_dir, gitignore_patterns):
    """Check if a path is ignored by gitignore patterns"""
    if not gitignore_patterns:
        return False
        
    # Default to not ignored
    ignored = False
    
    # Apply all patterns in order
    for pattern in gitignore_patterns:
        if pattern.matches(rel_path, is_dir):
            # If pattern matches, set ignored based on whether it's negated
            ignored = not pattern.is_negated
    
    return ignored

def is_binary_file(file_path, sample_size=8192):
    """Check if a file is binary by examining a sample of its contents"""
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
            # Check for null bytes which often indicate binary content
            if b'\x00' in sample:
                return True
            # Try to decode as text
            try:
                sample.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except (IOError, OSError):
        # If we can't read the file, assume it's binary to be safe
        return True

def walk_filtered_files(root_dir, show_hidden=False, show_deps=False, 
                       respect_gitignore=True, binary_check=True):
    """
    Walk through directory and yield file paths that pass all filters.
    
    Args:
        root_dir (str): Root directory to start traversal
        show_hidden (bool): Whether to include hidden files
        show_deps (bool): Whether to include dependency directories
        respect_gitignore (bool): Whether to respect .gitignore patterns
        binary_check (bool): Whether to filter out binary files
    
    Yields:
        tuple: (abs_path, rel_path) for each file
    """
    # Load gitignore patterns if needed
    gitignore_patterns = None
    if respect_gitignore:
        gitignore_path = os.path.join(root_dir, '.gitignore')
        gitignore_patterns = parse_gitignore(gitignore_path)
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter directories in-place (this affects os.walk traversal)
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
                
            i += 1
            
        # Process files in this directory
        for filename in filenames:
            # Skip hidden files
            if filename.startswith('.') and not show_hidden:
                continue
                
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, root_dir)
            
            # Skip files ignored by gitignore
            if respect_gitignore and gitignore_patterns and is_ignored_by_gitignore(rel_path, False, gitignore_patterns):
                continue
                
            # Skip binary files if requested
            if binary_check and is_binary_file(file_path):
                continue
                
            yield (file_path, rel_path)