"""
Core converter that orchestrates the Git to Markdown conversion process.

This module ties together all the other modules to provide a simple API
for converting repositories to Markdown.
"""

from pathlib import Path

from modules.file_discovery import FileDiscovery
from modules.git_handler import GitHandler
from modules.markdown_generator import FileContent, MarkdownGenerator
from modules.pdf_reader import PDFReader
from modules.text_reader import TextReader


class ConverterConfig:
    """Configuration for the Git to Markdown converter."""

    # Default max characters per output file (100k)
    DEFAULT_MAX_CHARS_PER_FILE = 100_000

    def __init__(
        self,
        include_pdf: bool = False,
        include_tree: bool = True,
        include_toc: bool = False,
        max_tree_depth: int | None = None,
        max_file_size: int | None = None,
        custom_extensions: set[str] | None = None,
        exclude_dirs: set[str] | None = None,
        split_output: bool = False,
        max_chars_per_file: int = DEFAULT_MAX_CHARS_PER_FILE,
    ):
        """
        Initialize converter configuration.

        Args:
            include_pdf: Whether to include PDF files (requires Docling).
            include_tree: Whether to include directory tree in output.
            include_toc: Whether to include table of contents.
            max_tree_depth: Maximum depth for directory tree display.
            max_file_size: Maximum file size in bytes to include.
            custom_extensions: Additional file extensions to include.
            exclude_dirs: Additional directories to exclude.
            split_output: Whether to split output into multiple files.
            max_chars_per_file: Maximum characters per output file when splitting.
        """
        self.include_pdf = include_pdf
        self.include_tree = include_tree
        self.include_toc = include_toc
        self.max_tree_depth = max_tree_depth
        self.max_file_size = max_file_size
        self.custom_extensions = custom_extensions
        self.exclude_dirs = exclude_dirs
        self.split_output = split_output
        self.max_chars_per_file = max_chars_per_file


class GitToMarkdownConverter:
    """Main converter class that orchestrates the conversion process."""

    def __init__(self, config: ConverterConfig | None = None):
        """
        Initialize the converter.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or ConverterConfig()
        self._text_reader = TextReader(max_file_size=self.config.max_file_size)
        self._pdf_reader: PDFReader | None = None

        # Initialize PDF reader if needed
        if self.config.include_pdf:
            self._pdf_reader = PDFReader()

    def convert(self, repo_source: str, output_path: Path | str | None = None) -> str:
        """
        Convert a repository to Markdown.

        Args:
            repo_source: Git URL or local path to the repository.
            output_path: Optional path to write the output file.

        Returns:
            The generated Markdown content.
        """
        # Use context manager for automatic cleanup of cloned repos
        with GitHandler(repo_source) as git_handler:
            repo_path = git_handler.repo_path
            repo_name = git_handler.repo_name

            # Discover files
            discovery = FileDiscovery(
                root_path=repo_path,
                include_pdf=self.config.include_pdf,
                custom_extensions=self.config.custom_extensions,
                exclude_dirs=self.config.exclude_dirs,
            )

            # Generate tree
            tree = discovery.generate_tree(max_depth=self.config.max_tree_depth)

            # Get files
            files = discovery.discover_files()

            # Initialize markdown generator
            generator = MarkdownGenerator(
                repo_name=repo_name,
                include_tree=self.config.include_tree,
                include_toc=self.config.include_toc,
                max_tree_depth=self.config.max_tree_depth,
            )
            generator.set_tree(tree)

            # Process files
            for file_path in files:
                relative_path = str(file_path.relative_to(repo_path))
                is_pdf = file_path.suffix.lower() == ".pdf"

                if is_pdf and self._pdf_reader:
                    # Handle PDF file
                    content = self._pdf_reader.read_pdf_safe(file_path)
                    language = "markdown"  # PDF content is exported as markdown
                else:
                    # Handle text file
                    content = self._text_reader.read_file(file_path)
                    if content is None:
                        content = "[Failed to read file]"
                    language = self._text_reader.get_language_identifier(file_path)

                file_content = FileContent(
                    path=file_path,
                    relative_path=relative_path,
                    content=content,
                    language=language,
                    is_pdf=is_pdf,
                )
                generator.add_file(file_content)

            # Generate output
            markdown = generator.generate()

            # Write to file if path provided
            if output_path:
                output_path = Path(output_path)
                if self.config.split_output:
                    self._generated_files = generator.generate_chunked_to_files(
                        output_path, self.config.max_chars_per_file
                    )
                else:
                    generator.generate_to_file(output_path)
                    self._generated_files = [output_path]

            return markdown

    def get_generated_files(self) -> list[Path]:
        """Get the list of generated files from the last conversion."""
        return getattr(self, "_generated_files", [])

    def convert_to_file(self, repo_source: str, output_path: Path | str) -> Path | list[Path]:
        """
        Convert a repository to Markdown and save to a file.

        Args:
            repo_source: Git URL or local path to the repository.
            output_path: Path to write the output file.

        Returns:
            Path to the generated file, or list of paths if split_output is enabled.
        """
        output_path = Path(output_path)
        self.convert(repo_source, output_path)
        return output_path

    def check_pdf_support(self) -> bool:
        """Check if PDF support is available."""
        if self._pdf_reader is None:
            self._pdf_reader = PDFReader()
        return self._pdf_reader.is_available
