import os
from pathlib import Path
from typing import Dict, Iterator, Tuple

from pathspec import GitIgnoreSpec


def load_directory_gitignore_specs(directory: Path) -> Dict[Path, GitIgnoreSpec]:
    """
    Load all ``.gitignore`` files found under ``directory``.

    The returned mapping maps the directory that contains each ``.gitignore``
    file to a ``GitIgnoreSpec`` object (from the ``pathspec`` package).

    Args:
        directory: Root directory to search recursively for ``.gitignore`` files.

    Returns:
        A dict mapping the parent directory of each discovered ``.gitignore``
        file to a ``GitIgnoreSpec`` that can be used to test whether paths
        relative to that directory match ignore patterns.

    Example:
        >>> specs = load_directory_gitignore_specs(Path("/my/repo"))
        >>> repo_root_spec = specs.get(Path('/my/repo'))
        >>> bool(repo_root_spec.match_file('build/'))
    """
    specs = {}

    for gitignore_path in directory.rglob(".gitignore"):
        with gitignore_path.open("r") as f:
            # Each .gitignore file is effective relative to its own directory
            specs[gitignore_path.parent] = GitIgnoreSpec.from_lines(f)

    return specs


def should_path_ignore(path: Path, specs: Dict[Path, GitIgnoreSpec]) -> bool:
    """
    Return True if ``path`` should be ignored by git rules.

    This function checks for two things:
    - If any path component equals ``.git`` the path is considered ignored.
    - For each discovered ``.gitignore`` specification, if the specification
      applies to an ancestor directory of ``path`` then the path is tested
      relative to that ancestor and matched via the spec.

    Args:
        path: A file or directory path to test.
        specs: Mapping from directories (parents of ``.gitignore`` files) to
            their compiled ``GitIgnoreSpec`` objects.

    Returns:
        True if the path should be ignored according to any applicable
        ``.gitignore`` spec or because it is inside a ``.git`` directory.
    """
    if any(part == ".git" for part in path.parts):
        return True

    # Find all applicable .gitignore rules
    for dir_path, spec in specs.items():
        # Only apply when the path is in the .gitignore directory or its subdirectories
        if dir_path not in [*path.parents]:
            continue
        relpath = path.relative_to(dir_path)
        # Check both directory and file
        if spec.match_file(str(relpath)) or (
            path.is_dir() and spec.match_file(f"{relpath}/")
        ):
            return True

    return False


def path_walk(directory: Path) -> Iterator[Tuple[Path, Path, Path]]:
    """
    Lightweight wrapper around ``os.walk`` that yields Path objects.

    Yields tuples ``(root_path, dirs, files)`` where ``root_path`` is a
    ``Path`` instance and ``dirs``/``files`` are lists of ``Path`` objects
    representing the directory entries in that root.

    Args:
        directory: The root directory to walk.

    Yields:
        Tuples of (root_path, dirs, files).
    """
    for root, dirnames, filenames in os.walk(directory):
        root_path = Path(root)
        dirs = [Path(d) for d in dirnames]
        files = [Path(f) for f in filenames]

        yield root_path, dirs, files


def path_walk_respect_gitignore(
    directory: Path,
) -> Iterator[Tuple[Path, Path, Path]]:
    """
    Walk directory tree while applying discovered ``.gitignore`` rules.

    This function behaves like :func:`path_walk` but filters out any files or
    directories that would be ignored according to any ``.gitignore`` files
    found under ``directory``.

    Args:
        directory: Root directory to traverse.

    Yields:
        Tuples of (root_path, dirs, files) where ``dirs`` and ``files`` have
        been filtered to exclude ignored entries.
    """
    specs = load_directory_gitignore_specs(directory)
    for root, dirnames, filenames in os.walk(directory):
        root_path = Path(root)
        dirs = [d for d in dirnames if not should_path_ignore(root_path / d, specs)]
        files = [f for f in filenames if not should_path_ignore(root_path / f, specs)]

        yield root_path, dirs, files


def iter_files_with_respect_gitignore(
    directory: Path, respect_gitignore: bool = False
) -> Iterator[Path]:
    """
    Yield files under ``directory`` recursively, optionally respecting
    ``.gitignore`` rules.

    Args:
        directory: Root directory to iterate.
        respect_gitignore: If True, discovered ``.gitignore`` files are
            respected and ignored files are skipped.

    Yields:
        ``Path`` objects for every file discovered.
    """
    if respect_gitignore:
        walk = path_walk_respect_gitignore
    else:
        walk = path_walk

    for root_path, _, files in walk(directory):
        for f in files:
            yield root_path / f


def iter_dirs_with_respect_gitignore(
    directory: Path, respect_gitignore: bool = False
) -> Iterator[Path]:
    """
    Yield directories under ``directory`` recursively, optionally
    respecting ``.gitignore`` rules.

    Args:
        directory: Root directory to iterate.
        respect_gitignore: If True, discovered ``.gitignore`` files are
            respected and ignored directories are skipped.

    Yields:
        ``Path`` objects for every directory discovered.
    """
    if respect_gitignore:
        walk = path_walk_respect_gitignore
    else:
        walk = path_walk

    for root_path, dirs, _ in walk(directory):
        for d in dirs:
            yield root_path / d


def glob_respect_gitignore(directory: Path, glob: str = "*") -> Iterator[Path]:
    """
    Yield entries matching ``glob`` at top level of ``directory`` while
    skipping those ignored by any applicable ``.gitignore`` files.

    Args:
        directory: Directory to glob in.
        glob: Glob pattern (defaults to "*").

    Yields:
        Paths that match the glob and are not ignored.
    """
    specs = load_directory_gitignore_specs(directory)
    for file in directory.glob(glob):
        if not should_path_ignore(file, specs):
            yield file


def rglob_respect_gitignore(directory: Path, glob: str = "*") -> Iterator[Path]:
    """
    Recursively glob for files under ``directory`` while skipping ignored
    paths according to discovered ``.gitignore`` files.

    Args:
        directory: Root directory to search.
        glob: Glob pattern for recursive search (defaults to "*").

    Yields:
        Matching ``Path`` objects that are not ignored.
    """
    specs = load_directory_gitignore_specs(directory)
    for file in directory.rglob(glob):
        if not should_path_ignore(file, specs):
            yield file
