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
"""Candidate generation for dependency resolution.

This module provides classes representing dependency candidates and factory
functions to generate candidates from requirements. Candidates represent
concrete versions of dependencies that can satisfy requirements.

Classes:
    Candidate: Abstract base class for all candidate types.
    PackageIndexCandidate: Candidate from a package index registry.
    PathCandidate: Candidate from a local filesystem path.
    GitCandidate: Candidate from a git repository.

Functions:
    candidate_factory: Singledispatch function to create candidates from requirements.
"""

from __future__ import annotations

import pathlib
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Generator
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from functools import lru_cache, singledispatch

from fastsandpm import _git_utils
from fastsandpm.dependencies.requirements import (
    BranchGitRequirement,
    CommitGitRequirement,
    ConcreteRequirement,
    GitRequirement,
    PackageIndexRequirement,
    PathRequirement,
    TaggedGitRequirement,
    VersionedGitRequirement,
)
from fastsandpm.manifest import MANIFEST_FILENAME, Manifest, get_manifest, get_manifest_from_bytes
from fastsandpm.registries import Registries
from fastsandpm.versioning.library_version import LibraryVersion
from fastsandpm.versioning.specifier import VersionSpecifier


@dataclass(frozen=True)
class Candidate(ABC):
    """Abstract base class for dependency resolution candidates.

    A candidate represents a concrete version of a dependency that can potentially
    satisfy one or more requirements. During dependency resolution, candidates are
    generated from requirements and evaluated for compatibility.
    """

    name: str
    """The name of the dependency package."""

    version: LibraryVersion | None
    """The semantic version of this candidate, or None if not versioned."""

    @abstractmethod
    def get_manifest(self) -> Manifest | None:
        """Retrieve the manifest for this candidate.

        Returns:
            The parsed Manifest object for this candidate, or None if no manifest
            exists or cannot be retrieved.
        """

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        """Check if this candidate satisfies the given requirement.

        A candidate satisfies a requirement when:
        - The requirement name and candidate name match
        - If the requirement specifies a version, the candidate's version matches

        Args:
            requirement: The requirement to check against.

        Returns:
            True if this candidate satisfies the requirement, False otherwise.
        """
        if (
            version := getattr(requirement, "version", None)
        ) is not None and self.version is not None:
            assert isinstance(version, VersionSpecifier)
            if not version.satisfied_by(self.version):
                return False

        return requirement.name == self.name


@dataclass(frozen=True)
class PackageIndexCandidate(Candidate):
    """A candidate from a package index registry.

    Package index candidates are resolved from package registries like JFrog
    Artifactory. This implementation is currently a placeholder as package
    index registries are not yet fully implemented.

    Note:
        Package index registry support is under development.
    """

    def get_manifest(self) -> Manifest | None:
        """Retrieve the manifest for this package index candidate.

        Returns:
            The parsed Manifest object, or None. Currently always returns None
            as package index registries are not yet implemented.
        """
        # Note Package Index registries are not yet implemented
        pass

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        """Check if this candidate satisfies the given requirement.

        Args:
            requirement: The requirement to check against.

        Returns:
            True if this candidate satisfies the requirement, False otherwise.
        """
        return super().satisfies(requirement)


