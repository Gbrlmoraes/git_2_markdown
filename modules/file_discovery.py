"""
File discovery and filtering module.

Provides functionality to discover files in a repository and filter them
based on extensions, patterns, and other criteria.
"""

from collections.abc import Iterator
from pathlib import Path


# Default text-based file extensions
DEFAULT_TEXT_EXTENSIONS: set[str] = {
    # Programming languages
    ".py",
    ".pyw",
    ".pyi",  # Python
    ".js",
    ".mjs",
    ".cjs",  # JavaScript
    ".ts",
    ".tsx",
    ".mts",  # TypeScript
    ".jsx",  # React
    ".java",  # Java
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".hh",  # C/C++
    ".cs",  # C#
    ".go",  # Go
    ".rs",  # Rust
    ".rb",  # Ruby
    ".php",  # PHP
    ".swift",  # Swift
    ".kt",
    ".kts",  # Kotlin
    ".scala",  # Scala
    ".r",
    ".R",  # R
    ".lua",  # Lua
    ".pl",
    ".pm",  # Perl
    ".sh",
    ".bash",
    ".zsh",
    ".fish",  # Shell
    ".ps1",
    ".psm1",  # PowerShell
    ".bat",
    ".cmd",  # Batch
    # Web
    ".html",
    ".htm",
    ".xhtml",  # HTML
    ".css",
    ".scss",
    ".sass",
    ".less",  # Stylesheets
    ".vue",
    ".svelte",  # Frameworks
    # Data & Config
    ".json",
    ".jsonl",
    ".json5",  # JSON
    ".yaml",
    ".yml",  # YAML
    ".toml",  # TOML
    ".xml",
    ".xsl",
    ".xslt",  # XML
    ".ini",
    ".cfg",
    ".conf",  # Config
    ".env",
    ".env.example",
    ".env.local",  # Environment
    ".properties",  # Java properties
    # Documentation
    ".md",
    ".markdown",
    ".mdx",  # Markdown
    ".rst",  # reStructuredText
    ".txt",
    ".text",  # Plain text
    ".adoc",
    ".asciidoc",  # AsciiDoc
    # Build & CI
    ".dockerfile",  # Docker (note: Dockerfile has no extension)
    ".makefile",  # Make
    ".cmake",  # CMake
    ".gradle",  # Gradle
    ".tf",
    ".tfvars",  # Terraform
    # Other
    ".sql",  # SQL
    ".graphql",
    ".gql",  # GraphQL
    ".proto",  # Protocol Buffers
    ".csv",
    ".tsv",  # Data files
    ".gitignore",
    ".gitattributes",  # Git
    ".editorconfig",  # Editor config
    ".prettierrc",
    ".eslintrc",  # Linters/formatters
}

# Files without extensions that should be included
DEFAULT_INCLUDE_FILENAMES: set[str] = {
    "Dockerfile",
    "Makefile",
    "Jenkinsfile",
    "Vagrantfile",
    "Procfile",
    "Gemfile",
    "Rakefile",
    "LICENSE",
    "CHANGELOG",
    "CONTRIBUTING",
    "AUTHORS",
    "CODEOWNERS",
    "README",
    ".gitignore",
    ".gitattributes",
    ".dockerignore",
    ".editorconfig",
    ".nvmrc",
    ".python-version",
    ".ruby-version",
    ".node-version",
}

# Directories to always exclude
DEFAULT_EXCLUDE_DIRS: set[str] = {
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".nox",
    ".eggs",
    "*.egg-info",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    "bower_components",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "target",
    ".idea",
    ".vscode",
    ".vs",
    "*.xcodeproj",
    "*.xcworkspace",
    ".gradle",
    ".cache",
    ".parcel-cache",
    "coverage",
    ".nyc_output",
    "htmlcov",
}


