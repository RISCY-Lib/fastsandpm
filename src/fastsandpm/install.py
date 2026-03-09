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
"""Install and manage dependencies into a local library.

This module provides functionality to build and install library dependencies from resolved
dependency definitions. It handles installation of different candidate types:

- **Git Candidates**: Clones repositories and checks out specified commits with smart
  directory replacement for dirty/incorrect repos when clean=True.
- **Path Candidates**: Creates symlinks to local directories with smart updates when
  target already exists.
- **PackageIndex Candidates**: Not yet implemented.

The main entry point is `library_from_manifest()` which resolves dependencies from a manifest
and installs them into a destination directory. For more direct control, use `build_library()`
with a pre-built dependency definition.

After all dependencies are installed, a ``library.f`` file is created that lists the file
lists of each dependency in dependency-sorted order, allowing the entire library to be
included via a single "-F library.f" directive.

Installation Behavior:

- **Non-existent directories**: Cloned/created fresh.
- **Existing with correct state**: Updated to specified versions (fetch+checkout for git).
- **Existing with incorrect state**: Removed and replaced if clean=True, otherwise skipped
  with a warning.
- **Dirty repositories or non-git directories**: Handled based on the clean flag.

Example:
    >>> manifest = get_manifest("path/to/manifest.toml")
    >>> library_from_manifest(manifest, pathlib.Path("lib/"))
"""

from __future__ import annotations

import logging
import pathlib
import shutil
from subprocess import CalledProcessError

from fastsandpm import _git_utils
from fastsandpm.dependencies import Candidate, resolve
from fastsandpm.dependencies.candidates import GitCandidate, PackageIndexCandidate, PathCandidate
from fastsandpm.manifest import (
    Manifest,
    ManifestNotFoundError,
    ManifestParseError,
    get_manifest,
)

_logger = logging.getLogger(__name__)


def library_from_manifest(
    manifest: Manifest,
    dest: pathlib.Path,
    optional_deps: list[str] | None = None,
    clean: bool = True,
) -> None:
    """Build a library of dependencies from a manifest.

    The library will be placed in the destination directory with each dependency having it's own
    directory.
    A ``library.f`` file list will be created which points to the root file-list of each dependency.

    Args:
        manifest: The manifest to build the library from.
        dest: The destination directory for the library.
        optional_dep: Optional dependency groups to include in the library.
        clean: If True, clean existing directories when conflicts occur.

    Raises:
        resolvelib.ResolutionImpossible: If no compatible resolution exists.
    """
    library = resolve(manifest, optional_deps)
    build_library(library, dest, clean)