@dataclass(frozen=True)
class PathCandidate(Candidate):
    """A candidate from a local filesystem path.

    Path candidates represent dependencies available at a local directory.
    They are useful for monorepo setups or local development where
    dependencies are checked out alongside the main project.
    """

    path: pathlib.Path
    """The absolute resolved path to the candidate directory."""

    def get_manifest(self) -> Manifest | None:
        """Retrieve the manifest from the candidate's local path.

        Returns:
            The parsed Manifest object if a proj.toml file exists at the path,
            or None if no manifest file is found.
        """
        if self.path.joinpath(MANIFEST_FILENAME).exists():
            return get_manifest(self.path)
        return None

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        """Check if this path candidate satisfies the given requirement.

        A path candidate satisfies a requirement when the requirement name
        and candidate name match, and type-specific conditions are met:

        * For PackageIndexRequirement: the candidate's version matches the specifier
        * For PathRequirement: the candidate path ends with the requirement path
        * For Git requirements: the path is a git repo and HEAD complies with
          the requirement's constraints (commit, branch, tag, or version)

        Args:
            requirement: The requirement to check against.

        Returns:
            True if this candidate satisfies the requirement, False otherwise.
        """
        if not super().satisfies(requirement):
            return False

        if isinstance(requirement, PackageIndexRequirement):
            return self.version is not None and requirement.version.satisfied_by(self.version)

        # Handle PathRequirement: check if candidate path ends with requirement path
        if isinstance(requirement, PathRequirement):
            req_parts = requirement.path.parts
            cand_parts = self.path.parts
            if len(req_parts) <= len(cand_parts):
                return cand_parts[-len(req_parts) :] == req_parts
            return False

        # Handle Git requirements: check if candidate points to a git repo
        # and the git repo HEAD complies with the requirement
        # Check if the candidate path is a git repository
        if not _git_utils.is_git_repo(self.path):
            return False

        # For CommitGitRequirement: check if HEAD commit matches
        if isinstance(requirement, CommitGitRequirement):
            if (head_commit := _git_utils.get_head_commit(self.path)) is None:
                return False
            return head_commit.startswith(requirement.commit)  # allow prefix matches

        # For BranchGitRequirement: check if current branch matches
        if isinstance(requirement, BranchGitRequirement):
            current_branch = _git_utils.get_current_branch(self.path)
            return current_branch == requirement.branch

        # For TaggedGitRequirement: check if HEAD has the required tag
        if isinstance(requirement, TaggedGitRequirement):
            tags_at_head = _git_utils.get_tags_at_head(self.path)
            return requirement.tag in tags_at_head

        # For VersionedGitRequirement: check if any tag at HEAD satisfies the version
        if isinstance(requirement, VersionedGitRequirement):
            if self.version is not None and requirement.version.satisfied_by(self.version):
                return True

            tags_at_head = _git_utils.get_tags_at_head(self.path)
            for tag in tags_at_head:
                # Try to parse tag as a version (strip 'v' or 'V' prefix)
                version_str = tag.lstrip("vV")
                try:
                    tag_version = LibraryVersion(version_str)
                    if requirement.version.satisfied_by(tag_version):
                        return True
                except ValueError:
                    # Tag is not a valid version, skip it
                    continue
            return False

        # For base GitRequirement (no version/tag/branch/commit specified):
        # Just verify that the path is a git repo (already checked above)
        return True


# Sentinel value to distinguish "no manifest found" from "not yet cached"
_NO_MANIFEST: Manifest = None  # type: ignore[assignment]


@lru_cache(maxsize=256)
def _fetch_git_manifest_cached(remote: str, commit_hash: str) -> Manifest | None:
    """Fetch and cache a manifest from a git remote.

    Results are cached by (remote, commit_hash) to avoid repeated network calls
    during dependency resolution. Use `_fetch_git_manifest_cached.cache_clear()`
    to invalidate the cache.

    The function tries multiple methods in order of speed:
    1. git archive --remote (fastest, but not supported by GitHub)
    2. Hosting provider REST API (GitHub/GitLab raw file endpoints)
    3. Full git clone (slowest, but works with any git host)

    Args:
        remote: The fully qualified URL to the git repository.
        commit_hash: The commit hash to fetch the manifest from.

    Returns:
        The parsed Manifest object, or None if no manifest exists or fetching fails.
    """
    # First, try the fast path: fetch only proj.toml using git archive or hosting provider API
    try:
        content = _git_utils.get_remote_file(remote, commit_hash, MANIFEST_FILENAME)
        return get_manifest_from_bytes(content, source=f"{remote}@{commit_hash}")
    except ValueError:
        # git archive --remote is not supported by this host (e.g., GitHub)
        # or the file doesn't exist. Try hosting provider API next.
        pass

    # Fallback: full clone (slower but works with all git hosts)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = pathlib.Path(tmpdir) / "repo"
        try:
            _git_utils.clone(remote, repo_path)
            _git_utils.checkout(commit_hash, repo_path)
        except Exception:
            # If cloning or checkout fails, return None
            return None

        # Check if manifest file exists
        if not repo_path.joinpath(MANIFEST_FILENAME).exists():
            return None

        return get_manifest(repo_path)


