"""
PDF reader module using Docling.

This module is optional and requires the 'pdf' extra to be installed.
Provides functionality to extract text content from PDF files.
"""

from pathlib import Path
from typing import TYPE_CHECKING

# Lazy import for optional dependency
if TYPE_CHECKING:
    from docling.document_converter import DocumentConverter


class PDFReaderError(Exception):
    """Exception raised when PDF reading fails."""

    pass


class PDFReader:
    """Reads PDF files using Docling for text extraction."""

    def __init__(self):
        """Initialize the PDF reader."""
        self._converter: "DocumentConverter | None" = None
        self._available: bool | None = None

    @property
    def is_available(self) -> bool:
        """Check if PDF reading is available (Docling is installed)."""
        if self._available is None:
            import importlib.util

            self._available = importlib.util.find_spec("docling") is not None
        return self._available

    def _get_converter(self) -> "DocumentConverter":
        """Get or create the document converter."""
        if not self.is_available:
            raise PDFReaderError(
                "Docling is not installed. Install with: uv pip install 'git-2-markdown[pdf]'"
            )

        if self._converter is None:
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()

        return self._converter

    def read_pdf(self, file_path: Path) -> str | None:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text content, or None if extraction failed.

        Raises:
            PDFReaderError: If Docling is not available or extraction fails.
        """
        if not file_path.exists():
            return None

        if not file_path.is_file():
            return None

        if file_path.suffix.lower() != ".pdf":
            return None

        try:
            converter = self._get_converter()
            result = converter.convert(str(file_path))

            # Export to markdown format for consistent output
            markdown_content = result.document.export_to_markdown()
            return markdown_content

        except ImportError as e:
            raise PDFReaderError(
                "Docling is not installed. Install with: uv pip install 'git-2-markdown[pdf]'"
            ) from e
        except Exception as e:
            raise PDFReaderError(f"Failed to extract PDF content: {e}") from e

    def read_pdf_safe(self, file_path: Path) -> str:
        """
        Safely extract text content from a PDF file.

        Unlike read_pdf(), this method never raises exceptions and returns
        an error message string on failure.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text content or an error message.
        """
        try:
            content = self.read_pdf(file_path)
            if content is None:
                return "[Failed to read PDF file]"
            return content
        except PDFReaderError as e:
            return f"[PDF extraction error: {e}]"
        except Exception as e:
            return f"[Unexpected error reading PDF: {e}]"
