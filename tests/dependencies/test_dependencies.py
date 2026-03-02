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
    Dependencies,
    GitDependency,
    PathDependency,
    RegistryDependency,
)


class TestRegistryDependency:
    """Tests for the RegistryDependency class.

    According to the documentation:
    - Registry specifier requires name and version
    - Optional registry field for alternative registries
    """

    def test_registry_dependency_simple(self) -> None:
        """Test creating a simple registry dependency."""
        dep = RegistryDependency(name="time", version="1.0.0")
        assert dep.name == "time"
        assert dep.version == "1.0.0"
        assert dep.registry is None

    def test_registry_dependency_with_registry(self) -> None:
        """Test creating a registry dependency with custom registry."""
        dep = RegistryDependency(name="time", version="1.0.0", registry="my-registry")
        assert dep.name == "time"
        assert dep.version == "1.0.0"
        assert dep.registry == "my-registry"

    def test_registry_dependency_version_specifier_exact(self) -> None:
        """Test registry dependency with exact version."""
        dep = RegistryDependency(name="time", version="2.3.4")
        assert dep.version == "2.3.4"

    def test_registry_dependency_version_specifier_caret(self) -> None:
        """Test registry dependency with caret version specifier."""
        dep = RegistryDependency(name="time", version="^1.2.3")
        assert dep.version == "^1.2.3"

    def test_registry_dependency_version_specifier_range(self) -> None:
        """Test registry dependency with range version specifier."""
        dep = RegistryDependency(name="time", version=">=1.0.0,<2.0.0")
        assert dep.version == ">=1.0.0,<2.0.0"

    def test_registry_dependency_version_specifier_comparison(self) -> None:
        """Test registry dependency with comparison version specifier."""
        dep = RegistryDependency(name="time", version=">=1.0.0")
        assert dep.version == ">=1.0.0"

    def test_registry_dependency_name_required(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            RegistryDependency(version="1.0.0")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_registry_dependency_version_required(self) -> None:
        """Test that version is required."""
        with pytest.raises(ValidationError) as exc_info:
            RegistryDependency(name="time")  # type: ignore[call-arg]
        assert "version" in str(exc_info.value)


class TestGitDependency:
    """Tests for the GitDependency class.

    According to the documentation:
    - Git specifier requires git URL or project ID
    - Optional version, branch, tag, or commit (mutually exclusive)
    """

    def test_git_dependency_with_url(self) -> None:
        """Test creating a git dependency with full URL."""
        dep = GitDependency(name="time", git="https://github.com/username/repo.git")
        assert dep.name == "time"
        assert dep.git == "https://github.com/username/repo.git"
        assert dep.version is None
        assert dep.branch is None
        assert dep.tag is None
        assert dep.commit is None

    def test_git_dependency_with_project_id(self) -> None:
        """Test creating a git dependency with project/org ID."""
        dep = GitDependency(name="dep2", git="SOME_ORG")
        assert dep.name == "dep2"
        assert dep.git == "SOME_ORG"

    def test_git_dependency_with_version(self) -> None:
        """Test creating a git dependency with version specifier."""
        dep = GitDependency(
            name="time",
            git="https://github.com/username/repo.git",
            version="1.0.0",
        )
        assert dep.version == "1.0.0"
        assert dep.branch is None
        assert dep.tag is None
        assert dep.commit is None

    def test_git_dependency_with_branch(self) -> None:
        """Test creating a git dependency with branch specifier."""
        dep = GitDependency(
            name="time",
            git="https://github.com/username/repo.git",
            branch="develop",
        )
        assert dep.version is None
        assert dep.branch == "develop"
        assert dep.tag is None
        assert dep.commit is None

    def test_git_dependency_with_tag(self) -> None:
        """Test creating a git dependency with tag specifier."""
        dep = GitDependency(
            name="time",
            git="https://github.com/username/repo.git",
            tag="v1.0.0",
        )
        assert dep.version is None
        assert dep.branch is None
        assert dep.tag == "v1.0.0"
        assert dep.commit is None

    def test_git_dependency_with_commit(self) -> None:
        """Test creating a git dependency with commit specifier."""
        dep = GitDependency(
            name="time",
            git="https://github.com/username/repo.git",
            commit="deadbeef",
        )
        assert dep.version is None
        assert dep.branch is None
        assert dep.tag is None
        assert dep.commit == "deadbeef"

    def test_git_dependency_with_full_commit_hash(self) -> None:
        """Test creating a git dependency with full commit hash."""
        dep = GitDependency(
            name="time",
            git="https://github.com/username/repo.git",
            commit="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        )
        assert dep.commit == "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

    def test_git_dependency_mutually_exclusive_version_and_branch(self) -> None:
        """Test that version and branch are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(
                name="time",
                git="https://github.com/username/repo.git",
                version="1.0.0",
                branch="develop",
            )
        assert "Only one version specifier type can be used" in str(exc_info.value)

    def test_git_dependency_mutually_exclusive_version_and_tag(self) -> None:
        """Test that version and tag are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(
                name="time",
                git="https://github.com/username/repo.git",
                version="1.0.0",
                tag="v1.0.0",
            )
        assert "Only one version specifier type can be used" in str(exc_info.value)

    def test_git_dependency_mutually_exclusive_version_and_commit(self) -> None:
        """Test that version and commit are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(
                name="time",
                git="https://github.com/username/repo.git",
                version="1.0.0",
                commit="deadbeef",
            )
        assert "Only one version specifier type can be used" in str(exc_info.value)

    def test_git_dependency_mutually_exclusive_branch_and_tag(self) -> None:
        """Test that branch and tag are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(
                name="time",
                git="https://github.com/username/repo.git",
                branch="develop",
                tag="v1.0.0",
            )
        assert "Only one version specifier type can be used" in str(exc_info.value)

    def test_git_dependency_mutually_exclusive_branch_and_commit(self) -> None:
        """Test that branch and commit are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(
                name="time",
                git="https://github.com/username/repo.git",
                branch="develop",
                commit="deadbeef",
            )
        assert "Only one version specifier type can be used" in str(exc_info.value)

    def test_git_dependency_mutually_exclusive_tag_and_commit(self) -> None:
        """Test that tag and commit are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(
                name="time",
                git="https://github.com/username/repo.git",
                tag="v1.0.0",
                commit="deadbeef",
            )
        assert "Only one version specifier type can be used" in str(exc_info.value)

    def test_git_dependency_mutually_exclusive_all_specifiers(self) -> None:
        """Test that using all specifiers together fails."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(
                name="time",
                git="https://github.com/username/repo.git",
                version="1.0.0",
                branch="develop",
                tag="v1.0.0",
                commit="deadbeef",
            )
        assert "Only one version specifier type can be used" in str(exc_info.value)

    def test_git_dependency_name_required(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(git="https://github.com/username/repo.git")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_git_dependency_git_required(self) -> None:
        """Test that git is required."""
        with pytest.raises(ValidationError) as exc_info:
            GitDependency(name="time")  # type: ignore[call-arg]
        assert "git" in str(exc_info.value)


class TestPathDependency:
    """Tests for the PathDependency class.

    According to the documentation:
    - Path specifier requires a local path
    - Path should contain an fastsandpm manifest
    """

    def test_path_dependency_with_relative_path(self) -> None:
        """Test creating a path dependency with relative path."""
        dep = PathDependency(name="time", path="./some/path/to/dep1")
        assert dep.name == "time"
        assert dep.path == pathlib.Path("./some/path/to/dep1")

    def test_path_dependency_with_path_object(self) -> None:
        """Test creating a path dependency with Path object."""
        path = pathlib.Path("./local/dependency")
        dep = PathDependency(name="local-dep", path=path)
        assert dep.path == path

    def test_path_dependency_with_parent_directory(self) -> None:
        """Test creating a path dependency with parent directory reference."""
        dep = PathDependency(name="parent-dep", path="../sibling-project")
        assert dep.path == pathlib.Path("../sibling-project")

    def test_path_dependency_with_absolute_path(self) -> None:
        """Test creating a path dependency with absolute path."""
        dep = PathDependency(name="abs-dep", path="/absolute/path/to/dep")
        assert dep.path == pathlib.Path("/absolute/path/to/dep")

    def test_path_dependency_name_required(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            PathDependency(path="./some/path")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_path_dependency_path_required(self) -> None:
        """Test that path is required."""
        with pytest.raises(ValidationError) as exc_info:
            PathDependency(name="time")  # type: ignore[call-arg]
        assert "path" in str(exc_info.value)


class TestDependencies:
    """Tests for the Dependencies collection class.

    Tests parsing from various TOML-style formats into the correct
    dependency types.
    """

    def test_dependencies_empty_list(self) -> None:
        """Test creating empty dependencies."""
        deps = Dependencies([])
        assert len(deps) == 0

    def test_dependencies_from_simple_string_format(self) -> None:
        """Test parsing simple string format: name = "version".

        TOML: [dependencies]
              time = "1.0.0"
        """
        deps = Dependencies({"time": "1.0.0"})
        assert len(deps) == 1
        assert isinstance(deps[0], RegistryDependency)
        assert deps[0].name == "time"
        assert deps[0].version == "1.0.0"

    def test_dependencies_from_registry_dict_format(self) -> None:
        """Test parsing registry dict format: name = {version = "1.0.0"}.

        TOML: [dependencies]
              time = {version = "1.0.0"}
        """
        deps = Dependencies({"time": {"version": "1.0.0"}})
        assert len(deps) == 1
        assert isinstance(deps[0], RegistryDependency)
        assert deps[0].name == "time"
        assert deps[0].version == "1.0.0"

    def test_dependencies_from_registry_with_registry_field(self) -> None:
        """Test parsing registry format with custom registry.

        TOML: [dependencies]
              time = {version = "1.0.0", registry = "my-registry"}
        """
        deps = Dependencies({"time": {"version": "1.0.0", "registry": "my-registry"}})
        assert len(deps) == 1
        assert isinstance(deps[0], RegistryDependency)
        assert deps[0].name == "time"
        assert deps[0].version == "1.0.0"
        assert deps[0].registry == "my-registry"

    def test_dependencies_from_git_url_format(self) -> None:
        """Test parsing git URL format.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git"}
        """
        deps = Dependencies({"time": {"git": "https://github.com/username/repo.git"}})
        assert len(deps) == 1
        assert isinstance(deps[0], GitDependency)
        assert deps[0].name == "time"
        assert deps[0].git == "https://github.com/username/repo.git"

    def test_dependencies_from_git_project_format(self) -> None:
        """Test parsing git project ID format.

        TOML: [dependencies]
              dep2 = {git = "SOME_ORG"}
        """
        deps = Dependencies({"dep2": {"git": "SOME_ORG"}})
        assert len(deps) == 1
        assert isinstance(deps[0], GitDependency)
        assert deps[0].name == "dep2"
        assert deps[0].git == "SOME_ORG"

    def test_dependencies_from_git_with_version(self) -> None:
        """Test parsing git format with version.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", version = "1.0.0"}
        """
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "version": "1.0.0",
                }
            }
        )
        assert len(deps) == 1
        assert isinstance(deps[0], GitDependency)
        assert deps[0].version == "1.0.0"

    def test_dependencies_from_git_with_branch(self) -> None:
        """Test parsing git format with branch.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", branch = "some_branch"}
        """
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "branch": "some_branch",
                }
            }
        )
        assert len(deps) == 1
        assert isinstance(deps[0], GitDependency)
        assert deps[0].branch == "some_branch"

    def test_dependencies_from_git_with_tag(self) -> None:
        """Test parsing git format with tag.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", tag = "v1.0.0"}
        """
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "tag": "v1.0.0",
                }
            }
        )
        assert len(deps) == 1
        assert isinstance(deps[0], GitDependency)
        assert deps[0].tag == "v1.0.0"

    def test_dependencies_from_git_with_commit(self) -> None:
        """Test parsing git format with commit.

        TOML: [dependencies]
              time = {git = "https://github.com/username/repo.git", commit = "deadbeef"}
        """
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "commit": "deadbeef",
                }
            }
        )
        assert len(deps) == 1
        assert isinstance(deps[0], GitDependency)
        assert deps[0].commit == "deadbeef"

    def test_dependencies_from_path_format(self) -> None:
        """Test parsing path format.

        TOML: [dependencies]
              time = {path = "./some/path/to/dep1"}
        """
        deps = Dependencies({"time": {"path": "./some/path/to/dep1"}})
        assert len(deps) == 1
        assert isinstance(deps[0], PathDependency)
        assert deps[0].name == "time"
        assert deps[0].path == pathlib.Path("./some/path/to/dep1")

    def test_dependencies_mixed_types(self) -> None:
        """Test parsing mixed dependency types.

        TOML: [dependencies]
              registry-dep = "1.0.0"
              git-dep = {git = "https://github.com/org/repo.git"}
              path-dep = {path = "./local"}
        """
        deps = Dependencies(
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

        assert isinstance(registry, RegistryDependency)
        assert isinstance(git, GitDependency)
        assert isinstance(path, PathDependency)

    def test_dependencies_multiple_registry(self) -> None:
        """Test parsing multiple registry dependencies."""
        deps = Dependencies(
            {
                "dep1": "1.0.0",
                "dep2": "2.0.0",
                "dep3": "^3.0.0",
            }
        )
        assert len(deps) == 3
        assert all(isinstance(d, RegistryDependency) for d in deps)

    def test_dependencies_multiple_git(self) -> None:
        """Test parsing multiple git dependencies."""
        deps = Dependencies(
            {
                "dep1": {"git": "https://github.com/org/repo1.git"},
                "dep2": {"git": "https://github.com/org/repo2.git", "branch": "main"},
                "dep3": {"git": "ORG_NAME", "tag": "v1.0.0"},
            }
        )
        assert len(deps) == 3
        assert all(isinstance(d, GitDependency) for d in deps)

    def test_dependencies_iteration(self) -> None:
        """Test iterating over dependencies."""
        deps = Dependencies(
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
        deps = Dependencies(
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
        deps = Dependencies(
            {
                "dep1": "1.0.0",
            }
        )
        dep = deps.get_by_name("nonexistent")
        assert dep is None

    def test_dependencies_registry_dependencies(self) -> None:
        """Test filtering registry dependencies."""
        deps = Dependencies(
            {
                "reg1": "1.0.0",
                "git1": {"git": "https://github.com/org/repo.git"},
                "reg2": "2.0.0",
            }
        )
        registry_deps = deps.registry_dependencies()
        assert len(registry_deps) == 2
        assert all(isinstance(d, RegistryDependency) for d in registry_deps)

    def test_dependencies_git_dependencies(self) -> None:
        """Test filtering git dependencies."""
        deps = Dependencies(
            {
                "reg1": "1.0.0",
                "git1": {"git": "https://github.com/org/repo1.git"},
                "git2": {"git": "https://github.com/org/repo2.git"},
            }
        )
        git_deps = deps.git_dependencies()
        assert len(git_deps) == 2
        assert all(isinstance(d, GitDependency) for d in git_deps)

    def test_dependencies_path_dependencies(self) -> None:
        """Test filtering path dependencies."""
        deps = Dependencies(
            {
                "reg1": "1.0.0",
                "path1": {"path": "./local1"},
                "path2": {"path": "./local2"},
            }
        )
        path_deps = deps.path_dependencies()
        assert len(path_deps) == 2
        assert all(isinstance(d, PathDependency) for d in path_deps)

    def test_dependencies_from_list_format(self) -> None:
        """Test creating dependencies from a list of dicts."""
        deps = Dependencies(
            [
                {"name": "dep1", "version": "1.0.0"},
                {"name": "dep2", "git": "https://github.com/org/repo.git"},
            ]
        )
        assert len(deps) == 2
        assert isinstance(deps[0], RegistryDependency)
        assert isinstance(deps[1], GitDependency)

    def test_dependencies_duplicate_names_rejected(self) -> None:
        """Test that duplicate dependency names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Dependencies(
                [
                    {"name": "dep1", "version": "1.0.0"},
                    {"name": "dep1", "version": "2.0.0"},
                ]
            )
        assert "Duplicate dependency names" in str(exc_info.value)

    def test_dependencies_single_dict_with_name_key(self) -> None:
        """Test parsing a single dict with name key."""
        deps = Dependencies({"name": "dep1", "version": "1.0.0"})
        assert len(deps) == 1
        assert deps[0].name == "dep1"


class TestDependenciesDocumentationExamples:
    """Tests based on examples from the specifying_dependencies documentation."""

    def test_registry_simple_example(self) -> None:
        """Test example: time = "1.0.0"."""
        deps = Dependencies({"time": "1.0.0"})
        dep = deps[0]
        assert isinstance(dep, RegistryDependency)
        assert dep.name == "time"
        assert dep.version == "1.0.0"

    def test_registry_with_registry_example(self) -> None:
        """Test example: time = {registry = "my-registry", version = "1.0.0"}."""
        deps = Dependencies({"time": {"registry": "my-registry", "version": "1.0.0"}})
        dep = deps[0]
        assert isinstance(dep, RegistryDependency)
        assert dep.name == "time"
        assert dep.version == "1.0.0"
        assert dep.registry == "my-registry"

    def test_git_full_url_example(self) -> None:
        """Test example: time = {git = "https://github.com/username/repo.git"}."""
        deps = Dependencies({"time": {"git": "https://github.com/username/repo.git"}})
        dep = deps[0]
        assert isinstance(dep, GitDependency)
        assert dep.name == "time"
        assert dep.git == "https://github.com/username/repo.git"

    def test_git_project_id_example(self) -> None:
        """Test example: dep2 = {git = "SOME_ORG"}."""
        deps = Dependencies({"dep2": {"git": "SOME_ORG"}})
        dep = deps[0]
        assert isinstance(dep, GitDependency)
        assert dep.name == "dep2"
        assert dep.git == "SOME_ORG"

    def test_git_commit_example(self) -> None:
        """Test example: time = {git = "...", commit = "deadbeef"}."""
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "commit": "deadbeef",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, GitDependency)
        assert dep.commit == "deadbeef"

    def test_git_tag_example(self) -> None:
        """Test example: time = {git = "...", tag = "v1.0.0"}."""
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "tag": "v1.0.0",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, GitDependency)
        assert dep.tag == "v1.0.0"

    def test_git_branch_example(self) -> None:
        """Test example: time = {git = "...", branch = "some_branch"}."""
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "branch": "some_branch",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, GitDependency)
        assert dep.branch == "some_branch"

    def test_git_version_example(self) -> None:
        """Test example: time = {git = "...", version = "1.0.0"}."""
        deps = Dependencies(
            {
                "time": {
                    "git": "https://github.com/username/repo.git",
                    "version": "1.0.0",
                }
            }
        )
        dep = deps[0]
        assert isinstance(dep, GitDependency)
        assert dep.version == "1.0.0"

    def test_path_example(self) -> None:
        """Test example: time = {path = "./some/path/to/dep1"}."""
        deps = Dependencies({"time": {"path": "./some/path/to/dep1"}})
        dep = deps[0]
        assert isinstance(dep, PathDependency)
        assert dep.name == "time"
        assert dep.path == pathlib.Path("./some/path/to/dep1")
