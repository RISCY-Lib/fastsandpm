####################################################################################################
# FastSandPM is a package management and dependency resolution tool for HDL Design and DV projects
# Copyright (C) 2026, Benjamin Davis
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <https://www.gnu.org/licenses/>.
####################################################################################################
"""Git utility functions for repository operations.

This module provides wrapper functions around git commands for cloning,
checking out, fetching, and querying git repositories. These utilities
are used internally by the library controller to manage library dependencies.
"""

from __future__ import annotations

import pathlib
import subprocess


def clone(remote: str, dest: pathlib.Path) -> None:
    """Clone a git repository from a remote URL to a local destination.

    Args:
        remote: The URL of the remote repository to clone.
        dest: The local path where the repository will be cloned.

    Raises:
        subprocess.CalledProcessError: If the git clone command fails.
    """
    subprocess.check_output(["git", "clone", remote, dest], stderr=subprocess.STDOUT)


def checkout(commitish: str, repo: pathlib.Path) -> None:
    """Checkout a specific commit, branch, or tag in a repository.

    Args:
        commitish: The commit SHA, branch name, or tag to checkout.
        repo: The path to the local git repository.

    Raises:
        subprocess.CalledProcessError: If the git checkout command fails.
    """
    subprocess.check_output(["git", "checkout", commitish], cwd=repo, stderr=subprocess.STDOUT)


def fetch(repo: pathlib.Path) -> None:
    """Fetch updates from the remote repository.

    Args:
        repo: The path to the local git repository.

    Raises:
        subprocess.CalledProcessError: If the git fetch command fails.
    """
    subprocess.check_output(["git", "fetch"], cwd=repo, stderr=subprocess.STDOUT)


