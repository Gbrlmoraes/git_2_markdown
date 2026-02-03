"""
Text-based file reader module.

Provides functionality to read text files with proper encoding detection.
"""

import mimetypes
from pathlib import Path


# Common encoding fallback order
ENCODING_FALLBACKS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii"]

# Language identifiers for code blocks based on file extension
LANGUAGE_MAP: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".mts": "typescript",
    # Web
    ".html": "html",
    ".htm": "html",
    ".xhtml": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".vue": "vue",
    ".svelte": "svelte",
    # Data formats
    ".json": "json",
    ".jsonl": "json",
    ".json5": "json5",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".xsl": "xml",
    ".xslt": "xml",
    # Shell
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
    # Other languages
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".hh": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
    ".lua": "lua",
    ".pl": "perl",
    ".pm": "perl",
    # Documentation
    ".md": "markdown",
    ".markdown": "markdown",
    ".mdx": "mdx",
    ".rst": "rst",
    ".txt": "text",
    ".text": "text",
    ".adoc": "asciidoc",
    ".asciidoc": "asciidoc",
    # Config
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".env": "dotenv",
    ".properties": "properties",
    # Build/CI
    ".dockerfile": "dockerfile",
    ".makefile": "makefile",
    ".cmake": "cmake",
    ".gradle": "gradle",
    ".tf": "terraform",
    ".tfvars": "terraform",
    # Database/Query
    ".sql": "sql",
    ".graphql": "graphql",
    ".gql": "graphql",
    # Other
    ".proto": "protobuf",
    ".csv": "csv",
    ".tsv": "tsv",
    ".gitignore": "gitignore",
}

# Special filenames without extensions
FILENAME_LANGUAGE_MAP: dict[str, str] = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "Jenkinsfile": "groovy",
    "Vagrantfile": "ruby",
    "Procfile": "yaml",
    "Gemfile": "ruby",
    "Rakefile": "ruby",
    ".gitignore": "gitignore",
    ".gitattributes": "gitattributes",
    ".dockerignore": "dockerignore",
    ".editorconfig": "editorconfig",
}


class TextReader:
    """Reads text-based files with encoding detection."""

    def __init__(self, max_file_size: int | None = None):
        """
        Initialize the text reader.

        Args:
            max_file_size: Maximum file size in bytes to read (None for no limit).
        """
        self.max_file_size = max_file_size

    def read_file(self, file_path: Path) -> str | None:
        """
        Read a text file with automatic encoding detection.

        Args:
            file_path: Path to the file to read.

        Returns:
            File contents as string, or None if the file couldn't be read.
        """
        if not file_path.exists():
            return None

        if not file_path.is_file():
            return None

        # Check file size if limit is set
        if self.max_file_size is not None:
            try:
                if file_path.stat().st_size > self.max_file_size:
                    return f"[File too large: {file_path.stat().st_size} bytes]"
            except OSError:
                return None

        # Try reading with different encodings
        for encoding in ENCODING_FALLBACKS:
            try:
                content = file_path.read_text(encoding=encoding)
                return content
            except (UnicodeDecodeError, UnicodeError):
                continue
            except OSError as e:
                return f"[Error reading file: {e}]"

        # If all encodings fail, try reading as binary and decode with replacement
        try:
            content = file_path.read_bytes().decode("utf-8", errors="replace")
            return content
        except OSError as e:
            return f"[Error reading file: {e}]"

    def get_language_identifier(self, file_path: Path) -> str:
        """
        Get the language identifier for syntax highlighting.

        Args:
            file_path: Path to the file.

        Returns:
            Language identifier string for Markdown code blocks.
        """
        # Check filename first
        if file_path.name in FILENAME_LANGUAGE_MAP:
            return FILENAME_LANGUAGE_MAP[file_path.name]

        # Check extension
        suffix = file_path.suffix.lower()
        if suffix in LANGUAGE_MAP:
            return LANGUAGE_MAP[suffix]

        # Try to guess from mimetype
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if "python" in mime_type:
                return "python"
            if "javascript" in mime_type:
                return "javascript"
            if "json" in mime_type:
                return "json"
            if "xml" in mime_type:
                return "xml"
            if "html" in mime_type:
                return "html"
            if "css" in mime_type:
                return "css"

        # Default to empty string (plain text)
        return ""

    def is_binary(self, file_path: Path, sample_size: int = 8192) -> bool:
        """
        Check if a file appears to be binary.

        Args:
            file_path: Path to the file.
            sample_size: Number of bytes to sample.

        Returns:
            True if the file appears to be binary.
        """
        try:
            with open(file_path, "rb") as f:
                sample = f.read(sample_size)

            # Check for null bytes (common in binary files)
            if b"\x00" in sample:
                return True

            # Try to decode as UTF-8
            try:
                sample.decode("utf-8")
                return False
            except UnicodeDecodeError:
                # Check if it's likely a text file with different encoding
                # by checking the ratio of printable characters
                printable = sum(
                    1 for byte in sample if 32 <= byte <= 126 or byte in (9, 10, 13)
                )
                return printable / len(sample) < 0.7 if sample else False

        except OSError:
            return True