def build_library(definition: dict[str, Candidate], dest: pathlib.Path, clean: bool = True) -> bool:
    """Build a library candidate from a manifest definition.

    The library will be placed in the destination directory with each dependency having it's own
    directory.
    A ``library.f`` file list will be created which points to the root file-list of each dependency.

    For Git Candidates:
    - If the directory doesn't exist, it will be cloned and checked out to the correct commit.
    - If the directory is a git repo with the correct remote and no local changes, it will be
    checked out to the correct commit. Otherwise, it will be deleted and cloned and checked out to
    the correct commit.
    - If the directory is a git repo with an incorrect remote and no local changes or commits, it
    will be deleted and the new repo cloned and checked out to the correct commit.
    - If the directory is a git repo with local changes or un-pushed commits, it will be deleted
    and replaced with the new repo cloned and checked out to the correct commit, if and only if
    clean is True. Otherwise, a warning will be logged and the method will return False after all
    other dependencies have been installed.
    - If the directory is not a git repo, it will be deleted and replaced with the new repo if and
    only if clean is True. Otherwise, a warning will be logged and the method will return False
    after all other dependencies have been installed.

    For Path Candidates:
    - If the directory doesn't exist, a symlink will be created to the correct path.
    - If the directory exists and is a symlink, the symlink will be updated to the correct path.
    - If the directory exists and is not a symlink and clean is True, the directory will be deleted
    and replaced with a symlink to the correct path.
    - Otherwise a warning will be logged and the method will return False after all other
    dependencies have been installed.

    For PackageIndex Candidates:
    - **NOT CURRENTLY IMPLEMENTED**

    After all of the candidates have been installed, the ``library.f`` file list will be created.
    This is done by creating an ordered list of dependencies such that any dependency whose manifest
    includes another dependency appears after that dependency. The ``library.f`` file list will
    then be created such that it is a series of "-F" relative includes which point to the 'flist'
    files of each dependency (if they have a manifest) or the the '{name}.f' of a dependency without
    a manifest.

    Args:
        definition: The definition of the library to build. Where the key is the name of the
            dependency and the value is the candidate for that dependency.
        dest: The destination directory for the library.
        clean: If True, clean the destination directory before building the library.

    Returns:
        True if all of the library dependencies were successfully updated or installed.
        Otherwise False.
    """

    # Track if all installations succeed
    all_success = True

    # Create destination directory if it doesn't exist
    dest.mkdir(parents=True, exist_ok=True)

    # Install each candidate
    for name, candidate in definition.items():
        dep_dir = dest / name

        if isinstance(candidate, GitCandidate):
            success = _install_git_candidate(candidate, dep_dir, clean)
            all_success = all_success and success

        elif isinstance(candidate, PathCandidate):
            success = _install_path_candidate(candidate, dep_dir, clean)
            all_success = all_success and success

        elif isinstance(candidate, PackageIndexCandidate):
            _logger.warning("PackageIndex candidates are not yet implemented. Skipping %s.", name)
            all_success = False

        else:
            _logger.error("Unknown candidate type for %s: %s", name, type(candidate))
            all_success = False

    # Create library.f file with proper dependency ordering
    _create_library_filelist(definition, dest)

    return all_success


def _clone_and_checkout(candidate: GitCandidate, dep_dir: pathlib.Path) -> bool:
    """Clone a repository and checkout the specified commit.

    Args:
        candidate: The Git candidate containing remote URL and commit hash.
        dep_dir: The directory where the repository should be cloned.

    Returns:
        True if clone and checkout succeeded, False otherwise.
    """
    try:
        _git_utils.clone(candidate.remote, dep_dir)
        _git_utils.checkout(candidate.commit_hash, dep_dir)
        return True
    except CalledProcessError as e:
        _logger.error("Failed to clone/checkout %s: %s", candidate.name, e)
        return False


def _remove_directory(dep_dir: pathlib.Path) -> bool:
    """Remove a directory or symlink.

    Args:
        dep_dir: The directory or symlink to remove.

    Returns:
        True if removal succeeded, False otherwise.
    """
    try:
        if dep_dir.is_symlink():
            dep_dir.unlink()
        else:
            shutil.rmtree(dep_dir)
        return True
    except Exception as e:
        _logger.error("Failed to remove directory %s: %s", dep_dir, e)
        return False


def _replace_with_clone(
    candidate: GitCandidate,
    dep_dir: pathlib.Path,
    log_message: str,
    log_level: int = logging.WARNING,
) -> bool:
    """Remove existing directory and clone fresh repository.

    Args:
        candidate: The Git candidate containing remote URL and commit hash.
        dep_dir: The directory to replace with a fresh clone.
        log_message: Message to log on success (will be formatted with candidate.name).
        log_level: The logging level for the success message.

    Returns:
        True if replacement succeeded, False otherwise.
    """
    if not _remove_directory(dep_dir):
        return False

    if not _clone_and_checkout(candidate, dep_dir):
        return False

    _logger.log(log_level, log_message, candidate.name)
    return True


