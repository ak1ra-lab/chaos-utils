import os
from pathlib import Path
from typing import Dict, Iterator, Tuple

from pathspec import GitIgnoreSpec


def load_directory_gitignore_specs(directory: Path) -> Dict[Path, GitIgnoreSpec]:
    """Recursively load all .gitignore files and return a mapping of paths to GitIgnoreSpec"""
    specs = {}

    for gitignore_path in directory.rglob(".gitignore"):
        with gitignore_path.open("r") as f:
            # Each .gitignore file is effective relative to its own directory
            specs[gitignore_path.parent] = GitIgnoreSpec.from_lines(f)

    return specs


def should_path_ignore(path: Path, specs: Dict[Path, GitIgnoreSpec]) -> bool:
    """Checks if a path should be ignored"""
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
    for root, dirnames, filenames in os.walk(directory):
        root_path = Path(root)
        dirs = [Path(d) for d in dirnames]
        files = [Path(f) for f in filenames]

        yield root_path, dirs, files


def path_walk_respect_gitignore(
    directory: Path,
) -> Iterator[Tuple[Path, Path, Path]]:
    """Recursively traverse directories, respecting all levels of .gitignore files"""
    specs = load_directory_gitignore_specs(directory)
    for root, dirnames, filenames in os.walk(directory):
        root_path = Path(root)
        dirs = [d for d in dirnames if not should_path_ignore(root_path / d, specs)]
        files = [f for f in filenames if not should_path_ignore(root_path / f, specs)]

        yield root_path, dirs, files


def iter_files_with_respect_gitignore(
    directory: Path, respect_gitignore: bool = False
) -> Iterator[Path]:
    """Generator that yields all files in a directory recursively, with options."""
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
    """Generator that yields all dirs in a directory recursively, with options."""
    if respect_gitignore:
        walk = path_walk_respect_gitignore
    else:
        walk = path_walk

    for root_path, dirs, _ in walk(directory):
        for d in dirs:
            yield root_path / d


def glob_respect_gitignore(directory: Path, glob: str = "*") -> Iterator[Path]:
    specs = load_directory_gitignore_specs(directory)
    for file in directory.glob(glob):
        if not should_path_ignore(file, specs):
            yield file


def rglob_respect_gitignore(directory: Path, glob: str = "*") -> Iterator[Path]:
    specs = load_directory_gitignore_specs(directory)
    for file in directory.rglob(glob):
        if not should_path_ignore(file, specs):
            yield file
