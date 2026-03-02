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
"""Tests for fastsandpm.dependencies module.

These tests verify the dependency specifiers as defined in the specifying_dependencies
documentation. The supported specifier types are:

- Registry: name + version (+ optional registry)
- Git: git URL/project ID + optional version/branch/tag/commit
- Path: local path to dependency
"""

from __future__ import annotations

import pathlib

import pytest
from pydantic import ValidationError

from fastsandpm.dependencies import (
    PackageIndexRequirement,
    PathRequirement,
)
from fastsandpm.dependencies.requirements import (
    BranchGitRequirement,
    CommitGitRequirement,
    GitRequirement,
    TaggedGitRequirement,
    VersionedGitRequirement,
)
from fastsandpm.versioning import (
    CaretVersionSpecifier,
    ComparisonVersionSpecifier,
    DirectVersionSpecifier,
    LibraryVersion,
    RangeVersionSpecifier,
)


class TestPackageIndexRequirement:
    """Tests for the PackageIndexRequirement class.

    According to the documentation:
    - Registry specifier requires name and version
    - Optional registry field for alternative registries
    """

    def test_registry_dependency_simple(self) -> None:
        """Test creating a simple registry dependency."""
        dep = PackageIndexRequirement(name="time", version="1.0.0")
        assert dep.name == "time"
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert dep.index is None

    def test_registry_dependency_with_registry(self) -> None:
        """Test creating a registry dependency with custom registry."""
        dep = PackageIndexRequirement(name="time", version="1.0.0", index="my-registry")
        assert dep.name == "time"
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert dep.index == "my-registry"

    def test_registry_dependency_version_specifier_exact(self) -> None:
        """Test registry dependency with exact version."""
        dep = PackageIndexRequirement(name="time", version="2.3.4")
        assert dep.version == DirectVersionSpecifier(LibraryVersion("2.3.4"))

    def test_registry_dependency_version_specifier_caret(self) -> None:
        """Test registry dependency with caret version specifier."""
        dep = PackageIndexRequirement(name="time", version="^1.2.3")
        assert dep.version == CaretVersionSpecifier(LibraryVersion("1.2.3"))

    def test_registry_dependency_version_specifier_range(self) -> None:
        """Test registry dependency with range version specifier."""
        dep = PackageIndexRequirement(name="time", version=">=1.0.0,<2.0.0")
        assert dep.version == RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")

    def test_registry_dependency_version_specifier_comparison(self) -> None:
        """Test registry dependency with comparison version specifier."""
        dep = PackageIndexRequirement(name="time", version=">=1.0.0")
        assert dep.version == ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))

    def test_registry_dependency_name_required(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            PackageIndexRequirement(version="1.0.0")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_registry_dependency_version_required(self) -> None:
        """Test that version is required."""
        with pytest.raises(ValidationError) as exc_info:
            PackageIndexRequirement(name="time")  # type: ignore[call-arg]
        assert "version" in str(exc_info.value)


class TestGitDependency:
    """Tests for the GitDependency class.

    According to the documentation:
    - Git specifier requires git URL or project ID
    - Optional version, branch, tag, or commit (mutually exclusive)
    """

    def test_git_dependency_with_url(self) -> None:
        """Test creating a git dependency with full URL."""
        dep = GitRequirement(name="time", git="https://github.com/username/repo.git")
        assert dep.name == "time"
        assert dep.git == "https://github.com/username/repo.git"

    def test_git_dependency_with_project_id(self) -> None:
        """Test creating a git dependency with project/org ID."""
        dep = GitRequirement(name="dep2", git="SOME_ORG")
        assert dep.name == "dep2"
        assert dep.git == "SOME_ORG"

    def test_git_dependency_with_version(self) -> None:
        """Test creating a git dependency with version specifier."""
        dep = VersionedGitRequirement(
            name="time",
            git="https://github.com/username/repo.git",
            version="1.0.0",
        )
        assert dep.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_git_dependency_with_branch(self) -> None:
        """Test creating a git dependency with branch specifier."""
        dep = BranchGitRequirement(
            name="time",
            git="https://github.com/username/repo.git",
            branch="develop",
        )
        assert dep.branch == "develop"

    def test_git_dependency_with_tag(self) -> None:
        """Test creating a git dependency with tag specifier."""
        dep = TaggedGitRequirement(
            name="time",
            git="https://github.com/username/repo.git",
            tag="v1.0.0",
        )
        assert dep.tag == "v1.0.0"

    def test_git_dependency_with_commit(self) -> None:
        """Test creating a git dependency with commit specifier."""
        dep = CommitGitRequirement(
            name="time",
            git="https://github.com/username/repo.git",
            commit="deadbeef",
        )
        assert dep.commit == "deadbeef"

    def test_git_dependency_with_full_commit_hash(self) -> None:
        """Test creating a git dependency with full commit hash."""
        dep = CommitGitRequirement(
            name="time",
            git="https://github.com/username/repo.git",
            commit="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        )
        assert dep.commit == "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

    def test_git_dependency_name_required(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            GitRequirement(git="https://github.com/username/repo.git")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_git_dependency_git_required(self) -> None:
        """Test that git is required."""
        with pytest.raises(ValidationError) as exc_info:
            GitRequirement(name="time")  # type: ignore[call-arg]
        assert "git" in str(exc_info.value)


class TestPathRequirement:
    """Tests for the PathRequirement class.

    According to the documentation:
    - Path specifier requires a local path
    - Path should contain an fastsandpm manifest
    """

    def test_path_dependency_with_relative_path(self) -> None:
        """Test creating a path dependency with relative path."""
        dep = PathRequirement(name="time", path="./some/path/to/dep1")
        assert dep.name == "time"
        assert dep.path == pathlib.Path("./some/path/to/dep1")

    def test_path_dependency_with_path_object(self) -> None:
        """Test creating a path dependency with Path object."""
        path = pathlib.Path("./local/dependency")
        dep = PathRequirement(name="local-dep", path=path)
        assert dep.path == path

    def test_path_dependency_with_parent_directory(self) -> None:
        """Test creating a path dependency with parent directory reference."""
        dep = PathRequirement(name="parent-dep", path="../sibling-project")
        assert dep.path == pathlib.Path("../sibling-project")

    def test_path_dependency_with_absolute_path(self) -> None:
        """Test creating a path dependency with absolute path."""
        dep = PathRequirement(name="abs-dep", path="/absolute/path/to/dep")
        assert dep.path == pathlib.Path("/absolute/path/to/dep")

    def test_path_dependency_name_required(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            PathRequirement(path="./some/path")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_path_dependency_path_required(self) -> None:
        """Test that path is required."""
        with pytest.raises(ValidationError) as exc_info:
            PathRequirement(name="time")  # type: ignore[call-arg]
        assert "path" in str(exc_info.value)
