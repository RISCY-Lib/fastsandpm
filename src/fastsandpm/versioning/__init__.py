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
"""Module for handling semantic versioning and version range specifications.

This module provides classes and functions for parsing, comparing, and
resolving semantic versions. It supports:

- Semantic versioning with major.minor.patch format (e.g., "1.2.3")
- Optional pre-release identifiers (e.g., "1.2.3.alpha")
- Version constraints with comparison operators (e.g., ">=1.0.0", "<2.0.0")
- Version ranges combining multiple constraints (e.g., ">1.0.0,<2.0.0")

Classes:
    PreReleaseStage: Enum for a pre-release stage.
    LibraryVersion: Represents and compares semantic versions.
    VersionSpecifier: Base class for version specifications.
    DirectVersionSpecifier: Matches a single version exactly.
    CaretVersionSpecifier: Matches semver-compatible versions.
    ComparisonVersionSpecifier: Matches versions using comparison operators.
    RangeVersionSpecifier: Matches versions matching a range specification.

Functions:
    meets_constraints: Check if a version meets specified constraints.
    find_compatible_version: Find the best matching version from available options.
    version_specifier_from_str: Create a version specifier from a string.
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