def _install_git_candidate(candidate: GitCandidate, dep_dir: pathlib.Path, clean: bool) -> bool:
    """Install a Git candidate to the specified directory.

    Args:
        candidate: The Git candidate to install.
        dep_dir: The directory where the candidate should be installed.
        clean: If True, allow deletion of existing directories with issues.

    Returns:
        True if installation succeeded, False otherwise.
    """
    # Case 1: Directory doesn't exist - clone and checkout
    if not dep_dir.exists():
        if _clone_and_checkout(candidate, dep_dir):
            _logger.debug("Cloned %s from %s", candidate.name, candidate.remote)
            return True
        return False

    # Case 2: Directory exists but is not a git repo
    if not _git_utils.is_git_repo(dep_dir):
        return _handle_non_git_directory(candidate, dep_dir, clean)

    # Case 3: Directory is a git repo - check remote and dirty state
    return _handle_existing_git_repo(candidate, dep_dir, clean)


def _handle_non_git_directory(candidate: GitCandidate, dep_dir: pathlib.Path, clean: bool) -> bool:
    """Handle the case where the target directory exists but is not a git repo.

    Args:
        candidate: The Git candidate to install.
        dep_dir: The existing non-git directory.
        clean: If True, remove and replace with clone.

    Returns:
        True if installation succeeded, False otherwise.
    """
    if not clean:
        _logger.warning(
            "Directory %s exists but is not a git repo. Use clean=True to overwrite.",
            candidate.name,
        )
        return False

    return _replace_with_clone(candidate, dep_dir, "Removed non-git directory for %s and cloned")


def _handle_existing_git_repo(candidate: GitCandidate, dep_dir: pathlib.Path, clean: bool) -> bool:
    """Handle the case where the target directory is an existing git repo.

    Args:
        candidate: The Git candidate to install.
        dep_dir: The existing git repository directory.
        clean: If True, allow removal of dirty repos.

    Returns:
        True if installation succeeded, False otherwise.
    """
    current_remote = _git_utils.get_remote_url(dep_dir, "origin")
    is_dirty = _git_utils.is_dirty(dep_dir)
    remote_matches = current_remote == candidate.remote

    # Clean repo with correct remote - just fetch and checkout
    if remote_matches and not is_dirty:
        return _fetch_and_checkout(candidate, dep_dir)

    # Clean repo with wrong remote - replace it
    if not remote_matches and not is_dirty:
        return _replace_with_clone(
            candidate,
            dep_dir,
            "Removed repo with incorrect remote for %s and re-cloned",
            logging.DEBUG,
        )

    # Dirty repo - need clean=True to proceed
    if not clean:
        if remote_matches:
            _logger.warning(
                "Repository %s has local changes. Use clean=True to overwrite.",
                candidate.name,
            )
        else:
            _logger.warning(
                "Repository %s has incorrect remote and local changes. "
                "Use clean=True to overwrite.",
                candidate.name,
            )
        return False

    # Dirty repo with clean=True - replace it
    log_msg = (
        "Removed dirty repo for %s and re-cloned"
        if remote_matches
        else "Removed dirty repo with incorrect remote for %s and re-cloned"
    )
    return _replace_with_clone(candidate, dep_dir, log_msg)


def _fetch_and_checkout(candidate: GitCandidate, dep_dir: pathlib.Path) -> bool:
    """Fetch updates and checkout the specified commit.

    Args:
        candidate: The Git candidate containing the commit hash.
        dep_dir: The git repository directory.

    Returns:
        True if fetch and checkout succeeded, False otherwise.
    """
    try:
        _git_utils.fetch(dep_dir)
        _git_utils.checkout(candidate.commit_hash, dep_dir)
        _logger.debug("Updated %s to %s", candidate.name, candidate.commit_hash[:7])
        return True
    except CalledProcessError as e:
        _logger.error("Failed to checkout %s: %s", candidate.name, e)
        return False