class FileDiscovery:
    """Discovers and filters files in a repository."""

    def __init__(
        self,
        root_path: Path,
        text_extensions: set[str] | None = None,
        include_filenames: set[str] | None = None,
        exclude_dirs: set[str] | None = None,
        include_pdf: bool = False,
        custom_extensions: set[str] | None = None,
    ):
        """
        Initialize the file discovery.

        Args:
            root_path: Root path of the repository.
            text_extensions: Set of file extensions to include (with dots).
            include_filenames: Set of exact filenames to include.
            exclude_dirs: Set of directory names to exclude.
            include_pdf: Whether to include PDF files.
            custom_extensions: Additional extensions to include.
        """
        self.root_path = root_path.resolve()
        self.text_extensions = text_extensions or DEFAULT_TEXT_EXTENSIONS.copy()
        self.include_filenames = include_filenames or DEFAULT_INCLUDE_FILENAMES.copy()
        self.exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS.copy()
        self.include_pdf = include_pdf

        # Add custom extensions if provided
        if custom_extensions:
            self.text_extensions.update(custom_extensions)

        # Add PDF extension if enabled
        if include_pdf:
            self.text_extensions.add(".pdf")

    def _should_exclude_dir(self, dir_name: str) -> bool:
        """Check if a directory should be excluded."""
        # Direct match
        if dir_name in self.exclude_dirs:
            return True
        # Pattern matching for entries with wildcards
        for pattern in self.exclude_dirs:
            if "*" in pattern:
                # Simple glob-like matching
                if pattern.startswith("*") and dir_name.endswith(pattern[1:]):
                    return True
                if pattern.endswith("*") and dir_name.startswith(pattern[:-1]):
                    return True
        return False

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file should be included based on extension or name."""
        # Check exact filename match
        if file_path.name in self.include_filenames:
            return True

        # Check extension
        suffix = file_path.suffix.lower()
        if suffix in self.text_extensions:
            return True

        # Check for files without extension but with known names
        return not suffix and file_path.name in self.include_filenames

    def _is_pdf_file(self, file_path: Path) -> bool:
        """Check if a file is a PDF."""
        return file_path.suffix.lower() == ".pdf"

    def discover_files(self) -> list[Path]:
        """
        Discover all relevant files in the repository.

        Returns:
            List of file paths sorted with README first if present.
        """
        files: list[Path] = []
        readme_file: Path | None = None

        for file_path in self._walk_directory(self.root_path):
            relative_path = file_path.relative_to(self.root_path)

            # Check for README files at root level (README.md, README, README.txt, etc.)
            if (
                file_path.name.lower().startswith("readme")
                and len(relative_path.parts) == 1
            ):
                # Prefer README.md over other README variants
                if readme_file is None or file_path.name.lower() == "readme.md":
                    readme_file = file_path
                else:
                    files.append(file_path)
            elif self._is_text_file(file_path):
                files.append(file_path)

        # Sort files by path for consistent output
        files.sort(key=lambda p: str(p.relative_to(self.root_path)).lower())

        # Ensure README is first if it exists
        if readme_file:
            files.insert(0, readme_file)

        return files

    def _walk_directory(self, directory: Path) -> Iterator[Path]:
        """
        Walk through directory yielding files, respecting exclusions.

        Args:
            directory: Directory to walk.

        Yields:
            File paths.
        """
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    if not self._should_exclude_dir(entry.name):
                        yield from self._walk_directory(entry)
                elif entry.is_file():
                    yield entry
        except PermissionError:
            pass  # Skip directories we can't access

    def get_text_files(self) -> list[Path]:
        """Get all text-based files (excluding PDFs)."""
        return [f for f in self.discover_files() if not self._is_pdf_file(f)]

    def get_pdf_files(self) -> list[Path]:
        """Get all PDF files."""
        if not self.include_pdf:
            return []
        return [f for f in self.discover_files() if self._is_pdf_file(f)]

    def generate_tree(self, max_depth: int | None = None) -> str:
        """
        Generate a tree view of the repository structure.

        Args:
            max_depth: Maximum depth to display (None for unlimited).

        Returns:
            String representation of the directory tree.
        """
        lines: list[str] = [self.root_path.name + "/"]
        self._build_tree(self.root_path, "", lines, 0, max_depth)
        return "\n".join(lines)

    def _build_tree(
        self,
        directory: Path,
        prefix: str,
        lines: list[str],
        current_depth: int,
        max_depth: int | None,
    ) -> None:
        """Recursively build the tree structure."""
        if max_depth is not None and current_depth >= max_depth:
            return

        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        # Filter out excluded directories
        entries = [
            e for e in entries
            if not (e.is_dir() and self._should_exclude_dir(e.name))
        ]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "│   "
                self._build_tree(
                    entry, prefix + extension, lines, current_depth + 1, max_depth
                )
            else:
                # Only show files we would include
                if self._is_text_file(entry) or (self.include_pdf and self._is_pdf_file(entry)):
                    lines.append(f"{prefix}{connector}{entry.name}")
