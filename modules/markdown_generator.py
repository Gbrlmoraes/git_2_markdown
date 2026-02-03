"""
Markdown generation and formatting module.

Provides functionality to generate the final Markdown output from repository contents.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileContent:
    """Represents a file's content and metadata."""

    path: Path
    relative_path: str
    content: str
    language: str
    is_pdf: bool = False


class MarkdownGenerator:
    """Generates Markdown output from repository contents."""

    def __init__(
        self,
        repo_name: str,
        include_tree: bool = True,
        include_toc: bool = False,
        max_tree_depth: int | None = None,
    ):
        """
        Initialize the Markdown generator.

        Args:
            repo_name: Name of the repository.
            include_tree: Whether to include directory tree at the start.
            include_toc: Whether to include a table of contents.
            max_tree_depth: Maximum depth for the directory tree.
        """
        self.repo_name = repo_name
        self.include_tree = include_tree
        self.include_toc = include_toc
        self.max_tree_depth = max_tree_depth
        self._files: list[FileContent] = []
        self._tree: str = ""

    def set_tree(self, tree: str) -> None:
        """Set the directory tree string."""
        self._tree = tree

    def add_file(self, file_content: FileContent) -> None:
        """Add a file to the output."""
        self._files.append(file_content)

    def add_files(self, file_contents: list[FileContent]) -> None:
        """Add multiple files to the output."""
        self._files.extend(file_contents)

    def generate(self) -> str:
        """
        Generate the complete Markdown output.

        Returns:
            Complete Markdown document as a string.
        """
        sections: list[str] = []

        # Title
        sections.append(self._generate_title())

        # Directory tree
        if self.include_tree and self._tree:
            sections.append(self._generate_tree_section())

        # Table of contents (optional)
        if self.include_toc:
            sections.append(self._generate_toc())

        # File contents
        sections.append(self._generate_files_section())

        return "\n\n".join(sections)

    def _generate_title(self) -> str:
        """Generate the document title."""
        return f"# Repository: {self.repo_name}"

    def _generate_tree_section(self) -> str:
        """Generate the directory tree section."""
        lines = [
            "## Repository Structure",
            "",
            "```",
            self._tree,
            "```",
        ]
        return "\n".join(lines)

    def _generate_toc(self) -> str:
        """Generate the table of contents."""
        lines = ["## Table of Contents", ""]

        for file_content in self._files:
            # Create anchor-friendly link
            anchor = self._create_anchor(file_content.relative_path)
            lines.append(f"- [{file_content.relative_path}](#{anchor})")

        return "\n".join(lines)

    def _create_anchor(self, text: str) -> str:
        """Create a Markdown anchor from text."""
        # Convert to lowercase and replace non-alphanumeric chars with hyphens
        anchor = text.lower()
        anchor = "".join(c if c.isalnum() or c == "-" else "-" for c in anchor)
        # Remove consecutive hyphens
        while "--" in anchor:
            anchor = anchor.replace("--", "-")
        # Remove leading/trailing hyphens
        return anchor.strip("-")

    def _generate_files_section(self) -> str:
        """Generate the file contents section."""
        lines = ["## File Contents", ""]

        for file_content in self._files:
            lines.append(self._format_file(file_content))
            lines.append("")  # Empty line between files

        return "\n".join(lines)

    def _format_file(self, file_content: FileContent) -> str:
        """Format a single file for Markdown output."""
        lines = []

        # File header with name and path
        lines.append(f"### {file_content.path.name}")
        lines.append(f"**Path:** `{file_content.relative_path}`")

        # Add PDF indicator if applicable
        if file_content.is_pdf:
            lines.append("**Type:** PDF (extracted text)")

        lines.append("")

        # File content in code block
        lang = file_content.language if file_content.language else ""
        
        # For markdown files, we might want to handle them specially
        # to avoid nested markdown issues
        if file_content.language == "markdown":
            lines.append(f"```{lang}")
            lines.append(file_content.content)
            lines.append("```")
        else:
            lines.append(f"```{lang}")
            lines.append(file_content.content)
            lines.append("```")

        return "\n".join(lines)

    def generate_to_file(self, output_path: Path) -> None:
        """
        Generate and write Markdown to a file.

        Args:
            output_path: Path to write the output file.
        """
        content = self.generate()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    def generate_chunked(self, max_chars: int = 100_000) -> list[str]:
        """
        Generate Markdown output split into chunks.

        Each chunk will not exceed max_chars, and individual files are never
        split across chunks.

        Args:
            max_chars: Maximum characters per chunk (default: 100,000).

        Returns:
            List of Markdown strings, one per chunk.
        """
        chunks: list[str] = []
        current_chunk_parts: list[str] = []
        current_chunk_size = 0

        # Generate header (title + tree + toc) - included in first chunk only
        header_parts: list[str] = []
        header_parts.append(self._generate_title())
        if self.include_tree and self._tree:
            header_parts.append(self._generate_tree_section())
        if self.include_toc:
            header_parts.append(self._generate_toc())

        header = "\n\n".join(header_parts)
        header_with_section = header + "\n\n## File Contents\n"

        current_chunk_parts.append(header_with_section)
        current_chunk_size = len(header_with_section)

        # Process each file
        for file_content in self._files:
            file_markdown = self._format_file(file_content) + "\n"
            file_size = len(file_markdown)

            # Check if adding this file would exceed the limit
            if current_chunk_size + file_size > max_chars and current_chunk_parts:
                # Save current chunk (if it has more than just the header)
                if len(current_chunk_parts) > 1 or current_chunk_size > len(header_with_section):
                    chunks.append("\n".join(current_chunk_parts))

                # Start new chunk with continuation header
                continuation_header = f"# Repository: {self.repo_name} (continued)\n\n## File Contents (continued)\n"
                current_chunk_parts = [continuation_header]
                current_chunk_size = len(continuation_header)

            current_chunk_parts.append(file_markdown)
            current_chunk_size += file_size

        # Add the last chunk if it has content
        if current_chunk_parts:
            chunks.append("\n".join(current_chunk_parts))

        return chunks

    def generate_chunked_to_files(
        self, output_path: Path, max_chars: int = 100_000
    ) -> list[Path]:
        """
        Generate chunked Markdown and write to multiple files.

        Files are named: base_name_part1.md, base_name_part2.md, etc.
        If only one chunk, uses the original filename.

        Args:
            output_path: Base path for output files.
            max_chars: Maximum characters per chunk.

        Returns:
            List of paths to generated files.
        """
        chunks = self.generate_chunked(max_chars)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if len(chunks) == 1:
            # Single file - use original name
            output_path.write_text(chunks[0], encoding="utf-8")
            return [output_path]

        # Multiple files - add part numbers
        stem = output_path.stem
        suffix = output_path.suffix
        parent = output_path.parent

        generated_files: list[Path] = []
        for i, chunk in enumerate(chunks, start=1):
            part_path = parent / f"{stem}_part{i}{suffix}"
            part_path.write_text(chunk, encoding="utf-8")
            generated_files.append(part_path)

        return generated_files

    def get_file_count(self) -> int:
        """Get the number of files added."""
        return len(self._files)

    def get_total_size(self) -> int:
        """Get the total size of all file contents."""
        return sum(len(f.content) for f in self._files)
