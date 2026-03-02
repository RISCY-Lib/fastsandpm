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
    LibraryVersion: Represents and compares semantic versions.
    VersionConstraint: Represents a single version constraint.
    VersionRange: Represents a range of acceptable versions.

Functions:
    is_version_range: Check if a string is a version range specification.
    resolve_version_range: Find the best matching version from available options.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Literal, Self

from .library_version import LibraryVersion


class VersionSpecifier(ABC):
    """Base class for version specifications."""

    @abstractmethod
    def meets(self, version: LibraryVersion) -> bool:
        """Check if a version meets the specification.

        Args:
            version: The version to check.

        Returns:
            True if the version meets the specification, False otherwise.
        """


class DirectVersionSpecifier(VersionSpecifier):
    """Version specification that matches a single version."""

    def __init__(self, version: LibraryVersion) -> None:
        """Initialize a DirectVersionSpecifier.

        Args:
            version: The exact version to match.
        """
        self.version = version

    def meets(self, version: LibraryVersion) -> bool:
        """Check if a version meets the specification.

        Args:
            version: The version to check.

        Returns:
            True if the version matches exactly, False otherwise.
        """
        return self.version == version

    def __eq__(self, value: object) -> bool:
        """Check for equality between this DirectVersionSpecifier and the object"""
        if not isinstance(value, DirectVersionSpecifier):
            return False
        return self.version == value.version

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        """Return string representation of the specifier."""
        return f"DirectVersionSpecifier({self.version!s})"

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create a DirectVersionSpecifier from string.

        Returns:
            The created specifier.

        Raises:
            ValueError: If the value can't be converted to a valid DirectVersionSpecifier
        """
        return cls(LibraryVersion(value.strip()))


class CaretVersionSpecifier(VersionSpecifier):
    """Version specification for caret requirements (^x.y.z).

    Caret requirements allow semver-compatible updates:
    - ^1.2.3 allows >=1.2.3, <2.0.0
    - ^0.2.3 allows >=0.2.3, <0.3.0 (0.x.x versions treat minor as breaking)
    """

    def __init__(self, version: LibraryVersion) -> None:
        """Initialize a CaretVersionSpecifier.

        Args:
            version: The base version for the caret requirement.
        """
        self.version = version

    def meets(self, version: LibraryVersion) -> bool:
        """Check if a version meets the caret specification.

        Args:
            version: The version to check.

        Returns:
            True if the version is semver-compatible, False otherwise.
        """
        # Exclude pre-release versions and versions less than this version
        if version < self.version:
            return False

        # Must have same major
        if version.major != self.version.major:
            return False

        # For 0.x.x versions, minor bump is considered breaking
        if self.version.major == 0:
            # Must have same major and minor
            if version.minor != self.version.minor:
                return False

        return True

    def __eq__(self, value: object, /) -> bool:
        """Check for equality between this DirectVersionSpecifier and the object"""
        if not isinstance(value, CaretVersionSpecifier):
            return False
        return self.version == value.version

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        """Return string representation of the specifier."""
        return f"CaretVersionSpecifier(^{self.version!s})"

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create a CaretVersionSpecifier from string.

        Returns:
            The created specifier.

        Raises:
            ValueError: If the value can't be converted to a valid DirectVersionSpecifier
        """
        if not value[0] == "^":
            raise ValueError(f"Cannot create CaretVersionSpecifier from string: {value}")

        return cls(LibraryVersion(value[1:].strip()))


ComparisonOperator = Literal[">=", "<=", ">", "<"]