def is_dirty(repo: pathlib.Path) -> bool:
    """Check if a repository has uncommitted changes.

    This checks both staged changes (diff-index) and unstaged changes
    (diff-files) to determine if the working directory is dirty.

    Args:
        repo: The path to the local git repository.

    Returns:
        True if the repository has uncommitted changes, False otherwise.
    """
    proc = subprocess.run(
        ["git", "diff-index", "--quiet", "HEAD", "--"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return True

    proc = subprocess.run(
        ["git", "diff-files", "--quiet"], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    if proc.returncode != 0 or len(proc.stdout) != 0:
        return True

    return False


def remote_exists(remote: str) -> bool:
    """Check if a remote repository URL is accessible.

    Args:
        remote: The URL of the remote repository to check.

    Returns:
        True if the remote repository exists and is accessible, False otherwise.
    """
    proc = subprocess.run(
        ["git", "ls-remote", remote], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return proc.returncode == 0


def get_available_tags(remote: str) -> list[str]:
    """Get all available tags from a repository.

    Args:
        remote: The URL of the remote repository.

    Returns:
        List of tag names from the repository.

    Raises:
        ValueError: If the remote repository cannot be found.
    """
    proc = subprocess.run(
        ["git", "ls-remote", "--tags", remote],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )

    if proc.returncode != 0:
        raise ValueError(f"Could not access remote {remote}")

    tags = []
    for line in proc.stdout.decode("utf-8").split("\n"):
        if line.strip():
            # Parse lines like: "abc123 refs/tags/v1.2.3"
            parts = line.split("\t")
            if len(parts) == 2:
                ref = parts[1]
                if ref.startswith("refs/tags/"):
                    tag_name = ref[10:]  # Remove 'refs/tags/' prefix
                    # Skip tags that end with ^{} (annotated tag references)
                    if not tag_name.endswith("^{}"):
                        tags.append(tag_name)
    return tags


def is_git_repo(path: pathlib.Path) -> bool:
    """Check if a path is a git repository.

    Args:
        path: The path to check.

    Returns:
        True if the path is a git repository, False otherwise.
    """
    proc = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def get_head_commit(repo: pathlib.Path) -> str | None:
    """Get the HEAD commit hash of a repository.

    Args:
        repo: The path to the local git repository.

    Returns:
        The full commit hash of HEAD, or None if the repository has no commits.
    """
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8").strip()


def get_current_branch(repo: pathlib.Path) -> str | None:
    """Get the current branch name of a repository.

    Args:
        repo: The path to the local git repository.

    Returns:
        The current branch name, or None if in detached HEAD state.
    """
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    branch = proc.stdout.decode("utf-8").strip()
    # When in detached HEAD state, git returns "HEAD"
    if branch == "HEAD":
        return None
    return branch


def get_tags_at_head(repo: pathlib.Path) -> list[str]:
    """Get all tags pointing to HEAD commit.

    Args:
        repo: The path to the local git repository.

    Returns:
        List of tag names pointing to HEAD.
    """
    proc = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return []
    output = proc.stdout.decode("utf-8").strip()
    if not output:
        return []
    return output.split("\n")


def get_remote_url(repo: pathlib.Path, remote_name: str = "origin") -> str | None:
    """Get the URL of a remote.

    Args:
        repo: The path to the local git repository.
        remote_name: The name of the remote (default: "origin").

    Returns:
        The URL of the remote, or None if the remote doesn't exist.
    """
    proc = subprocess.run(
        ["git", "remote", "get-url", remote_name],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8").strip()


def get_remote_file(remote: str, treeish: str, path: str) -> bytes:
    """Get a file from a remote repository.

    Args:
        remote: The remote repository URL.
        treeish: The commit, branch, or tag get the file from.
        path: The path of the file in the repository.

    Returns:
        The contents of the file.

    Raises:
        ValueError: If the file cannot be fetched from the remote repository.
    """
    proc = subprocess.run(
        f"git archive --remote={remote} {treeish} {path} | tar xO",
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )

    if proc.returncode != 0:
        raise ValueError(f"Could not fetch file {path} from remote {remote}")

    return proc.stdout


def get_remote_refs(remote: str) -> dict[str, tuple[set[str], set[str]]]:
    """Get all refs (branches and tags) from a remote repository grouped by commit hash.

    Args:
        remote: The URL of the remote repository.

    Returns:
        A dictionary mapping commit hashes to tuples of (branches, tags) that point to that commit.

    Raises:
        ValueError: If the remote repository cannot be accessed.
    """
    proc = subprocess.run(
        ["git", "ls-remote", remote],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )

    if proc.returncode != 0:
        raise ValueError(f"Could not access remote {remote}")

    # Maps commit_hash -> (set of branches, set of tags)
    refs: dict[str, tuple[set[str], set[str]]] = {}

    for line in proc.stdout.decode("utf-8").split("\n"):
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) != 2:
            continue

        commit_hash, ref = parts

        # Skip annotated tag references (ending with ^{})
        if ref.endswith("^{}"):
            continue

        if commit_hash not in refs:
            refs[commit_hash] = (set(), set())

        branches, tags = refs[commit_hash]

        if ref.startswith("refs/heads/"):
            branch_name = ref[11:]  # Remove 'refs/heads/' prefix
            branches.add(branch_name)
        elif ref.startswith("refs/tags/"):
            tag_name = ref[10:]  # Remove 'refs/tags/' prefix
            tags.add(tag_name)

    return refs


def get_commit_for_ref(remote: str, ref: str) -> str | None:
    """Get the commit hash for a specific ref (branch or tag) from a remote repository.

    Args:
        remote: The URL of the remote repository.
        ref: The ref name (branch or tag) to look up.

    Returns:
        The commit hash for the ref, or None if the ref doesn't exist.
    """
    proc = subprocess.run(
        ["git", "ls-remote", remote, ref],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
    )

    if proc.returncode != 0:
        return None

    output = proc.stdout.decode("utf-8").strip()
    if not output:
        return None

    # Parse "commit_hash\trefs/..."
    parts = output.split("\t")
    if parts:
        return parts[0]

    return None
