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
"""Tests for relative path dependency resolution.

These tests verify that path dependencies in a manifest file are resolved
relative to the manifest file's directory, not the current working directory.
"""

from __future__ import annotations

import pathlib

from fastsandpm.dependencies import PathRequirement
from fastsandpm.manifest import get_manifest


class TestRelativePathResolution:
    """Tests that path dependencies are resolved relative to the manifest file."""

    def test_relative_path_resolved_to_absolute(self, tmp_path: pathlib.Path) -> None:
        """Test that relative paths are resolved to absolute paths relative to manifest."""
        # Create a directory structure:
        # tmp_path/
        #   project/
        #     proj.toml  (with path = "../lib")
        #   lib/
        #     proj.toml

        project_dir = tmp_path / "project"
        lib_dir = tmp_path / "lib"
        project_dir.mkdir()
        lib_dir.mkdir()

        # Create the library manifest
        lib_manifest = lib_dir / "proj.toml"
        lib_manifest.write_text("""
[package]
name = "my-lib"
version = "1.0.0"
""")

        # Create the project manifest with relative path
        project_manifest = project_dir / "proj.toml"
        project_manifest.write_text("""
[package]
name = "my-project"
version = "1.0.0"

[dependencies]
my-lib = {path = "../lib"}
""")

        # Load the manifest
        manifest = get_manifest(project_dir)

        # Check that the path dependency was resolved to an absolute path
        dep = manifest.dependencies.get_by_name("my-lib")
        assert isinstance(dep, PathRequirement)
        assert dep.path.is_absolute(), f"Path should be absolute but got: {dep.path}"
        assert dep.path == lib_dir.resolve()

    def test_absolute_path_unchanged(self, tmp_path: pathlib.Path) -> None:
        """Test that absolute paths remain unchanged."""
        project_dir = tmp_path / "project"
        lib_dir = tmp_path / "lib"
        project_dir.mkdir()
        lib_dir.mkdir()

        # Create the library manifest
        lib_manifest = lib_dir / "proj.toml"
        lib_manifest.write_text("""
[package]
name = "my-lib"
version = "1.0.0"
""")

        # Create the project manifest with absolute path
        abs_path = lib_dir.resolve()
        project_manifest = project_dir / "proj.toml"
        project_manifest.write_text(f"""
[package]
name = "my-project"
version = "1.0.0"

[dependencies]
my-lib = {{path = "{abs_path}"}}
""")

        # Load the manifest
        manifest = get_manifest(project_dir)

        # Check that the absolute path is preserved
        dep = manifest.dependencies.get_by_name("my-lib")
        assert isinstance(dep, PathRequirement)
        assert dep.path == abs_path

    def test_relative_path_with_current_directory(self, tmp_path: pathlib.Path) -> None:
        """Test that ./ relative paths are resolved correctly."""
        project_dir = tmp_path / "project"
        lib_dir = project_dir / "lib"
        project_dir.mkdir()
        lib_dir.mkdir()

        # Create the library manifest
        lib_manifest = lib_dir / "proj.toml"
        lib_manifest.write_text("""
[package]
name = "my-lib"
version = "1.0.0"
""")

        # Create the project manifest with ./ relative path
        project_manifest = project_dir / "proj.toml"
        project_manifest.write_text("""
[package]
name = "my-project"
version = "1.0.0"

[dependencies]
my-lib = {path = "./lib"}
""")

        # Load the manifest
        manifest = get_manifest(project_dir)

        # Check that the path dependency was resolved to an absolute path
        dep = manifest.dependencies.get_by_name("my-lib")
        assert isinstance(dep, PathRequirement)
        assert dep.path.is_absolute()
        assert dep.path == lib_dir.resolve()

    def test_optional_dependencies_relative_path(self, tmp_path: pathlib.Path) -> None:
        """Test that relative paths in optional dependencies are also resolved."""
        project_dir = tmp_path / "project"
        lib_dir = tmp_path / "dev-lib"
        project_dir.mkdir()
        lib_dir.mkdir()

        # Create the library manifest
        lib_manifest = lib_dir / "proj.toml"
        lib_manifest.write_text("""
[package]
name = "dev-lib"
version = "0.1.0"
""")

        # Create the project manifest with relative path in optional dependencies
        project_manifest = project_dir / "proj.toml"
        project_manifest.write_text("""
[package]
name = "my-project"
version = "1.0.0"

[optional_dependencies.dev]
dev-lib = {path = "../dev-lib"}
""")

        # Load the manifest
        manifest = get_manifest(project_dir)

        # Check that the path dependency in optional dependencies was resolved
        assert "dev" in manifest.optional_dependencies
        opt_deps = manifest.optional_dependencies["dev"]
        dep = opt_deps.get_by_name("dev-lib")
        assert isinstance(dep, PathRequirement)
        assert dep.path.is_absolute()
        assert dep.path == lib_dir.resolve()

    def test_deeply_nested_relative_path(self, tmp_path: pathlib.Path) -> None:
        """Test that deeply nested relative paths are resolved correctly."""
        # Create a directory structure:
        # tmp_path/
        #   packages/
        #     project/
        #       proj.toml  (with path = "../../lib")
        #   lib/
        #     proj.toml

        project_dir = tmp_path / "packages" / "project"
        lib_dir = tmp_path / "lib"
        project_dir.mkdir(parents=True)
        lib_dir.mkdir()

        # Create the library manifest
        lib_manifest = lib_dir / "proj.toml"
        lib_manifest.write_text("""
[package]
name = "my-lib"
version = "1.0.0"
""")

        # Create the project manifest with relative path going up two levels
        project_manifest = project_dir / "proj.toml"
        project_manifest.write_text("""
[package]
name = "my-project"
version = "1.0.0"

[dependencies]
my-lib = {path = "../../lib"}
""")

        # Load the manifest
        manifest = get_manifest(project_dir)

        # Check that the path dependency was resolved correctly
        dep = manifest.dependencies.get_by_name("my-lib")
        assert isinstance(dep, PathRequirement)
        assert dep.path.is_absolute()
        assert dep.path == lib_dir.resolve()
