#!/usr/bin/env python3
"""
Git to Markdown Converter

A command-line tool that converts Git repositories into a single Markdown file
suitable for LLM consumption.

Usage:
    git-2-markdown <repo_url_or_path> [options]

Examples:
    git-2-markdown https://github.com/user/repo
    git-2-markdown ./local-repo -o output.md
    git-2-markdown https://github.com/user/repo --include-pdf
"""

import argparse
import sys
from pathlib import Path

from modules.converter import ConverterConfig, GitToMarkdownConverter


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="git-2-markdown",
        description="Convert a Git repository to a single Markdown file for LLM consumption.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://github.com/user/repo
  %(prog)s ./local-repo -o output.md
  %(prog)s https://github.com/user/repo --include-pdf --max-depth 3
  %(prog)s ./project --extensions .jsx .tsx --exclude-dirs tests docs
        """,
    )

    parser.add_argument(
        "repository",
        nargs="?",  # Make optional to allow --check-pdf without repo
        help="Git repository URL or local path to convert",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: <repo_name>.md in current directory)",
    )

    parser.add_argument(
        "--include-pdf",
        action="store_true",
        help="Include PDF files using Docling for text extraction (requires 'pdf' extra)",
    )

    parser.add_argument(
        "--no-tree",
        action="store_true",
        help="Exclude the directory tree from output",
    )

    parser.add_argument(
        "--include-toc",
        action="store_true",
        help="Include a table of contents",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum depth for directory tree display",
    )

    parser.add_argument(
        "--max-file-size",
        type=int,
        default=None,
        help="Maximum file size in bytes to include (skip larger files)",
    )

    parser.add_argument(
        "--extensions",
        nargs="+",
        default=None,
        help="Additional file extensions to include (e.g., .jsx .tsx)",
    )

    parser.add_argument(
        "--exclude-dirs",
        nargs="+",
        default=None,
        help="Additional directories to exclude",
    )

    parser.add_argument(
        "--split",
        action="store_true",
        help="Split output into multiple files based on character limit",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=100_000,
        help="Maximum characters per output file when using --split (default: 100000)",
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write output to stdout instead of a file",
    )

    parser.add_argument(
        "--check-pdf",
        action="store_true",
        help="Check if PDF support is available and exit",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def main(args: list[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command-line arguments (uses sys.argv if None).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Check PDF support if requested
    if parsed_args.check_pdf:
        converter = GitToMarkdownConverter()
        if converter.check_pdf_support():
            print("✓ PDF support is available (Docling is installed)")
            return 0
        else:
            print("✗ PDF support is NOT available")
            print("  Install with: uv pip install 'git-2-markdown[pdf]'")
            return 1

    # Validate repository argument
    if not parsed_args.repository:
        parser.print_help()
        return 1

    # Prepare custom extensions
    custom_extensions = None
    if parsed_args.extensions:
        custom_extensions = set()
        for ext in parsed_args.extensions:
            # Ensure extensions start with a dot
            if not ext.startswith("."):
                ext = "." + ext
            custom_extensions.add(ext)

    # Prepare exclude dirs
    exclude_dirs = None
    if parsed_args.exclude_dirs:
        exclude_dirs = set(parsed_args.exclude_dirs)

    # Create configuration
    config = ConverterConfig(
        include_pdf=parsed_args.include_pdf,
        include_tree=not parsed_args.no_tree,
        include_toc=parsed_args.include_toc,
        max_tree_depth=parsed_args.max_depth,
        max_file_size=parsed_args.max_file_size,
        custom_extensions=custom_extensions,
        exclude_dirs=exclude_dirs,
        split_output=parsed_args.split,
        max_chars_per_file=parsed_args.max_chars,
    )

    # Check PDF support if requested
    if config.include_pdf:
        converter = GitToMarkdownConverter(config)
        if not converter.check_pdf_support():
            print(
                "Warning: PDF support requested but Docling is not installed.",
                file=sys.stderr,
            )
            print(
                "  Install with: uv pip install 'git-2-markdown[pdf]'",
                file=sys.stderr,
            )
            print("  Continuing without PDF support...", file=sys.stderr)
            config.include_pdf = False

    # Create converter
    converter = GitToMarkdownConverter(config)

    try:
        if parsed_args.verbose:
            print(f"Processing repository: {parsed_args.repository}", file=sys.stderr)

        # Determine output path
        if parsed_args.stdout:
            output_path = None
        elif parsed_args.output:
            output_path = parsed_args.output
        else:
            # Generate default output filename
            from modules.git_handler import GitHandler

            handler = GitHandler(parsed_args.repository)
            output_path = Path.cwd() / f"{handler.repo_name}.md"

        # Convert
        markdown = converter.convert(parsed_args.repository, output_path)

        if parsed_args.stdout:
            # Handle encoding for stdout (especially on Windows)
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            print(markdown)
        else:
            generated_files = converter.get_generated_files()
            if parsed_args.verbose:
                if len(generated_files) > 1:
                    print(f"Output split into {len(generated_files)} files:", file=sys.stderr)
                    for f in generated_files:
                        print(f"  - {f}", file=sys.stderr)
                else:
                    print(f"Output written to: {output_path}", file=sys.stderr)
            else:
                if len(generated_files) > 1:
                    print(f"Generated {len(generated_files)} files:")
                    for f in generated_files:
                        print(f"  - {f}")
                else:
                    print(f"Generated: {output_path}")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if parsed_args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
