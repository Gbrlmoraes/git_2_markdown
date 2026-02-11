# Git to Markdown

> 🎸 **Vibe Coding Project** - This is a fun experimental project to test some features and create a simple tool that could be useful in future projects. Built with good vibes and curiosity!

Convert Git repositories into a single Markdown file suitable for LLM consumption.

## Features

- 📂 **Clone remote repositories** or use local directories
- 🌳 **Directory tree view** at the beginning of the output
- 📄 **Smart file detection** - automatically identifies text-based files
- 🎨 **Syntax highlighting** - appropriate language identifiers for code blocks
- 📑 **README first** - ensures README.md appears at the top of the content
- 📘 **Optional PDF support** - extract text from PDFs using Docling
- 🔧 **Configurable** - exclude directories, add extensions, set file size limits

## Installation

### Using UV (recommended)

```bash
# Basic installation
uv pip install git-2-markdown

# With PDF support
uv pip install 'git-2-markdown[pdf]'
```

### From source

```bash
git clone https://github.com/yourusername/git-2-markdown
cd git-2-markdown
uv sync
```

### Development installation

```bash
uv sync --all-extras
```

## Usage

### Command Line

```bash
# Convert a remote repository
git-2-markdown https://github.com/user/repo

# Convert a local repository
git-2-markdown ./my-project

# Specify output file
git-2-markdown https://github.com/user/repo -o output.md

# Include PDF files (requires pdf extra)
git-2-markdown ./project --include-pdf

# Output to stdout
git-2-markdown ./project --stdout

# Customize tree depth
git-2-markdown ./project --max-depth 3

# Include table of contents
git-2-markdown ./project --include-toc

# Add custom file extensions
git-2-markdown ./project --extensions .jsx .tsx .astro

# Exclude specific directories
git-2-markdown ./project --exclude-dirs tests docs examples

# Set maximum file size (bytes)
git-2-markdown ./project --max-file-size 100000

# Split output into multiple files (default: 100k chars per file)
git-2-markdown ./project --split

# Split with custom character limit
git-2-markdown ./project --split --max-chars 50000

# Check if PDF support is available
git-2-markdown --check-pdf
```

### Short alias

You can also use `g2md` as a shorter alias:

```bash
g2md https://github.com/user/repo -o output.md
```

### As a Python module

```python
from modules.converter import GitToMarkdownConverter, ConverterConfig

# Basic usage
converter = GitToMarkdownConverter()
markdown = converter.convert("https://github.com/user/repo")

# With configuration
config = ConverterConfig(
    include_pdf=True,
    include_tree=True,
    include_toc=True,
    max_tree_depth=4,
    max_file_size=500000,  # 500KB
    custom_extensions={".jsx", ".tsx"},
    exclude_dirs={"tests", "docs"},
)
converter = GitToMarkdownConverter(config)
markdown = converter.convert("./my-project", output_path="output.md")
```

## Output Format

The generated Markdown file has the following structure:

```markdown
# Repository: project-name

## Repository Structure

```
project-name/
├── src/
│   ├── main.py
│   └── utils.py
├── README.md
└── pyproject.toml
```

## File Contents

### README.md
**Path:** `README.md`

```markdown
# Project documentation...
```

### main.py
**Path:** `src/main.py`

```python
def main():
    ...
```
```

## Project Structure

```
git-2-markdown/
├── main.py                      # CLI entry point
├── pyproject.toml               # Project configuration
├── README.md                    # This file
└── modules/
    ├── __init__.py              # Package exports
    ├── converter.py             # Main converter orchestration
    ├── file_discovery.py        # File discovery and filtering
    ├── git_handler.py           # Git repository operations
    ├── markdown_generator.py    # Markdown output generation
    ├── pdf_reader.py            # Optional PDF reading (Docling)
    └── text_reader.py           # Text file reading
```

## Supported File Types

The tool automatically detects and includes common text-based files:

- **Programming**: `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.scala`
- **Web**: `.html`, `.css`, `.scss`, `.vue`, `.svelte`, `.jsx`, `.tsx`
- **Data**: `.json`, `.yaml`, `.yml`, `.toml`, `.xml`, `.csv`
- **Documentation**: `.md`, `.rst`, `.txt`, `.adoc`
- **Config**: `.ini`, `.cfg`, `.conf`, `.env`, `.properties`
- **Build**: `Dockerfile`, `Makefile`, `.tf`, `.gradle`
- **Shell**: `.sh`, `.bash`, `.ps1`, `.bat`

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output file path | `<repo_name>.md` |
| `--include-pdf` | Include PDF files | `False` |
| `--no-tree` | Exclude directory tree | `False` |
| `--include-toc` | Include table of contents | `False` |
| `--max-depth` | Max tree display depth | Unlimited |
| `--max-file-size` | Max file size in bytes | Unlimited |
| `--extensions` | Additional extensions | None |
| `--exclude-dirs` | Additional dirs to exclude | None |
| `--split` | Split output into multiple files | `False` |
| `--max-chars` | Max chars per file when splitting | `100000` |
| `--stdout` | Output to stdout | `False` |
| `--verbose`, `-v` | Verbose output | `False` |

## Dependencies

### Required
- `gitpython>=3.1.0` - Git repository operations

### Optional (PDF support)
- `docling>=2.0.0` - PDF text extraction

### Development
- `pytest>=8.0.0` - Testing
- `ruff>=0.4.0` - Linting and formatting
- `mypy>=1.10.0` - Type checking

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Vibe Code Specification

| Tool | Version |
|------|---------|
| **IDE** | VSCode with Copilot PRO |
| **Model** | Claude Opus 4.5 |