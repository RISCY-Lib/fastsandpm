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
"""Semantic versioning and version specification subpackage.

This subpackage provides classes and functions for parsing, comparing, and
resolving semantic versions used throughout FastSandPM. It supports standard
semantic versioning with extensions for pre-release identifiers.

Supported Version Formats:
    - Standard: ``major.minor.patch`` (e.g., "1.2.3")
    - Pre-release with separator: ``major.minor.patch-pre`` (e.g., "1.2.3-alpha")
    - Pre-release with dot: ``major.minor.patch.pre`` (e.g., "1.2.3.rc1")

Supported Specifier Formats:
    - Direct version: ``"1.0.0"`` (exact match)
    - Caret requirement: ``"^1.2.3"`` (semver-compatible)
    - Comparison: ``">=1.0.0"``, ``"<2.0.0"``
    - Range: ``">=1.0.0,<2.0.0"``

Classes:
    PreReleaseStage: Enum for pre-release stages (ALPHA, BETA, RELEASE_CANDIDATE).
    LibraryVersion: Represents and compares semantic versions.
    VersionSpecifier: Abstract base class for version specifications.
    DirectVersionSpecifier: Matches a single version exactly.
    CaretVersionSpecifier: Matches semver-compatible versions (^x.y.z).
    ComparisonVersionSpecifier: Matches using comparison operators.
    RangeVersionSpecifier: Matches versions within a range.

Functions:
    meets_constraints: Check if a version meets specified constraints.
    find_compatible_version: Find the best matching version from available options.
    version_specifier_from_str: Parse a version specifier string.

Example:
    >>> from fastsandpm.versioning import LibraryVersion, version_specifier_from_str
    >>> v = LibraryVersion("1.2.3")
    >>> spec = version_specifier_from_str("^1.0.0")
    >>> spec.satisfied_by(v)
    True
"""

from __future__ import annotations

from fastsandpm.versioning.library_version import LibraryVersion, PreReleaseStage
from fastsandpm.versioning.specifier import (
    CaretVersionSpecifier,
    ComparisonVersionSpecifier,
    DirectVersionSpecifier,
    RangeVersionSpecifier,
    VersionSpecifier,
    find_compatible_version,
    meets_constraints,
    version_specifier_from_str,
)

__all__ = [
    "LibraryVersion",
    "PreReleaseStage",
    "VersionSpecifier",
    "DirectVersionSpecifier",
    "CaretVersionSpecifier",
    "ComparisonVersionSpecifier",
    "RangeVersionSpecifier",
    "meets_constraints",
    "find_compatible_version",
    "version_specifier_from_str",
]
