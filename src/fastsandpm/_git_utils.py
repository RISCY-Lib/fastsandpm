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

import logging
import pathlib
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

_logger = logging.getLogger(__name__)


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

    Uses `git archive` to fetch a single file from a remote repository without
    cloning the entire repository. This is significantly faster than a full clone
    when only a single file is needed.

    Note:
        This function requires the remote git server to support `git archive --remote`.
        Some hosting services (notably GitHub) do not support this protocol.
        For those services, a full clone or HTTP API fallback may be necessary.

    Args:
        remote: The remote repository URL.
        treeish: The commit, branch, or tag to get the file from.
        path: The path of the file in the repository.

    Returns:
        The contents of the file as bytes.

    Raises:
        ValueError: If the file cannot be fetched from the remote repository.
    """
    if file := fetch_file_from_hosting_api(remote, treeish, path):
        return file

    # Use shell=True to enable piping between git archive and tar
    proc = subprocess.run(
        f"git archive --remote={remote} {treeish} -- {path} | tar -xO",
        shell=True,
        capture_output=True,
    )

    if proc.returncode != 0:
        raise ValueError(f"Could not fetch file {path} from remote {remote}")

    return proc.stdout


@lru_cache(maxsize=128)
def get_remote_refs(remote: str) -> dict[str, tuple[frozenset[str], frozenset[str]]]:
    """Get all refs (branches and tags) from a remote repository grouped by commit hash.

    Results are cached to avoid repeated network calls to the same remote during
    dependency resolution. Use `get_remote_refs.cache_clear()` to invalidate the cache.

    Args:
        remote: The URL of the remote repository.

    Returns:
        A dictionary mapping commit hashes to tuples of (branches, tags) that point to
        that commit. Uses frozensets for hashability/cacheability.

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
    # Use mutable sets during construction, convert to frozensets at the end
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

    # Convert to frozensets for immutability and cacheability
    return {
        commit: (frozenset(branches), frozenset(tags)) for commit, (branches, tags) in refs.items()
    }


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


def parse_github_url(remote: str) -> tuple[str, str] | None:
    """Parse a GitHub remote URL to extract owner and repo name.

    Supports various GitHub URL formats:
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    - ssh://git@github.com/owner/repo.git

    Args:
        remote: The git remote URL.

    Returns:
        A tuple of (owner, repo) if the URL is a GitHub URL, None otherwise.
    """
    # HTTPS format: https://github.com/owner/repo.git or https://github.com/owner/repo
    https_match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", remote)
    if https_match:
        return (https_match.group(1), https_match.group(2))

    # SSH format: git@github.com:owner/repo.git
    ssh_match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", remote)
    if ssh_match:
        return (ssh_match.group(1), ssh_match.group(2))

    # SSH URL format: ssh://git@github.com/owner/repo.git
    ssh_url_match = re.match(r"ssh://git@github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", remote)
    if ssh_url_match:
        return (ssh_url_match.group(1), ssh_url_match.group(2))

    return None


def parse_gitlab_url(remote: str) -> tuple[str, str] | None:
    """Parse a GitLab remote URL to extract the project path.

    Supports various GitLab URL formats:
    - https://gitlab.com/owner/repo.git
    - https://gitlab.com/group/subgroup/repo.git
    - git@gitlab.com:owner/repo.git
    - ssh://git@gitlab.com/owner/repo.git

    Args:
        remote: The git remote URL.

    Returns:
        A tuple of (host, project_path) if the URL is a GitLab URL, None otherwise.
        The project_path may contain slashes for nested groups.
    """
    # HTTPS format: https://gitlab.com/owner/repo.git or with subgroups
    https_match = re.match(r"https?://(gitlab\.[^/]+)/(.+?)(?:\.git)?/?$", remote)
    if https_match:
        return (https_match.group(1), https_match.group(2))

    # SSH format: git@gitlab.com:owner/repo.git
    ssh_match = re.match(r"git@(gitlab\.[^:]+):(.+?)(?:\.git)?$", remote)
    if ssh_match:
        return (ssh_match.group(1), ssh_match.group(2))

    # SSH URL format: ssh://git@gitlab.com/owner/repo.git
    ssh_url_match = re.match(r"ssh://git@(gitlab\.[^/]+)/(.+?)(?:\.git)?/?$", remote)
    if ssh_url_match:
        return (ssh_url_match.group(1), ssh_url_match.group(2))

    return None


def fetch_file_from_github(owner: str, repo: str, commit: str, filepath: str) -> bytes | None:
    """Fetch a file from GitHub using the raw content URL.

    Args:
        owner: The repository owner.
        repo: The repository name.
        commit: The commit hash.
        filepath: The path to the file in the repository.

    Returns:
        The file contents as bytes, or None if fetching fails.
    """
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit}/{filepath}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            result: bytes = response.read()
            return result
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        _logger.warning(f"Failed to fetch file from GitHub ({url}): {e}")
        return None


def fetch_file_from_gitlab(
    host: str, project_path: str, commit: str, filepath: str
) -> bytes | None:
    """Fetch a file from GitLab using the repository files API.

    Args:
        host: The GitLab host (e.g., "gitlab.com").
        project_path: The project path (e.g., "owner/repo" or "group/subgroup/repo").
        commit: The commit hash.
        filepath: The path to the file in the repository.

    Returns:
        The file contents as bytes, or None if fetching fails.
    """
    # URL-encode the project path (slashes become %2F)
    encoded_project = urllib.parse.quote(project_path, safe="")
    # URL-encode the filepath
    encoded_filepath = urllib.parse.quote(filepath, safe="")
    url = f"https://{host}/api/v4/projects/{encoded_project}/repository/files/{encoded_filepath}/raw?ref={commit}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            result: bytes = response.read()
            return result
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        _logger.warning(f"Failed to fetch file from GitLab ({url}): {e}")
        return None


def fetch_file_from_hosting_api(remote: str, commit: str, filepath: str) -> bytes | None:
    """Try to fetch a file from a remote repository using hosting provider REST APIs.

    This is faster than a full git clone as it only fetches the single file needed.
    Supports GitHub and GitLab.

    Args:
        remote: The git remote URL.
        commit: The commit hash to fetch from.
        filepath: The path to the file in the repository.

    Returns:
        The file contents as bytes, or None if fetching fails or
        the hosting provider is not supported.
    """
    # Try GitHub
    github_info = parse_github_url(remote)
    if github_info:
        owner, repo = github_info
        return fetch_file_from_github(owner, repo, commit, filepath)

    # Try GitLab
    gitlab_info = parse_gitlab_url(remote)
    if gitlab_info:
        host, project_path = gitlab_info
        return fetch_file_from_gitlab(host, project_path, commit, filepath)

    # Unsupported hosting provider
    return None