@dataclass(frozen=True)
class GitCandidate(Candidate):
    """A candidate from a git repository.

    Git candidates represent dependencies available from remote git repositories.
    They are identified by a commit hash and include metadata about corresponding
    branches and tags for that commit.
    """

    remote: str
    """The fully qualified URL to the git repository."""

    commit_hash: str
    """The full SHA commit hash this candidate corresponds to."""

    corresponding_heads: frozenset[str]
    """Set of branch names pointing to this commit."""

    corresponding_tags: frozenset[str]
    """Set of tag names pointing to this commit."""

    def get_manifest(self) -> Manifest | None:
        """Retrieve the manifest for this git candidate.

        Results are cached by (remote, commit_hash) to avoid repeated network calls
        during dependency resolution. First attempts to fetch only the manifest file
        using the hosting provider's API (GitHub/GitLab), which is significantly
        faster than a full clone. If that fails, falls back to a full clone.

        Returns:
            The parsed Manifest object, or None if no manifest exists or fetching fails.
        """
        return _fetch_git_manifest_cached(self.remote, self.commit_hash)

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        """Check if this git candidate satisfies the given requirement.

        A git candidate satisfies a requirement when:
        - The requirement name and candidate name match
        - If the requirement specifies a version, the candidate's version matches
        - For PackageIndexRequirement: only if no specific index is required
        - PathRequirement: never satisfied by git candidates
        - For CommitGitRequirement: commit hash matches (prefix match allowed)
        - For BranchGitRequirement: candidate's heads include the required branch
        - For TaggedGitRequirement: candidate's tags include the required tag
        - For VersionedGitRequirement: any tag satisfies the version constraint

        Args:
            requirement: The requirement to check against.

        Returns:
            True if this candidate satisfies the requirement, False otherwise.
        """
        if not super().satisfies(requirement):
            return False

        if isinstance(requirement, PackageIndexRequirement):
            return requirement.index is None

        if isinstance(requirement, PathRequirement):
            return False

        # Handle Git requirements
        # For CommitGitRequirement: check if commit hash matches (prefix match allowed)
        if isinstance(requirement, CommitGitRequirement):
            return self.commit_hash.startswith(requirement.commit)

        # For BranchGitRequirement: check if the candidate's heads include the required branch
        if isinstance(requirement, BranchGitRequirement):
            return requirement.branch in self.corresponding_heads

        # For TaggedGitRequirement: check if the candidate's tags include the required tag
        if isinstance(requirement, TaggedGitRequirement):
            return requirement.tag in self.corresponding_tags

        # For VersionedGitRequirement: check if any tag satisfies the version
        if isinstance(requirement, VersionedGitRequirement):
            for tag in self.corresponding_tags:
                # Try to parse tag as a version (strip 'v' or 'V' prefix)
                version_str = tag.lstrip("vV")
                try:
                    tag_version = LibraryVersion(version_str)
                    if requirement.version.satisfied_by(tag_version):
                        return True
                except ValueError:
                    # Tag is not a valid version, skip it
                    continue
            return False

        # For base GitRequirement (no version/tag/branch/commit specified):
        # The git candidate satisfies base git requirements
        return True


@singledispatch
def candidate_factory(
    req: ConcreteRequirement, registries: Registries
) -> Generator[Candidate, None, None]:
    """Generate candidates from a requirement using available registries.

    This is a singledispatch function that dispatches to specialized implementations
    based on the requirement type. Each implementation generates zero or more
    candidates that could potentially satisfy the requirement.

    Args:
        req: The requirement to generate candidates for.
        registries: The available registries to search for candidates.

    Yields:
        Candidate objects that could satisfy the requirement.

    Note:
        The base implementation yields no candidates. Specialized implementations
        are registered for each concrete requirement type.
    """
    yield from []


