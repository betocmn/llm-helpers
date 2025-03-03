# LLM Helpers

A collection of Python scripts to help with LLM development, especially for creating prompts from source code.

## Requirements

- Python 3.x

## Tools

### print_file_tree.py

A utility to print directory tree structures with customizable options. The script intelligently handles `.gitignore` patterns and common dependency directories.

#### Usage

```bash
python bin/print_file_tree.py [path] [options]
```

#### Arguments

- `path`: Directory path to start from (default: current directory)

#### Options

- `-d, --dirs-only`: Only display directories, not files
- `-n, --no-recursive`: Don't recursively display subdirectories
- `-a, --all`: Show hidden files and directories (starting with '.')
- `--show-deps`: Show dependency and build directories (node_modules, __pycache__, etc.)
- `--no-gitignore`: Don't respect .gitignore patterns

#### Features

- **Smart Filtering**: By default, ignores common dependency directories like `node_modules`, `__pycache__`, `venv`, etc.
- **GitIgnore Support**: Automatically respects `.gitignore` patterns in the target directory
- **Hidden Files**: Option to show or hide files and directories that start with a dot
- **Customizable Display**: Control recursion depth and content types

#### Examples

**Print the current directory tree:**
```bash
python bin/print_file_tree.py
```

**Print a specific directory tree:**
```bash
python bin/print_file_tree.py /path/to/directory
```

**Print only directories (no files):**
```bash
python bin/print_file_tree.py -d
```

**Print without recursion (only top-level entries):**
```bash
python bin/print_file_tree.py -n
```

**Show hidden files and directories:**
```bash
python bin/print_file_tree.py -a
```

**Show dependency directories:**
```bash
python bin/print_file_tree.py --show-deps
```

**Ignore .gitignore patterns:**
```bash
python bin/print_file_tree.py --no-gitignore
```

**Combine options:**
```bash
python bin/print_file_tree.py /path/to/directory -d -a --show-deps
```

#### Example Output

```
project/
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   └── utils.py
└── tests/
    └── test_utils.py
```

### generate_prompt_with_source_code.py

A utility to generate source code previews for files in a directory. This is useful for creating prompts that include code context for LLMs, enabling them to understand and work with your codebase more effectively.

#### Usage

```bash
python bin/generate_prompt_with_source_code.py [path] [options]
```

#### Arguments

- `path`: Directory path to start from (default: current directory)

#### Options

- `-n, --max-lines`: Maximum number of lines to include per file (default: 200)
- `-a, --all`: Show hidden files and directories (starting with '.')
- `--show-deps`: Show dependency and build directories (node_modules, __pycache__, etc.)
- `--no-gitignore`: Don't respect .gitignore patterns
- `-o, --output`: Output file path (default: print to stdout)

#### Features

- **Code Previews**: Generates previews of source code files with their relative paths
- **Smart Filtering**: Uses the same filtering logic as print_file_tree.py
- **Truncation**: Limits the number of lines per file to avoid overwhelming output
- **Output Options**: Can output to a file or stdout
- **Error Handling**: Gracefully handles binary files and encoding issues
- **Binary Detection**: Automatically skips binary files to avoid corrupted output

#### Use Cases

- **Context for LLMs**: Provide code context to LLMs for more accurate code generation or modifications
- **Documentation**: Generate code previews for documentation purposes
- **Code Reviews**: Create summaries of codebases for review
- **Onboarding**: Help new team members understand the structure and content of a codebase
- **Prompt Engineering**: Build custom prompts that include relevant code snippets

#### Examples

**Generate preview for current directory:**
```bash
python bin/generate_prompt_with_source_code.py
```

**Generate preview for a specific directory:**
```bash
python bin/generate_prompt_with_source_code.py /path/to/directory
```

**Limit to 100 lines per file:**
```bash
python bin/generate_prompt_with_source_code.py -n 100
```

**Include hidden files:**
```bash
python bin/generate_prompt_with_source_code.py -a
```

**Save output to a file:**
```bash
python bin/generate_prompt_with_source_code.py -o code_preview.txt
```

**Combine with LLM prompt:**
```bash
echo "Please analyze this code and suggest improvements:" > prompt.txt
python bin/generate_prompt_with_source_code.py -o code.txt
cat prompt.txt code.txt | llm-cli
```

#### Example Output

```
SOURCE CODE PREVIEW FOR: /path/to/project
================================================================================

FILE: src/main.py
--------------------------------------------------------------------------------
#!/usr/bin/env python3
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()

================================================================================

FILE: src/utils.py
--------------------------------------------------------------------------------
def helper_function():
    return "I'm helping!"

... [more files] ...
```

## Project Structure

```
llm-helpers/
├── bin/                      # Executable scripts
│   ├── print_file_tree.py     # Directory tree visualization
│   ├── generate_prompt_with_source_code.py  # Source code preview generator
│   └── shared/               # Shared utilities
│       └── fs_utils.py       # File system utilities
└── README.md                 # This file
```

## License

See the [LICENSE](LICENSE) file for details. 