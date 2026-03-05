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

from __future__ import annotations

import pathlib
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from functools import singledispatch

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
from fastsandpm.manifest import MANIFEST_FILENAME, Manifest, get_manifest
from fastsandpm.registries import Registries
from fastsandpm.versioning.library_version import LibraryVersion
from fastsandpm.versioning.specifier import VersionSpecifier


@dataclass(frozen=True)
class Candidate(ABC):
    """A candidate in a dependency resolution process."""

    name: str
    """The name of the dependency."""

    version: LibraryVersion | None
    """The library version that this candidate corresponds to (if it corresponds to one)"""

    @abstractmethod
    def get_manifest(self) -> Manifest | None:
        """Return the manifest for this candidate"""

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        """A candidate is considered to satisfy the requirement under the following conditions:

        - The requirement name and candidate name match
        - If the requirement spcifies a version, the version of the candidate matches
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
    """A candidate from a Package Index"""

    def get_manifest(self) -> Manifest | None:
        """Return the manifest for this candidate"""
        # Note Package Index registries are not yet implemented
        pass

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        return super().satisfies(requirement)


@dataclass(frozen=True)
class PathCandidate(Candidate):
    """A candidate from a path on disk"""

    path: pathlib.Path
    """The abosolute resolved path to the candidate"""

    def get_manifest(self) -> Manifest | None:
        """Get the manifest from the candidate's path"""
        if self.path.joinpath(MANIFEST_FILENAME).exists():
            return get_manifest(self.path)
        return None

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        """A path candidate is considered to satisfy the requirement under the following conditions:

        - The requirement name and candidate name match
        - If the requirement spcifies a version, the version of the candidate matches
        - If the requirement is a package index registry, and the version of the candidate matches
        - If the requirement is a path index registry and the path of the candidate ends with the
          path of the requirement
        - If the requirement is a git repo and the candidate points to a git repo, and the git repo
          HEAD complies with the requirement
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
                return cand_parts[-len(req_parts):] == req_parts
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


@dataclass(frozen=True)
class GitCandidate(Candidate):
    """A candidate from a Git Repo"""

    remote: str
    """The fully qualified URL to the git repo which the candidate comes from"""

    commit_hash: str
    """The commit hash the GitCandidate corresponds to"""

    corresponding_heads: frozenset[str]
    """Set of corresponding git head references that this candidate's commit hash corresponds to"""

    corresponding_tags: frozenset[str]
    """Set of corresponding git tag references that this candidate's commit hash corresponds to"""

    def get_manifest(self) -> Manifest | None:
        """Return the manifest for this candidate.

        Clones the candidate's git repo to a temporary directory and checks for a ``proj.toml``.
        If found, returns the manifest from the ``proj.toml``.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = pathlib.Path(tmpdir) / "repo"
            try:
                _git_utils.clone(self.remote, repo_path)
                _git_utils.checkout(self.commit_hash, repo_path)
            except Exception:
                # If cloning or checkout fails, return None
                return None

            # Check if manifest file exists
            if not repo_path.joinpath(MANIFEST_FILENAME).exists():
                return None

            return get_manifest(repo_path)

    def satisfies(self, requirement: ConcreteRequirement) -> bool:
        """A git candidate is considered to satisfy the requirement under the following conditions:

        - The requirement name and candidate name match
        - If the requirement spcifies a version, the version of the candidate matches
        - If the requirement is a package index requirement and the requirement doesn't specify an
          index to use.
        - If the requirement is not a path candidate.
        - If the requirement is a git repo and the candidate points to a git repo, and the git repo
          HEAD complies with the requirement
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
    """Creates as many candidates as possible from the requirement and yields them."""
    breakpoint()
    yield from []


@candidate_factory.register
def _package_index_candidate_factory(
    req: PackageIndexRequirement, registries: Registries
) -> Generator[PackageIndexCandidate, None, None]:
    """Create a candidate from a package index requirement.

    Package Indecies are not yet implemented
    """
    yield from []


@candidate_factory.register
def _path_candidate_factory(
    req: PathRequirement, registries: Registries
) -> Generator[PathCandidate, None, None]:
    """Create a candidate from a path requirement.

    If the requirement uses an abosolute path then directly use it.
    Otherwise, go through the registries to find a matched path for any regsitry where match exists.
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
    """Create a set of candidates from a git requirement.

    If the requirement uses a concreteURL then use that URL as the remote.
    Otherwise, look through the registries to find a matching remote.

    Once the remote is found, create a candidate for each commit hash that meets the requirement
    specifications and yield them.
    """
    remotes_to_try: list[str] = []

    # If the requirement has a fully qualified remote URL, use it directly
    if req.has_qualified_remote():
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
    refs: dict[str, tuple[set[str], set[str]]],
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


def _extract_version_from_tags(tags: set[str]) -> LibraryVersion | None:
    """Extract the highest version from a set of tags.

    Args:
        tags: Set of tag names.

    Returns:
        The highest LibraryVersion found, or None if no valid versions.
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
