"""
Git to Markdown - Convert Git repositories to LLM-friendly Markdown files.

This package provides modular components for:
- Cloning and handling Git repositories
- Discovering and filtering files
- Reading text-based files
- Optional PDF extraction using Docling
- Generating formatted Markdown output
"""

from modules.converter import ConverterConfig, GitToMarkdownConverter
from modules.file_discovery import FileDiscovery
from modules.git_handler import GitHandler
from modules.markdown_generator import FileContent, MarkdownGenerator
from modules.pdf_reader import PDFReader, PDFReaderError
from modules.text_reader import TextReader

__all__ = [
    "GitHandler",
    "FileDiscovery",
    "TextReader",
    "PDFReader",
    "PDFReaderError",
    "MarkdownGenerator",
    "FileContent",
    "GitToMarkdownConverter",
    "ConverterConfig",
]
