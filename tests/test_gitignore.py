from pathlib import Path

import pytest

from chaos_utils import gitignore


@pytest.fixture
def temp_gitignore_tree(tmp_path):
    """
    Create a directory tree with .gitignore files for testing.

    Structure:
    tmp/
      .gitignore (ignores foo/)
      foo/
        bar.txt
      baz.txt
      sub/
        .gitignore (ignores *.log)
        keep.txt
        ignore.log
    """
    root = tmp_path
    (root / ".gitignore").write_text("foo/\n")
    (root / "foo").mkdir()
    (root / "foo" / "bar.txt").write_text("bar")
    (root / "baz.txt").write_text("baz")
    (root / "sub").mkdir()
    (root / "sub" / ".gitignore").write_text("*.log\n")
    (root / "sub" / "keep.txt").write_text("keep")
    (root / "sub" / "ignore.log").write_text("log")
    return root


def test_load_directory_gitignore_specs(temp_gitignore_tree):
    """
    Test loading .gitignore specs from directory tree.
    """
    specs = gitignore.load_directory_gitignore_specs(temp_gitignore_tree)
    assert temp_gitignore_tree in specs
    assert temp_gitignore_tree / "sub" in specs
    assert specs[temp_gitignore_tree].match_file("foo/")
    assert specs[temp_gitignore_tree / "sub"].match_file("ignore.log")


def test_should_path_ignore(temp_gitignore_tree):
    """
    Test if should_path_ignore correctly determines ignored paths.
    """
    specs = gitignore.load_directory_gitignore_specs(temp_gitignore_tree)
    # foo/ should be ignored
    assert gitignore.should_path_ignore(temp_gitignore_tree / "foo", specs)
    assert gitignore.should_path_ignore(temp_gitignore_tree / "foo" / "bar.txt", specs)
    # baz.txt should not be ignored
    assert not gitignore.should_path_ignore(temp_gitignore_tree / "baz.txt", specs)
    # sub/ignore.log should be ignored
    assert gitignore.should_path_ignore(
        temp_gitignore_tree / "sub" / "ignore.log", specs
    )
    # sub/keep.txt should not be ignored
    assert not gitignore.should_path_ignore(
        temp_gitignore_tree / "sub" / "keep.txt", specs
    )
    # .git are always be ignored
    assert gitignore.should_path_ignore(temp_gitignore_tree / ".git", specs)


def test_path_walk_and_respect_gitignore(temp_gitignore_tree):
    """
    Test path_walk and path_walk_respect_gitignore functions.
    """
    # path_walk without respect gitignore
    all_files = set()
    for root, dirs, files in gitignore.path_walk(temp_gitignore_tree):
        for f in files:
            all_files.add((root / f).relative_to(temp_gitignore_tree))
    assert Path("foo/bar.txt") in all_files
    assert Path("baz.txt") in all_files
    assert Path("sub/ignore.log") in all_files

    # path_walk_respect_gitignore should ignore foo/ and ignore.log
    all_files = set()
    for root, dirs, files in gitignore.path_walk_respect_gitignore(temp_gitignore_tree):
        for f in files:
            all_files.add((root / f).relative_to(temp_gitignore_tree))
    assert Path("baz.txt") in all_files
    assert Path("sub/keep.txt") in all_files
    assert Path("foo/bar.txt") not in all_files
    assert Path("sub/ignore.log") not in all_files


def test_iter_files_with_respect_gitignore(temp_gitignore_tree):
    """
    Test iter_files_with_respect_gitignore with and without gitignore respect.
    """
    # without respect gitignore
    files = set(
        p.relative_to(temp_gitignore_tree)
        for p in gitignore.iter_files_with_respect_gitignore(temp_gitignore_tree)
    )
    assert Path("foo/bar.txt") in files
    assert Path("sub/ignore.log") in files
    # respect gitignore
    files = set(
        p.relative_to(temp_gitignore_tree)
        for p in gitignore.iter_files_with_respect_gitignore(temp_gitignore_tree, True)
    )
    assert Path("foo/bar.txt") not in files
    assert Path("sub/ignore.log") not in files
    assert Path("baz.txt") in files
    assert Path("sub/keep.txt") in files


def test_iter_dirs_with_respect_gitignore(temp_gitignore_tree):
    """
    Test iter_dirs_with_respect_gitignore with and without gitignore respect.
    """
    # without respect gitignore
    dirs = set(
        p.relative_to(temp_gitignore_tree)
        for p in gitignore.iter_dirs_with_respect_gitignore(temp_gitignore_tree)
    )
    assert Path("foo") in dirs
    assert Path("sub") in dirs
    # respect gitignore
    dirs = set(
        p.relative_to(temp_gitignore_tree)
        for p in gitignore.iter_dirs_with_respect_gitignore(temp_gitignore_tree, True)
    )
    assert Path("foo") not in dirs
    assert Path("sub") in dirs


def test_glob_and_rglob_respect_gitignore(temp_gitignore_tree):
    """
    Test glob_respect_gitignore and rglob_respect_gitignore functions.
    """
    # glob_respect_gitignore
    files = set(
        p.name for p in gitignore.glob_respect_gitignore(temp_gitignore_tree, "*.txt")
    )
    assert "baz.txt" in files
    assert "foo" not in files
    # rglob_respect_gitignore
    files = set(
        p.relative_to(temp_gitignore_tree)
        for p in gitignore.rglob_respect_gitignore(temp_gitignore_tree, "*.txt")
    )
    assert Path("baz.txt") in files
    assert Path("sub/keep.txt") in files
    assert Path("foo/bar.txt") not in files
