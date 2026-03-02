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
"""Tests for fastsandpm.manifest.get_manifest function.

These tests verify the get_manifest function which loads and parses
proj.toml manifest files from repository paths.
"""

from __future__ import annotations

import pathlib

import pytest

import fastsandpm
from fastsandpm.dependencies import GitRequirement, PackageIndexRequirement, PathRequirement
from fastsandpm.dependencies.requirements import (
    BranchGitRequirement,
    CommitGitRequirement,
    TaggedGitRequirement,
    VersionedGitRequirement,
)
from fastsandpm.manifest import (
    MANIFEST_FILENAME,
    Manifest,
    ManifestNotFoundError,
    ManifestParseError,
    get_manifest,
)
from fastsandpm.versioning.library_version import LibraryVersion
from fastsandpm.versioning.specifier import CaretVersionSpecifier, DirectVersionSpecifier


class TestGetManifestBasic:
    """Tests for basic get_manifest functionality."""

    def test_get_manifest_minimal(self, tmp_path: pathlib.Path) -> None:
        """Test loading a minimal valid manifest."""
        manifest_content = """
[package]
name = "test-package"
version = "1.0.0"
description = "A test package"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert isinstance(manifest, Manifest)
        assert manifest.package.name == "test-package"
        assert str(manifest.package.version) == "1.0.0"
        assert manifest.package.description == "A test package"

    def test_get_manifest_with_all_package_fields(self, tmp_path: pathlib.Path) -> None:
        """Test loading a manifest with all package fields."""
        manifest_content = """