class ComparisonVersionSpecifier(VersionSpecifier):
    """Version specification for comparison requirements (>=, <=, >, <).
    """

    VALID_OPERATORS: set[str] = {">=", "<=", ">", "<"}

    def __init__(self, operator: ComparisonOperator, version: LibraryVersion) -> None:
        """Initialize a ComparisonVersionSpecifier.

        Args:
            operator: The comparison operator (>=, <=, >, <).
            version: The version to compare against.

        Raises:
            ValueError: If the operator is not valid.
        """
        if operator not in self.VALID_OPERATORS:
            raise ValueError(f"Invalid comparison operator: {operator}")
        self.operator = operator
        self.version = version

    def meets(self, version: LibraryVersion) -> bool:
        """Check if a version meets the comparison specification.

        Args:
            version: The version to check.

        Returns:
            True if the version satisfies the comparison, False otherwise.
        """
        if self.operator == ">=":
            return version >= self.version
        elif self.operator == "<=":
            return version <= self.version
        elif self.operator == ">":
            return version > self.version
        else:  # self.operator == "<"
            return version < self.version

    def __eq__(self, value: object, /) -> bool:
        """Check for equality between this ComparisonVersionSpecifier and the value"""
        if not isinstance(value, ComparisonVersionSpecifier):
            return False

        return self.operator == value.operator and self.version == value.version

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        """Return string representation of the specifier."""
        return f"ComparisonVersionSpecifier({self.operator}{self.version!s})"

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Convert the string to a comparison version specifier"""
        # Check longer operators first to avoid matching '<' when '<=' is intended
        for op in sorted(cls.VALID_OPERATORS, key=len, reverse=True):
            if value.startswith(op):
                version_str = value[len(op):].strip()
                return cls(op, LibraryVersion(version_str))  # type: ignore[arg-type]

        raise ValueError(f"Invalid comparison version specifier: {value}")


class RangeVersionSpecifier(VersionSpecifier):
    """Version specification for range requirements (e.g., >=1.0.0,<2.0.0).

    Combines multiple comparison constraints. A version must satisfy all
    constraints to meet the specification.
    """

    def __init__(self, c1: ComparisonVersionSpecifier, c2: ComparisonVersionSpecifier) -> None:
        """Initialize a RangeVersionSpecifier from a range string.

        Args:
            range_str: A comma-separated string of comparison requirements
                       (e.g., ">=1.0.0,<2.0.0").

        Raises:
            ValueError: If the range string is invalid.
        """
        self.constraints: tuple[ComparisonVersionSpecifier, ComparisonVersionSpecifier] = (c1, c2)

    @classmethod
    def from_string(cls, range_str: str) -> Self:
        """Parse a range string into individual comparison constraints.

        Args:
            range_str: A comma-separated string of comparison requirements.

        Raises:
            ValueError: If a constraint in the range is invalid.
        """
        # Split by comma and strip whitespace
        parts = [p.strip() for p in range_str.split(",")]

        if len(parts) != 2:
            raise ValueError(
                "RangeVersionSpecifier requires 2 ComparisonVersionSpecifiers. "
                + f"'{range_str}' contains {len(parts)}"
            )

        return cls(
            ComparisonVersionSpecifier.from_string(parts[0]),
            ComparisonVersionSpecifier.from_string(parts[1]),
        )

    def meets(self, version: LibraryVersion) -> bool:
        """Check if a version meets all range constraints.

        Args:
            version: The version to check.

        Returns:
            True if the version satisfies all constraints, False otherwise.
        """
        # All constraints must be satisfied
        return all(constraint.meets(version) for constraint in self.constraints)

    def __eq__(self, value: object, /) -> bool:
        """Check for equality between this RangeVersionSpecifier and the value"""
        if not isinstance(value, RangeVersionSpecifier):
            return False

        return self.constraints == value.constraints

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        """Return string representation of the specifier."""
        range_str = ",".join(f"{c.operator}{c.version}" for c in self.constraints)
        return f"RangeVersionSpecifier({range_str})"


def meets_constraints(
    version: str | LibraryVersion, constraints: Sequence[VersionSpecifier]
) -> bool:
    """Determine if the provided version meets all of the constraints provided.

    Args:
        version: The version to check (string or LibraryVersion).
        constraints: A sequence of version specifiers to check against.

    Returns:
        True if the version meets all constraints, False otherwise.
        Returns True if constraints list is empty.
    """
    if isinstance(version, str):
        version = LibraryVersion(version)

    # Empty constraints means any version is acceptable
    if not constraints:
        return True

    return all(constraint.meets(version) for constraint in constraints)


def find_compatible_version(
    versions: list[str] | list[LibraryVersion], constraints: Sequence[VersionSpecifier]
) -> LibraryVersion:
    """Find the latest matching version from the list of versions that meets the constraints.

    Args:
        versions: A list of available versions (strings or LibraryVersion objects).
        constraints: A sequence of version specifiers that must be satisfied.

    Returns:
        The latest LibraryVersion that meets all constraints.

    Raises:
        ValueError: If no compatible version is found or versions list is empty.
    """
    if not versions:
        raise ValueError("No versions provided")

    # Convert all versions to LibraryVersion
    library_versions: list[LibraryVersion] = []
    for v in versions:
        if isinstance(v, str):
            library_versions.append(LibraryVersion(v))
        else:
            library_versions.append(v)

    # Filter versions that meet all constraints
    compatible: list[LibraryVersion] = [
        v for v in library_versions if meets_constraints(v, constraints)
    ]

    if not compatible:
        raise ValueError("No compatible version found")

    # Sort and return the latest (highest) version
    compatible.sort()
    return compatible[-1]


def version_specifier_from_str(version_specifier_str: str) -> VersionSpecifier:
    """Create a version specifier from a string.

    Parses the string and returns the appropriate VersionSpecifier subclass:
    - Direct version: "1.0.0" -> DirectVersionSpecifier
    - Caret requirement: "^1.2.3" -> CaretVersionSpecifier
    - Comparison requirement: ">=1.0.0" -> ComparisonVersionSpecifier
    - Range requirement: ">=1.0.0,<2.0.0" -> RangeVersionSpecifier

    Args:
        version_specifier_str: The version specifier string to parse.

    Returns:
        A VersionSpecifier instance appropriate for the given string.

    Raises:
        ValueError: If the string is empty or cannot be parsed.
    """
    if not version_specifier_str:
        raise ValueError("Version specifier string cannot be empty")

    specifier_str = version_specifier_str.strip()

    try:
        return RangeVersionSpecifier.from_string(specifier_str)
    except ValueError:
        pass

    try:
        return ComparisonVersionSpecifier.from_string(specifier_str)
    except ValueError:
        pass

    try:
        return CaretVersionSpecifier.from_string(specifier_str)
    except ValueError:
        pass

    try:
        return DirectVersionSpecifier.from_string(specifier_str)
    except ValueError:
        pass

    raise ValueError(f"Unable to convert to version specifier: '{version_specifier_str}'")