def _install_path_candidate(candidate: PathCandidate, dep_dir: pathlib.Path, clean: bool) -> bool:
    """Install a Path candidate to the specified directory.

    Args:
        candidate: The Path candidate to install.
        dep_dir: The directory where the symlink should be created.
        clean: If True, allow deletion of existing directories.
        _logger: Logger for warnings and errors.

    Returns:
        True if installation succeeded, False otherwise.
    """
    # Case 1: Directory doesn't exist - create symlink
    if not dep_dir.exists():
        try:
            dep_dir.symlink_to(candidate.path, target_is_directory=True)
            _logger.debug("Created symlink for %s -> %s", candidate.name, candidate.path)
            return True
        except Exception as e:
            _logger.error("Failed to create symlink for %s: %s", candidate.name, e)
            return False

    # Case 2: Directory exists and is a symlink - update it
    if dep_dir.is_symlink():
        current_target = dep_dir.resolve()
        if current_target == candidate.path:
            _logger.debug("Symlink for %s is already correct", candidate.name)
            return True
        else:
            try:
                dep_dir.unlink()
                dep_dir.symlink_to(candidate.path, target_is_directory=True)
                _logger.debug("Updated symlink for %s -> %s", candidate.name, candidate.path)
                return True
            except Exception as e:
                _logger.error("Failed to update symlink for %s: %s", candidate.name, e)
                return False

    # Case 3: Directory exists but is not a symlink
    else:
        if clean:
            try:
                shutil.rmtree(dep_dir)
                dep_dir.symlink_to(candidate.path, target_is_directory=True)
                _logger.warning(
                    "Removed existing directory for %s and created symlink", candidate.name
                )
                return True
            except Exception as e:
                _logger.error("Failed to replace existing directory for %s: %s", candidate.name, e)
                return False
        else:
            _logger.warning(
                "Directory %s exists but is not a symlink. Use clean=True to overwrite.",
                candidate.name,
            )
            return False


def _create_library_filelist(definition: dict[str, Candidate], dest: pathlib.Path) -> None:
    """Create the library.f filelist with proper dependency ordering.

    Args:
        definition: The library definition with candidates.
        dest: The destination directory for the library.
        _logger: Logger for warnings and errors.
    """

    # Build dependency graph to determine ordering
    dep_graph: dict[str, set[str]] = {}
    dep_manifests: dict[str, Manifest] = {}

    for name, _ in definition.items():
        dep_graph[name] = set()
        dep_dir = dest / name

        # Check if candidate has a manifest
        try:
            dep_manifests[name] = get_manifest(dep_dir)

            # Add dependencies from manifest to graph
            for dep in dep_manifests[name].dependencies:
                if dep.name in definition:
                    dep_graph[name].add(dep.name)

        except ManifestNotFoundError as _:
            _logger.debug("No manifest found for %s", name)
        except ManifestParseError as e:
            _logger.warning("Failed to read manifest for %s: %s", name, e)

    # Topological sort to order dependencies
    ordered_deps = _topological_sort(dep_graph)

    # Create library.f file
    library_f_path = dest / "library.f"
    with library_f_path.open("w") as f:
        for name in ordered_deps:
            if name in dep_manifests:
                # Use 'flist' file from manifest
                f.write(f"-F {name}/{dep_manifests[name].package.flist}\n")
            else:
                # Use '{name}.f' for dependencies without manifest
                f.write(f"-F {name}/{name}.f\n")

    _logger.debug("Created library.f with %s dependencies", len(ordered_deps))


def _topological_sort(graph: dict[str, set[str]]) -> list[str]:
    """Perform topological sort on dependency graph.

    Args:
        graph: Dictionary mapping node to set of its dependencies.

    Returns:
        List of nodes in topologically sorted order (dependencies first).
    """
    # Count incoming edges for each node
    in_degree: dict[str, int] = {node: 0 for node in graph}
    for node in graph:
        for dep in graph[node]:
            in_degree[dep] = in_degree.get(dep, 0) + 1

    # Start with nodes that have no dependencies
    queue = [node for node in graph if in_degree[node] == 0]
    result = []

    while queue:
        # Sort to ensure deterministic ordering
        queue.sort()
        node = queue.pop(0)
        result.append(node)

        # Remove edges from this node
        for dep in graph.get(node, set()):
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    return result