[package]
name = "complete-package"
version = "2.1.0"
description = "A complete test package"
authors = ["John Doe <john@example.com>", "Jane Smith"]
readme = "README.md"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert manifest.package.name == "complete-package"
        assert str(manifest.package.version) == "2.1.0"
        assert manifest.package.description == "A complete test package"
        assert manifest.package.authors == ["John Doe <john@example.com>", "Jane Smith"]
        assert manifest.package.readme == pathlib.Path("README.md")

    def test_get_manifest_returns_empty_dependencies_when_not_specified(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Test that missing dependencies section returns empty Dependencies."""
        manifest_content = """
[package]
name = "no-deps"
version = "1.0.0"
description = "Package without dependencies"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert len(manifest.dependencies) == 0
        assert manifest.optional_dependencies == {}


class TestGetManifestWithDependencies:
    """Tests for get_manifest with various dependency types."""

    def test_get_manifest_with_registry_dependencies(self, tmp_path: pathlib.Path) -> None:
        """Test loading manifest with registry dependencies."""
        manifest_content = """
[package]
name = "with-deps"
version = "1.0.0"
description = "Package with registry dependencies"

[dependencies]
dep1 = "1.0.0"
dep2 = "^2.0.0"
dep3 = ">=1.0.0,<2.0.0"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert len(manifest.dependencies) == 3
        dep1 = manifest.dependencies.get_by_name("dep1")
        assert isinstance(dep1, PackageIndexRequirement)
        assert dep1.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_get_manifest_with_git_dependencies(self, tmp_path: pathlib.Path) -> None:
        """Test loading manifest with git dependencies."""
        manifest_content = """
[package]
name = "with-git-deps"
version = "1.0.0"
description = "Package with git dependencies"

[dependencies]
git_dep1 = {git = "https://github.com/org/repo.git"}
git_dep2 = {git = "https://github.com/org/repo2.git", branch = "develop"}
git_dep3 = {git = "https://github.com/org/repo3.git", tag = "v1.0.0"}
git_dep4 = {git = "https://github.com/org/repo4.git", commit = "abc123"}
git_dep5 = {git = "ORG_NAME", version = "1.0.0"}
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert len(manifest.dependencies) == 5

        dep1 = manifest.dependencies.get_by_name("git_dep1")
        assert isinstance(dep1, GitRequirement)
        assert dep1.git == "https://github.com/org/repo.git"

        dep2 = manifest.dependencies.get_by_name("git_dep2")
        assert isinstance(dep2, BranchGitRequirement)
        assert dep2.branch == "develop"

        dep3 = manifest.dependencies.get_by_name("git_dep3")
        assert isinstance(dep3, TaggedGitRequirement)
        assert dep3.tag == "v1.0.0"

        dep4 = manifest.dependencies.get_by_name("git_dep4")
        assert isinstance(dep4, CommitGitRequirement)
        assert dep4.commit == "abc123"

        dep5 = manifest.dependencies.get_by_name("git_dep5")
        assert isinstance(dep5, VersionedGitRequirement)
        assert dep5.version == DirectVersionSpecifier(LibraryVersion("1.0.0"))

    def test_get_manifest_with_path_dependencies(self, tmp_path: pathlib.Path) -> None:
        """Test loading manifest with path dependencies."""
        manifest_content = """
[package]
name = "with-path-deps"
version = "1.0.0"
description = "Package with path dependencies"

[dependencies]
local_dep = {path = "./local_utils"}
parent_dep = {path = "../sibling_project"}
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert len(manifest.dependencies) == 2

        local = manifest.dependencies.get_by_name("local_dep")
        assert isinstance(local, PathRequirement)
        assert local.path == pathlib.Path("./local_utils")

        parent = manifest.dependencies.get_by_name("parent_dep")
        assert isinstance(parent, PathRequirement)
        assert parent.path == pathlib.Path("../sibling_project")

    def test_get_manifest_with_mixed_dependencies(self, tmp_path: pathlib.Path) -> None:
        """Test loading manifest with mixed dependency types."""
        manifest_content = """
[package]
name = "mixed-deps"
version = "1.0.0"
description = "Package with mixed dependencies"

[dependencies]
uvm_utils = "^1.0.0"
std_cells = ">0.1.0"
amba_interfaces = {git = "PADC_AMBA_IP", branch = "main"}
local_utils = {path = "./local_utils"}
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert len(manifest.dependencies) == 4
        assert len([
            d for d in manifest.dependencies if isinstance(d, PackageIndexRequirement)
        ]) == 2
        assert len([d for d in manifest.dependencies if isinstance(d, GitRequirement)]) == 1
        assert len([d for d in manifest.dependencies if isinstance(d, PathRequirement)]) == 1


class TestGetManifestWithOptionalDependencies:
    """Tests for get_manifest with optional dependencies."""

    def test_get_manifest_with_optional_dependencies_list_format(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Test loading manifest with optional dependencies in list format."""
        manifest_content = """
[package]
name = "with-optional-deps"
version = "1.0.0"
description = "Package with optional dependencies"

[optional_dependencies]
uvm = [
    {name = "uvm_utils", version = "^1.0.0"},
    {name = "improved_uvm_ral", version = ">0.1.0"},
]
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert "uvm" in manifest.optional_dependencies
        assert len(manifest.optional_dependencies["uvm"]) == 2

    def test_get_manifest_with_optional_dependencies_table_format(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Test loading manifest with optional dependencies in table format."""
        manifest_content = """
[package]
name = "with-optional-deps"
version = "1.0.0"
description = "Package with optional dependencies"

[optional_dependencies.dev]
debug_tools = "1.0.0"
test_framework = "^2.0.0"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert "dev" in manifest.optional_dependencies
        assert len(manifest.optional_dependencies["dev"]) == 2


class TestGetManifestErrors:
    """Tests for get_manifest error handling."""

    def test_get_manifest_not_found(self, tmp_path: pathlib.Path) -> None:
        """Test that ManifestNotFoundError is raised when file doesn't exist."""
        with pytest.raises(ManifestNotFoundError) as exc_info:
            get_manifest(tmp_path)

        assert exc_info.value.path == tmp_path
        assert MANIFEST_FILENAME in str(exc_info.value)

    def test_get_manifest_invalid_toml(self, tmp_path: pathlib.Path) -> None:
        """Test that ManifestParseError is raised for invalid TOML."""
        manifest_content = """
[package
name = "broken"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        with pytest.raises(ManifestParseError) as exc_info:
            get_manifest(tmp_path)

        assert exc_info.value.path == tmp_path
        assert "Invalid TOML syntax" in str(exc_info.value)

    def test_get_manifest_missing_required_field(self, tmp_path: pathlib.Path) -> None:
        """Test that ManifestParseError is raised for missing required fields."""
        manifest_content = """
[package]
name = "incomplete"
# Missing version and description
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        with pytest.raises(ManifestParseError) as exc_info:
            get_manifest(tmp_path)

        assert exc_info.value.path == tmp_path

    def test_get_manifest_invalid_version_format(self, tmp_path: pathlib.Path) -> None:
        """Test that ManifestParseError is raised for invalid version."""
        manifest_content = """
[package]
name = "bad-version"
version = "not-a-version"
description = "Package with invalid version"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        with pytest.raises(ManifestParseError):
            get_manifest(tmp_path)

    def test_get_manifest_directory_instead_of_file(self, tmp_path: pathlib.Path) -> None:
        """Test that ManifestParseError is raised when proj.toml is a directory."""
        (tmp_path / MANIFEST_FILENAME).mkdir()

        with pytest.raises(ManifestParseError) as exc_info:
            get_manifest(tmp_path)

        assert "not a file" in str(exc_info.value)

    def test_get_manifest_empty_path(self, tmp_path: pathlib.Path) -> None:
        """Test loading from a non-existent path."""
        non_existent = tmp_path / "does_not_exist"

        with pytest.raises(ManifestNotFoundError):
            get_manifest(non_existent)


class TestGetManifestPathHandling:
    """Tests for path handling in get_manifest."""

    def test_get_manifest_accepts_string_path(self, tmp_path: pathlib.Path) -> None:
        """Test that get_manifest accepts string paths."""
        manifest_content = """
[package]
name = "string-path"
version = "1.0.0"
description = "Test with string path"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        # Pass as string instead of Path
        manifest = get_manifest(str(tmp_path))  # type: ignore[arg-type]

        assert manifest.package.name == "string-path"

    def test_get_manifest_accepts_path_object(self, tmp_path: pathlib.Path) -> None:
        """Test that get_manifest accepts pathlib.Path objects."""
        manifest_content = """
[package]
name = "path-object"
version = "1.0.0"
description = "Test with Path object"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        assert manifest.package.name == "path-object"


class TestGetManifestIntegration:
    """Integration tests for get_manifest matching documentation examples."""

    def test_documentation_example_manifest(self, tmp_path: pathlib.Path) -> None:
        """Test the example from manifest_format documentation."""
        manifest_content = """
[package]
name = "my-rtl-project"
version = "1.0.0"
description = "An RTL project using fastsandpm"

[dependencies]
uvm_utils = "^1.0.0"
std_cells = ">0.1.0"
amba_interfaces = {git = "PADC_AMBA_IP", branch = "main"}
local_utils = {path = "./local_utils"}
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        manifest = get_manifest(tmp_path)

        # Verify package section
        assert manifest.package.name == "my-rtl-project"
        assert str(manifest.package.version) == "1.0.0"
        assert manifest.package.description == "An RTL project using fastsandpm"

        # Verify dependencies
        assert len(manifest.dependencies) == 4

        uvm_utils = manifest.dependencies.get_by_name("uvm_utils")
        assert isinstance(uvm_utils, PackageIndexRequirement)
        assert uvm_utils.version == CaretVersionSpecifier(LibraryVersion("1.0.0"))

        amba = manifest.dependencies.get_by_name("amba_interfaces")
        assert isinstance(amba, BranchGitRequirement)
        assert amba.git == "PADC_AMBA_IP"
        assert amba.branch == "main"

        local = manifest.dependencies.get_by_name("local_utils")
        assert isinstance(local, PathRequirement)

    def test_top_level_import_works(self, tmp_path: pathlib.Path) -> None:
        """Test that get_manifest is accessible from top-level fastsandpm import."""
        manifest_content = """
[package]
name = "top-level-test"
version = "1.0.0"
description = "Testing top-level import"
"""
        (tmp_path / MANIFEST_FILENAME).write_text(manifest_content)

        # Use the top-level import as shown in documentation
        manifest = fastsandpm.get_manifest(tmp_path)

        assert manifest.package.name == "top-level-test"

    def test_exception_classes_accessible_from_top_level(self) -> None:
        """Test that exception classes are accessible from fastsandpm module."""
        assert fastsandpm.ManifestNotFoundError is ManifestNotFoundError
        assert fastsandpm.ManifestParseError is ManifestParseError

    def test_manifest_class_accessible_from_top_level(self) -> None:
        """Test that Manifest class is accessible from fastsandpm module."""
        assert fastsandpm.Manifest is Manifest
