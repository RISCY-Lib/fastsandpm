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
"""Tests for fastsandpm.manifest Package section.

These tests verify the contents of the [package] section as defined in the manifest_format
documentation. The package section is the only mandatory section in a manifest and contains:
- name: unique identifier for the package
- version: SemVer formatted version string
- description: plain-text summary of the package
- authors: optional field for author information
- readme: optional field pointing to README file
"""

from __future__ import annotations

import pathlib

import pytest
from pydantic import ValidationError

from fastsandpm.manifest import Package
from fastsandpm.versioning import LibraryVersion, PreReleaseStage


class TestPackageName:
    """Tests for the 'name' field of the Package section."""

    def test_name_is_required(self) -> None:
        """Test that name field is required."""
        with pytest.raises(ValidationError) as exc_info:
            Package(version="1.0.0", description="A test package")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_name_accepts_valid_string(self) -> None:
        """Test that name accepts a valid string identifier."""
        package = Package(name="my-package", version="1.0.0", description="A test package")
        assert package.name == "my-package"

    def test_name_with_underscores(self) -> None:
        """Test that name accepts underscores."""
        package = Package(name="my_package", version="1.0.0", description="A test package")
        assert package.name == "my_package"

    def test_name_with_numbers(self) -> None:
        """Test that name accepts numbers."""
        package = Package(name="package123", version="1.0.0", description="A test package")
        assert package.name == "package123"

    def test_name_rejects_empty_string(self) -> None:
        """Test that name field rejects empty strings."""
        with pytest.raises(ValidationError) as exc_info:
            Package(name="", version="1.0.0", description="A test package")
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_name_rejects_whitespace_only(self) -> None:
        """Test that name field rejects whitespace-only strings."""
        with pytest.raises(ValidationError) as exc_info:
            Package(name="   ", version="1.0.0", description="A test package")
        assert "cannot be empty" in str(exc_info.value).lower()


class TestPackageVersion:
    """Tests for the 'version' field of the Package section.

    According to the documentation, version must be formatted in accordance with SemVer.
    """

    def test_version_is_required(self) -> None:
        """Test that version field is required."""
        with pytest.raises(ValidationError) as exc_info:
            Package(name="test-package", description="A test package")  # type: ignore[call-arg]
        assert "version" in str(exc_info.value)

    def test_version_accepts_semver_format(self) -> None:
        """Test that version accepts standard SemVer format (MAJOR.MINOR.PATCH)."""
        package = Package(name="test-package", version="1.2.3", description="A test package")
        assert package.version == LibraryVersion("1.2.3")

    def test_version_rejects_major_only(self) -> None:
        """Test that version rejects major version only (must be MAJOR.MINOR.PATCH)."""
        with pytest.raises(ValidationError):
            Package(name="test-package", version="1", description="A test package")

    def test_version_rejects_major_minor(self) -> None:
        """Test that version rejects major.minor format (must be MAJOR.MINOR.PATCH)."""
        with pytest.raises(ValidationError):
            Package(name="test-package", version="1.0", description="A test package")

    def test_version_accepts_prerelease(self) -> None:
        """Test that version accepts pre-release identifiers."""
        package = Package(name="test-package", version="1.0.0-alpha", description="A test package")
        assert package.version == LibraryVersion("1.0.0-alpha")
        assert package.version.pre_stage == PreReleaseStage.ALPHA
        assert package.version.pre is None

    def test_version_accepts_prerelease_with_number(self) -> None:
        """Test that version accepts pre-release with numeric identifier."""
        package = Package(name="test-package", version="1.0.0-beta1", description="A test package")
        assert package.version == LibraryVersion("1.0.0-beta1")
        assert package.version.pre_stage == PreReleaseStage.BETA
        assert package.version.pre == 1

    def test_version_accepts_abridged_alpha_prerelease(self) -> None:
        """Test that version accepts abridged alpha pre-release notation (e.g., 1.0.0-a1)."""
        package = Package(name="test-package", version="1.0.0-a1", description="A test package")
        assert package.version == LibraryVersion("1.0.0-a1")
        assert package.version.pre_stage == PreReleaseStage.ALPHA
        assert package.version.pre == 1

    def test_version_accepts_abridged_beta_prerelease(self) -> None:
        """Test that version accepts abridged beta pre-release notation (e.g., 1.0.0-b2)."""
        package = Package(name="test-package", version="1.0.0-b2", description="A test package")
        assert package.version == LibraryVersion("1.0.0-b2")
        assert package.version.pre_stage == PreReleaseStage.BETA
        assert package.version.pre == 2

    def test_version_accepts_abridged_rc_prerelease(self) -> None:
        """Test that version accepts abridged release candidate notation (e.g., 1.2.1-rc3)."""
        package = Package(name="test-package", version="1.2.1-rc3", description="A test package")
        assert package.version == LibraryVersion("1.2.1-rc3")
        assert package.version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert package.version.pre == 3

    def test_version_rejects_build_metadata(self) -> None:
        """Test that version rejects build metadata (+ suffix)."""
        with pytest.raises(ValidationError):
            Package(name="test-package", version="1.0.0+build.123", description="A test package")

    def test_version_rejects_prerelease_with_build_metadata(self) -> None:
        """Test that version rejects pre-release versions with build metadata."""
        with pytest.raises(ValidationError):
            Package(
                name="test-package", version="1.0.0-rc.1+build.456", description="A test package"
            )

    def test_version_zero_major(self) -> None:
        """Test that version accepts zero major version for initial development."""
        package = Package(name="test-package", version="0.1.0", description="A test package")
        assert package.version == LibraryVersion("0.1.0")