@candidate_factory.register
def _package_index_candidate_factory(
    req: PackageIndexRequirement, registries: Registries
) -> Generator[PackageIndexCandidate, None, None]:
    """Generate candidates from a package index requirement.

    Args:
        req: The package index requirement to generate candidates for.
        registries: The available registries to search for candidates.

    Yields:
        PackageIndexCandidate objects matching the requirement.

    Note:
        Package index registries are not yet implemented, so this currently
        yields no candidates.
    """
    yield from []


@candidate_factory.register
def _path_candidate_factory(
    req: PathRequirement, registries: Registries
) -> Generator[PathCandidate, None, None]:
    """Generate candidates from a path requirement.

    For absolute paths, uses the path directly. For relative paths, searches
    through available path registries to find matching directories.

    Args:
        req: The path requirement to generate candidates for.
        registries: The available registries to search for candidates.

    Yields:
        PathCandidate objects for each matching path found.
    """
    # If the requirement path is absolute, use it directly
    if req.path.is_absolute():
        resolved_path = req.path.resolve()
        if not resolved_path.exists():
            return

        # Try to get version from manifest if it exists
        version = None
        manifest_path = resolved_path / MANIFEST_FILENAME
        if manifest_path.exists():
            try:
                manifest = get_manifest(resolved_path)
                version = manifest.package.version
            except Exception:
                pass

        yield PathCandidate(
            name=req.name,
            version=version,
            path=resolved_path,
        )
        return

    # For relative paths, search through path registries
    for registry in registries.path_registries():
        candidate_path = (registry.path / req.path).resolve()

        if not candidate_path.exists():
            continue

        # Try to get version from manifest if it exists
        version = None
        manifest_path = candidate_path / MANIFEST_FILENAME
        if manifest_path.exists():
            try:
                manifest = get_manifest(candidate_path)
                version = manifest.package.version
            except Exception:
                pass

        yield PathCandidate(
            name=req.name,
            version=version,
            path=candidate_path,
        )


@candidate_factory.register
def _git_candidate_factory(
    req: GitRequirement, registries: Registries
) -> Generator[GitCandidate, None, None]:
    """Generate candidates from a git requirement.

    If the requirement has a fully qualified remote URL, uses that directly.
    Otherwise, constructs potential remote URLs by combining the requirement's
    git identifier with available git registries.

    For each accessible remote, creates candidates based on the requirement type:
    - CommitGitRequirement: candidates matching the commit prefix
    - BranchGitRequirement: candidates on the specified branch
    - TaggedGitRequirement: candidates with the specified tag
    - VersionedGitRequirement: candidates with tags satisfying the version
    - Base GitRequirement: candidates on main/master branch

    Args:
        req: The git requirement to generate candidates for.
        registries: The available registries to search for candidates.

    Yields:
        GitCandidate objects for each matching ref found in the repository.
    """
    remotes_to_try: list[str] = []

    # If the requirement has a fully qualified remote URL, use it directly
    if req.has_qualified_remote():
        if not req.git.endswith(".git"):
            remotes_to_try.append(req.git + ".git")
        else:
            remotes_to_try.append(req.git)
    else:
        # Otherwise, build potential remotes from git registries
        for registry in registries.git_registries():
            # Construct the potential remote URL by combining registry remote
            # with the git identifier
            potential_remote = f"{registry.remote.rstrip('/')}/{req.git}/{req.name}"
            if not potential_remote.endswith(".git"):
                potential_remote += ".git"
            remotes_to_try.append(potential_remote)

    # Try each remote until we find one that works
    for remote in remotes_to_try:
        try:
            refs = _git_utils.get_remote_refs(remote)
        except ValueError:
            # Remote doesn't exist or isn't accessible
            continue

        # Create candidates based on the requirement type
        yield from _create_git_candidates_from_refs(req, remote, refs)
        # Only use the first accessible remote
        break


