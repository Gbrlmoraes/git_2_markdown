"""
Git repository handling module.

Provides functionality to clone remote repositories or use local repositories.
"""

import contextlib
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError


class GitHandler:
    """Handles Git repository operations including cloning and validation."""

    def __init__(self, repo_source: str, temp_dir: Path | None = None):
        """
        Initialize the Git handler.

        Args:
            repo_source: Either a Git URL or a local path to a repository.
            temp_dir: Optional custom temporary directory for cloning.
        """
        self.repo_source = repo_source
        self.temp_dir = temp_dir
        self._repo: Repo | None = None
        self._cloned_path: Path | None = None
        self._is_temp: bool = False

    @property
    def repo_path(self) -> Path:
        """Get the path to the repository."""
        if self._cloned_path is None:
            raise ValueError("Repository has not been loaded yet. Call load() first.")
        return self._cloned_path

    @property
    def repo_name(self) -> str:
        """Extract repository name from the source."""
        if self._is_url(self.repo_source):
            parsed = urlparse(self.repo_source)
            name = Path(parsed.path).stem
            # Handle .git suffix
            if name.endswith(".git"):
                name = name[:-4]
            return name or "repository"
        # For local paths, resolve to get the actual directory name
        path = Path(self.repo_source).resolve()
        return path.name or "repository"

    def _is_url(self, source: str) -> bool:
        """Check if the source is a URL."""
        parsed = urlparse(source)
        return parsed.scheme in ("http", "https", "git", "ssh") or source.startswith(
            "git@"
        )

    def load(self) -> Path:
        """
        Load the repository - either clone from URL or validate local path.

        Returns:
            Path to the repository root.

        Raises:
            ValueError: If the source is invalid.
            GitCommandError: If cloning fails.
        """
        if self._is_url(self.repo_source):
            return self._clone_repository()
        return self._load_local_repository()

    def _clone_repository(self) -> Path:
        """Clone a remote repository to a temporary directory."""
        if self.temp_dir:
            clone_path = self.temp_dir / self.repo_name
            clone_path.mkdir(parents=True, exist_ok=True)
        else:
            self._temp_base = tempfile.mkdtemp(prefix="git2md_")
            clone_path = Path(self._temp_base) / self.repo_name
            self._is_temp = True

        try:
            self._repo = Repo.clone_from(
                self.repo_source,
                clone_path,
                depth=1,  # Shallow clone for efficiency
            )
            self._cloned_path = clone_path
            return self._cloned_path
        except GitCommandError as e:
            self.cleanup()
            raise ValueError(f"Failed to clone repository: {e}") from e

    def _load_local_repository(self) -> Path:
        """Load and validate a local repository."""
        local_path = Path(self.repo_source).resolve()

        if not local_path.exists():
            raise ValueError(f"Path does not exist: {local_path}")

        if not local_path.is_dir():
            raise ValueError(f"Path is not a directory: {local_path}")

        # Check if it's a valid Git repository
        try:
            self._repo = Repo(local_path)
            self._cloned_path = local_path
            return self._cloned_path
        except InvalidGitRepositoryError:
            # Allow non-Git directories too (just a folder with files)
            self._cloned_path = local_path
            return self._cloned_path

    def cleanup(self) -> None:
        """Clean up temporary resources."""
        if self._is_temp and hasattr(self, "_temp_base"):
            with contextlib.suppress(Exception):
                shutil.rmtree(self._temp_base, ignore_errors=True)

    def __enter__(self) -> "GitHandler":
        """Context manager entry."""
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()