class TestPackageDescription:
    """Tests for the 'description' field of the Package section.

    According to the documentation, description is a short summary treated as plain-text.
    """

    def test_description_is_optional(self) -> None:
        """Test that description field is required."""
        package = Package(name="test-package", version="1.0.0")  # type: ignore[call-arg]
        assert package.description == ""

    def test_description_accepts_plain_text(self) -> None:
        """Test that description accepts a plain text string."""
        description = "A short summary of the package"
        package = Package(name="test-package", version="1.0.0", description=description)
        assert package.description == description

    def test_description_accepts_empty_string(self) -> None:
        """Test that description accepts an empty string."""
        package = Package(name="test-package", version="1.0.0", description="")
        assert package.description == ""

    def test_description_preserves_whitespace(self) -> None:
        """Test that description preserves internal whitespace."""
        description = "A package   with   extra   spaces"
        package = Package(name="test-package", version="1.0.0", description=description)
        assert package.description == description

    def test_description_accepts_special_characters(self) -> None:
        """Test that description accepts special characters."""
        description = "A package for RTL/HDL design & verification!"
        package = Package(name="test-package", version="1.0.0", description=description)
        assert package.description == description


class TestPackageAuthors:
    """Tests for the 'authors' field of the Package section.

    According to the documentation:
    - This field is optional
    - If not specified, it defaults to not including any author information
    - Can be an array of strings (with optional email in angle brackets)
    - Can be an array of dictionaries with 'name' and 'email' keys
    """

    def test_authors_is_optional(self) -> None:
        """Test that authors field is optional and defaults to None."""
        package = Package(name="test-package", version="1.0.0", description="A test package")
        assert package.authors is None

    def test_authors_accepts_single_string(self) -> None:
        """Test that authors accepts a single string."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors="John Doe",
        )
        assert package.authors == "John Doe"

    def test_authors_accepts_string_with_email(self) -> None:
        """Test that authors accepts a string with email in angle brackets."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors="John Doe <john.doe@example.com>",
        )
        assert package.authors == "John Doe <john.doe@example.com>"

    def test_authors_accepts_list_of_strings(self) -> None:
        """Test that authors accepts a list of strings."""
        authors = ["John Doe", "Jane Smith"]
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors=authors,
        )
        assert package.authors == authors

    def test_authors_accepts_list_of_strings_with_emails(self) -> None:
        """Test that authors accepts a list of strings with emails."""
        authors = [
            "John Doe <john.doe@example.com>",
            "Jane Smith <jane.smith@example.com>",
        ]
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors=authors,
        )
        assert package.authors == authors

    def test_authors_accepts_dict_with_name_and_email(self) -> None:
        """Test that authors accepts a dictionary with name and email keys."""
        authors = {"name": "John Doe", "email": "john.doe@example.com"}
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors=authors,
        )
        assert package.authors == authors

    def test_authors_accepts_dict_with_name_only(self) -> None:
        """Test that authors accepts a dictionary with only name key."""
        authors = {"name": "John Doe"}
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors=authors,
        )
        assert package.authors == authors

    def test_authors_accepts_empty_list(self) -> None:
        """Test that authors accepts an empty list."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors=[],
        )
        assert package.authors == []

    def test_authors_explicitly_set_to_none(self) -> None:
        """Test that authors can be explicitly set to None."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            authors=None,
        )
        assert package.authors is None