def _create_git_candidates_from_refs(
    req: GitRequirement,
    remote: str,
    refs: dict[str, tuple[frozenset[str], frozenset[str]]],
) -> Generator[GitCandidate, None, None]:
    """Create GitCandidate objects from remote refs based on the requirement type.

    Args:
        req: The git requirement specifying what to look for.
        remote: The remote URL.
        refs: Dictionary mapping commit hashes to (branches, tags) tuples.

    Yields:
        GitCandidate objects that match the requirement.
    """
    # For CommitGitRequirement: find the commit that matches
    if isinstance(req, CommitGitRequirement):
        for commit_hash, (branches, tags) in refs.items():
            if commit_hash.startswith(req.commit):
                # Try to extract version from tags
                version = _extract_version_from_tags(tags)
                yield GitCandidate(
                    name=req.name,
                    version=version,
                    remote=remote,
                    commit_hash=commit_hash,
                    corresponding_heads=frozenset(branches),
                    corresponding_tags=frozenset(tags),
                )
        return

    # For BranchGitRequirement: find commits on the specified branch
    if isinstance(req, BranchGitRequirement):
        for commit_hash, (branches, tags) in refs.items():
            if req.branch in branches:
                version = _extract_version_from_tags(tags)
                yield GitCandidate(
                    name=req.name,
                    version=version,
                    remote=remote,
                    commit_hash=commit_hash,
                    corresponding_heads=frozenset(branches),
                    corresponding_tags=frozenset(tags),
                )
        return

    # For TaggedGitRequirement: find commits with the specified tag
    if isinstance(req, TaggedGitRequirement):
        for commit_hash, (branches, tags) in refs.items():
            if req.tag in tags:
                version = _extract_version_from_tags(tags)
                yield GitCandidate(
                    name=req.name,
                    version=version,
                    remote=remote,
                    commit_hash=commit_hash,
                    corresponding_heads=frozenset(branches),
                    corresponding_tags=frozenset(tags),
                )
        return

    # For VersionedGitRequirement: find commits with tags that satisfy the version
    if isinstance(req, VersionedGitRequirement):
        for commit_hash, (branches, tags) in refs.items():
            for tag in tags:
                version_str = tag.lstrip("vV")
                try:
                    tag_version = LibraryVersion(version_str)
                    if req.version.satisfied_by(tag_version):
                        yield GitCandidate(
                            name=req.name,
                            version=tag_version,
                            remote=remote,
                            commit_hash=commit_hash,
                            corresponding_heads=frozenset(branches),
                            corresponding_tags=frozenset(tags),
                        )
                        break  # Only yield once per commit
                except ValueError:
                    continue
        return

    # For base GitRequirement: yield all commits (typically just want the default branch)
    # In practice, we should probably just yield the HEAD/main/master branch
    for commit_hash, (branches, tags) in refs.items():
        # Prefer main or master branch
        if "main" in branches or "master" in branches:
            version = _extract_version_from_tags(tags)
            yield GitCandidate(
                name=req.name,
                version=version,
                remote=remote,
                commit_hash=commit_hash,
                corresponding_heads=frozenset(branches),
                corresponding_tags=frozenset(tags),
            )
            return  # Only yield one candidate for base GitRequirement


def _extract_version_from_tags(tags: AbstractSet[str]) -> LibraryVersion | None:
    """Extract the highest semantic version from a set of git tags.

    Parses each tag as a potential version string (stripping 'v' or 'V' prefix)
    and returns the highest valid semantic version found.

    Args:
        tags: Set or frozenset of git tag names.

    Returns:
        The highest LibraryVersion found among valid version tags,
        or None if no tags can be parsed as valid versions.
    """
    versions: list[LibraryVersion] = []
    for tag in tags:
        version_str = tag.lstrip("vV")
        try:
            versions.append(LibraryVersion(version_str))
        except ValueError:
            continue

    if versions:
        versions.sort()
        return versions[-1]  # Return highest version

    return None
