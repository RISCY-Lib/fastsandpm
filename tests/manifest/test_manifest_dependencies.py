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
"""Tests for fastsandpm.manifest Dependencies section.
"""
from __future__ import annotations

import pathlib

import pytest
from pydantic import ValidationError

from fastsandpm.dependencies import PackageIndexRequirement, PathRequirement
from fastsandpm.dependencies.requirements import (
    BranchGitRequirement,
    CommitGitRequirement,
    GitRequirement,
    TaggedGitRequirement,
    VersionedGitRequirement,
)
from fastsandpm.manifest import Dependencies
from fastsandpm.versioning import (
    DirectVersionSpecifier,
    LibraryVersion,
)


class TestDependencies:
    """Tests for the Dependencies collection class.

    Tests parsing from various TOML-style formats into the correct
    dependency types.
    """

    def test_dependencies_empty_list(self) -> None:
        """Test creating empty dependencies."""
        deps = Dependencies.model_validate([])
        assert len(deps) == 0

    def test_dependencies_from_simple_string_format(self) -> None:
        """Test parsing simple string format: name = "version".

        TOML: [dependencies]
              time = "1.0.0"
        """
        deps = Dependencies.model_validate({"time": "1.0.0"})
        assert len(deps) == 1

        dep = deps[0]
        assert isinstance(dep, PackageIndexRequirement)
        assert dep.name == "time"
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_dependencies_from_registry_dict_format(self) -> None:
        """Test parsing registry dict format: name = {version = "1.0.0"}.

        TOML: [dependencies]
              time = {version = "1.0.0"}
        """
        deps = Dependencies.model_validate({"time": {"version": "1.0.0"}})
        assert len(deps) == 1

        dep = deps[0]
        assert isinstance(dep, PackageIndexRequirement)
        assert dep.name == "time"
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_dependencies_from_registry_with_registry_field(self) -> None:
        """Test parsing registry format with custom registry.

        TOML: [dependencies]
              time = {version = "1.0.0", registry = "my-registry"}
        """
        deps = Dependencies.model_validate({"time": {"version": "1.0.0", "index": "my-registry"}})
        assert len(deps) == 1

        dep = deps[0]
        assert isinstance(dep, PackageIndexRequirement)
        assert dep.name == "time"
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert dep.index == "my-registry"

    def test_dependencies_from_git_url_format(self) -> None:
        """Test parsing git URL format.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git"}
        """
        deps = Dependencies.model_validate(
            {"time": {"git": "https://github.com/username/repo.git"}})
        assert len(deps) == 1
        dep = deps[0]
        assert isinstance(dep, GitRequirement)
        assert dep.name == "time"
        assert dep.git == "https://github.com/username/repo.git"

    def test_dependencies_from_git_project_format(self) -> None:
        """Test parsing git project ID format.

        TOML: [dependencies]
              dep2 = {git = "SOME_ORG"}
        """
        deps = Dependencies.model_validate({"dep2": {"git": "SOME_ORG"}})
        assert len(deps) == 1
        dep = deps[0]
        assert isinstance(dep, GitRequirement)
        assert dep.name == "dep2"
        assert dep.git == "SOME_ORG"

    def test_dependencies_from_git_with_version(self) -> None:
        """Test parsing git format with version.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", version = "1.0.0"}
        """
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "version": "1.0.0",
                }
            }
        )
        assert len(deps) == 1
        dep = deps[0]
        assert isinstance(dep, VersionedGitRequirement)
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_dependencies_from_git_with_branch(self) -> None:
        """Test parsing git format with branch.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", branch = "some_branch"}
        """
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "branch": "some_branch",
                }
            }
        )
        assert len(deps) == 1
        dep = deps[0]
        assert isinstance(dep, BranchGitRequirement)
        assert dep.branch == "some_branch"

    def test_dependencies_from_git_with_tag(self) -> None:
        """Test parsing git format with tag.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", tag = "v1.0.0"}
        """
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "tag": "v1.0.0",
                }
            }
        )
        assert len(deps) == 1
        dep = deps[0]
        assert isinstance(dep, TaggedGitRequirement)
        assert dep.tag == "v1.0.0"

    def test_dependencies_from_git_with_commit(self) -> None:
        """Test parsing git format with commit.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", commit = "deadbeef"}
        """
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "commit": "deadbeef",
                }
            }
        )
        assert len(deps) == 1
        dep = deps[0]
        assert isinstance(dep, CommitGitRequirement)
        assert dep.commit == "deadbeef"

    def test_dependencies_from_path_format(self) -> None:
        """Test parsing path format.

        TOML: [dependencies]
              time = {path = "./some/path/to/dep1"}
        """
        deps = Dependencies.model_validate({"time": {"path": "./some/path/to/dep1"}})
        assert len(deps) == 1
        dep = deps[0]
        assert isinstance(dep, PathRequirement)
        assert dep.name == "time"
        assert dep.path == pathlib.Path("./some/path/to/dep1")

    def test_dependencies_mixed_types(self) -> None:
        """Test parsing mixed dependency types.

        TOML: [dependencies]
              registry-dep = "1.0.0"
              git-dep = {git = "https://github.com/org/repo.git"}
              path-dep = {path = "./local"}
        """
        deps = Dependencies.model_validate(
            {
                "registry-dep": "1.0.0",
                "git-dep": {"git": "https://github.com/org/repo.git"},
                "path-dep": {"path": "./local"},
            }
        )
        assert len(deps) == 3

        # Find each dependency by name and verify type
        registry = deps.get_by_name("registry-dep")
        git = deps.get_by_name("git-dep")
        path = deps.get_by_name("path-dep")

        assert isinstance(registry, PackageIndexRequirement)
        assert isinstance(git, GitRequirement)
        assert isinstance(path, PathRequirement)

    def test_dependencies_multiple_registry(self) -> None:
        """Test parsing multiple registry dependencies."""
        deps = Dependencies.model_validate(
            {
                "dep1": "1.0.0",
                "dep2": "2.0.0",
                "dep3": "^3.0.0",
            }
        )
        assert len(deps) == 3
        assert all(isinstance(d, PackageIndexRequirement) for d in deps)

    def test_dependencies_multiple_git(self) -> None:
        """Test parsing multiple git dependencies."""
        deps = Dependencies.model_validate(
            {
                "dep1": {"git": "https://github.com/org/repo1.git"},
                "dep2": {"git": "https://github.com/org/repo2.git", "branch": "main"},
                "dep3": {"git": "ORG_NAME", "tag": "v1.0.0"},
            }
        )
        assert len(deps) == 3
        assert all(isinstance(d, GitRequirement) for d in deps)

    def test_dependencies_iteration(self) -> None:
        """Test iterating over dependencies."""
        deps = Dependencies.model_validate(
            {
                "dep1": "1.0.0",
                "dep2": "2.0.0",
            }
        )
        names = [d.name for d in deps]
        assert "dep1" in names
        assert "dep2" in names

    def test_dependencies_get_by_name_found(self) -> None:
        """Test getting a dependency by name when it exists."""
        deps = Dependencies.model_validate(
            {
                "dep1": "1.0.0",
                "dep2": "2.0.0",
            }
        )
        dep = deps.get_by_name("dep2")
        assert dep is not None
        assert dep.name == "dep2"

    def test_dependencies_get_by_name_not_found(self) -> None:
        """Test getting a dependency by name when it doesn't exist."""
        deps = Dependencies.model_validate(
            {
                "dep1": "1.0.0",
            }
        )
        dep = deps.get_by_name("nonexistent")
        assert dep is None

    def test_dependencies_from_list_format(self) -> None:
        """Test creating dependencies from a list of dicts."""
        deps = Dependencies.model_validate(
            [
                {"name": "dep1", "version": "1.0.0"},
                {"name": "dep2", "git": "https://github.com/org/repo.git"},
            ]
        )
        assert len(deps) == 2
        assert isinstance(deps[0], PackageIndexRequirement)
        assert isinstance(deps[1], GitRequirement)

    def test_dependencies_duplicate_names_rejected(self) -> None:
        """Test that duplicate dependency names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Dependencies.model_validate(
                [
                    {"name": "dep1", "version": "1.0.0"},
                    {"name": "dep1", "version": "2.0.0"},
                ]
            )
        assert "Duplicate dependency names" in str(exc_info.value)

    def test_dependencies_single_dict_with_name_key(self) -> None:
        """Test parsing a single dict with name key."""
        deps = Dependencies.model_validate({"name": "dep1", "version": "1.0.0"})
        assert len(deps) == 1
        assert deps[0].name == "dep1"


class TestDependenciesDocumentationExamples:
    """Tests based on examples from the specifying_dependencies documentation."""

    def test_registry_simple_example(self) -> None:
        """Test example: time = "1.0.0"."""
        deps = Dependencies.model_validate({"time": "1.0.0"})
        dep = deps[0]
        assert isinstance(dep, PackageIndexRequirement)
        assert dep.name == "time"
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_registry_with_registry_example(self) -> None:
        """Test example: time = {registry = "my-registry", version = "1.0.0"}."""
        deps = Dependencies.model_validate({"time": {"index": "my-registry", "version": "1.0.0"}})
        dep = deps[0]
        assert isinstance(dep, PackageIndexRequirement)
        assert dep.name == "time"
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert dep.index == "my-registry"

    def test_git_full_url_example(self) -> None:
        """Test example: time = {git = "https://github.com/username/repo.git"}."""
        deps = Dependencies.model_validate(
            {"time": {"git": "https://github.com/username/repo.git"}})
        dep = deps[0]
        assert isinstance(dep, GitRequirement)
        assert dep.name == "time"
        assert dep.git == "https://github.com/username/repo.git"

    def test_git_project_id_example(self) -> None:
        """Test example: dep2 = {git = "SOME_ORG"}."""
        deps = Dependencies.model_validate({"dep2": {"git": "SOME_ORG"}})
        dep = deps[0]
        assert isinstance(dep, GitRequirement)
        assert dep.name == "dep2"
        assert dep.git == "SOME_ORG"

    def test_git_commit_example(self) -> None:
        """Test example: time = {git = "...", commit = "deadbeef"}."""
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "commit": "deadbeef",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, CommitGitRequirement)
        assert dep.commit == "deadbeef"

    def test_git_tag_example(self) -> None:
        """Test example: time = {git = "...", tag = "v1.0.0"}."""
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "tag": "v1.0.0",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, TaggedGitRequirement)
        assert dep.tag == "v1.0.0"

    def test_git_branch_example(self) -> None:
        """Test example: time = {git = "...", branch = "some_branch"}."""
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "branch": "some_branch",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, BranchGitRequirement)
        assert dep.branch == "some_branch"

    def test_git_version_example(self) -> None:
        """Test example: time = {git = "...", version = "1.0.0"}."""
        deps = Dependencies.model_validate(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "version": "1.0.0",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, VersionedGitRequirement)
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_path_example(self) -> None:
        """Test example: time = {path = "./some/path/to/dep1"}."""
        deps = Dependencies.model_validate({"time": {"path": "./some/path/to/dep1"}})
        dep = deps[0]
        assert isinstance(dep, PathRequirement)
        assert dep.name == "time"
        assert dep.path == pathlib.Path("./some/path/to/dep1")