class TestPackageReadme:
    """Tests for the 'readme' field of the Package section.

    According to the documentation:
    - This field is optional
    - If not specified, it defaults to not including any readme information
    - Points to the relative location of a README markdown or text file
    - Is relative to the location of the manifest file
    """

    def test_readme_is_optional(self) -> None:
        """Test that readme field is optional and defaults to None."""
        package = Package(name="test-package", version="1.0.0", description="A test package")
        assert package.readme is None

    def test_readme_accepts_path(self) -> None:
        """Test that readme accepts a Path object."""
        readme_path = pathlib.Path("README.md")
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            readme=readme_path,
        )
        assert package.readme == readme_path

    def test_readme_accepts_string_path(self) -> None:
        """Test that readme accepts a string path and converts to Path."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            readme="README.md",  # type: ignore[call-arg]
        )
        assert package.readme == pathlib.Path("README.md")

    def test_readme_accepts_relative_path(self) -> None:
        """Test that readme accepts a relative path."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            readme="docs/README.md",  # type: ignore[call-arg]
        )
        assert package.readme == pathlib.Path("docs/README.md")

    def test_readme_accepts_txt_extension(self) -> None:
        """Test that readme accepts a .txt file extension."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            readme="README.txt",  # type: ignore[call-arg]
        )
        assert package.readme == pathlib.Path("README.txt")

    def test_readme_accepts_rst_extension(self) -> None:
        """Test that readme accepts a .rst file extension."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            readme="README.rst",  # type: ignore[call-arg]
        )
        assert package.readme == pathlib.Path("README.rst")

    def test_readme_explicitly_set_to_none(self) -> None:
        """Test that readme can be explicitly set to None."""
        package = Package(
            name="test-package",
            version="1.0.0",
            description="A test package",
            readme=None,
        )
        assert package.readme is None


class TestPackageComplete:
    """Integration tests for complete Package configurations."""

    def test_minimal_valid_package(self) -> None:
        """Test creating a package with only required fields."""
        package = Package(
            name="minimal-package",
            version="1.0.0",
            description="A minimal package",
        )
        assert package.name == "minimal-package"
        assert package.version == LibraryVersion("1.0.0")
        assert package.description == "A minimal package"
        assert package.authors is None
        assert package.readme is None

    def test_complete_package_with_all_fields(self) -> None:
        """Test creating a package with all fields populated."""
        package = Package(
            name="complete-package",
            version="2.1.0",
            description="A complete package with all fields",
            authors=["John Doe <john@example.com>", "Jane Smith <jane@example.com>"],
            readme="README.md",  # type: ignore
        )
        assert package.name == "complete-package"
        assert package.version == LibraryVersion("2.1.0")
        assert package.description == "A complete package with all fields"
        assert package.authors == ["John Doe <john@example.com>", "Jane Smith <jane@example.com>"]
        assert package.readme == pathlib.Path("README.md")

    def test_package_from_dict(self) -> None:
        """Test creating a package from a dictionary (simulating TOML parsing)."""
        data = {
            "name": "dict-package",
            "version": "0.5.0",
            "description": "A package created from dict",
            "authors": ["Test Author"],
            "readme": "README.md",
        }
        package = Package(**data)
        assert package.name == "dict-package"
        assert package.version == LibraryVersion("0.5.0")
        assert package.description == "A package created from dict"
        assert package.authors == ["Test Author"]
        assert package.readme == pathlib.Path("README.md")

    def test_package_model_dump(self) -> None:
        """Test that package can be serialized back to a dictionary."""
        package = Package(
            name="serializable-package",
            version="1.0.0",
            description="A serializable package",
            authors="Single Author",
            readme="README.md",  # type: ignore[call-arg]
        )
        data = package.model_dump()
        assert data["name"] == "serializable-package"
        assert data["version"] == "1.0.0"
        assert data["description"] == "A serializable package"
        assert data["authors"] == "Single Author"
        # Note: Path objects may be serialized differently depending on Pydantic config
        assert data["readme"] == pathlib.Path("README.md")
