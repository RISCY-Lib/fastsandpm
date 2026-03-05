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
"""Version specifier classes for dependency constraints.

This module provides classes for representing and evaluating version
constraints used in dependency specifications. It supports various
constraint formats commonly used in package managers.

Supported Specifier Formats:
    - Direct: ``"1.0.0"`` (exact version match)
    - Caret: ``"^1.2.3"`` (semver-compatible updates)
    - Comparison: ``">=1.0.0"``, ``"<=2.0.0"``, ``">1.0.0"``, ``"<2.0.0"``
    - Range: ``">=1.0.0,<2.0.0"`` (multiple constraints)

Classes:
    VersionSpecifier: Abstract base class for all specifiers.
    DirectVersionSpecifier: Matches a single exact version.
    CaretVersionSpecifier: Matches semver-compatible versions.
    ComparisonVersionSpecifier: Matches using comparison operators.
    RangeVersionSpecifier: Matches versions within a range.

Functions:
    meets_constraints: Check if a version satisfies all constraints.
    find_compatible_version: Find the latest compatible version.
    version_specifier_from_str: Parse a specifier string into an object.

Type Aliases:
    ComparisonOperator: Literal type for valid comparison operators.

Example:
    >>> from fastsandpm.versioning.specifier import version_specifier_from_str
    >>> spec = version_specifier_from_str("^1.2.0")
    >>> spec.satisfied_by(LibraryVersion("1.5.0"))
    True
    >>> spec.satisfied_by(LibraryVersion("2.0.0"))
    False
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Literal, Self

from .library_version import LibraryVersion


class VersionSpecifier(ABC):
    """Abstract base class for version specifications.

    Version specifiers define constraints on acceptable versions. Subclasses
    implement specific constraint types (exact match, comparison, range, etc.).

    All specifiers must implement the ``satisfied_by`` method to check if
    a given version meets the specification's constraints.
    """

    @abstractmethod
    def satisfied_by(self, version: LibraryVersion) -> bool:
        """Check if a version satisfies this specification.

        Args:
            version: The LibraryVersion to check against this specifier.

        Returns:
            True if the version satisfies all constraints defined by this
            specifier, False otherwise.
        """


class DirectVersionSpecifier(VersionSpecifier):
    """Version specifier that matches a single exact version.

    This specifier requires an exact match with the specified version.
    Pre-release stages and numbers must also match exactly.

    Attributes:
        version: The exact version that must be matched.

    Example:
        >>> spec = DirectVersionSpecifier(LibraryVersion("1.2.3"))
        >>> spec.satisfied_by(LibraryVersion("1.2.3"))
        True
        >>> spec.satisfied_by(LibraryVersion("1.2.4"))
        False
    """

    def __init__(self, version: LibraryVersion) -> None:
        """Initialize a DirectVersionSpecifier.

        Args:
            version: The exact version to match.
        """
        self.version = version

    def satisfied_by(self, version: LibraryVersion) -> bool:
        """Check if a version meets the specification.

        Args:
            version: The version to check.

        Returns:
            True if the version matches exactly, False otherwise.
        """
        return self.version == version

    def __eq__(self, value: object) -> bool:
        """Check equality with another DirectVersionSpecifier.

        Args:
            value: The object to compare against.

        Returns:
            True if both specifiers match the same version, False otherwise.
        """
        if not isinstance(value, DirectVersionSpecifier):
            return False
        return self.version == value.version

    def __repr__(self) -> str:
        """Return the repr string (same as str)."""
        return str(self)

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            A string like ``DirectVersionSpecifier(1.2.3)``.
        """
        return f"DirectVersionSpecifier({self.version!s})"

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create a DirectVersionSpecifier from a version string.

        Args:
            value: A version string (e.g., "1.2.3").

        Returns:
            A new DirectVersionSpecifier for the parsed version.

        Raises:
            ValueError: If the string cannot be parsed as a valid version.
        """
        return cls(LibraryVersion(value.strip()))


class CaretVersionSpecifier(VersionSpecifier):
    """Version specifier for semver-compatible caret requirements (^x.y.z).

    Caret requirements allow updates that do not modify the left-most
    non-zero digit, following semantic versioning compatibility rules:

    - ``^1.2.3`` allows ``>=1.2.3, <2.0.0``
    - ``^0.2.3`` allows ``>=0.2.3, <0.3.0`` (0.x treats minor as breaking)
    - ``^0.0.3`` allows ``>=0.0.3, <0.0.4`` (0.0.x treats patch as breaking)

    Attributes:
        version: The base version for the caret requirement.

    Example:
        >>> spec = CaretVersionSpecifier(LibraryVersion("1.2.0"))
        >>> spec.satisfied_by(LibraryVersion("1.9.9"))
        True
        >>> spec.satisfied_by(LibraryVersion("2.0.0"))
        False
    """

    def __init__(self, version: LibraryVersion) -> None:
        """Initialize a CaretVersionSpecifier.

        Args:
            version: The base version for the caret requirement.
        """
        self.version = version

    def satisfied_by(self, version: LibraryVersion) -> bool:
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
        """Check equality with another CaretVersionSpecifier.

        Args:
            value: The object to compare against.

        Returns:
            True if both specifiers have the same base version, False otherwise.
        """
        if not isinstance(value, CaretVersionSpecifier):
            return False
        return self.version == value.version

    def __repr__(self) -> str:
        """Return the repr string (same as str)."""
        return str(self)

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            A string like ``CaretVersionSpecifier(^1.2.3)``.
        """
        return f"CaretVersionSpecifier(^{self.version!s})"

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create a CaretVersionSpecifier from a caret requirement string.

        Args:
            value: A caret requirement string (e.g., "^1.2.3").

        Returns:
            A new CaretVersionSpecifier for the parsed version.

        Raises:
            ValueError: If the string doesn't start with '^' or the version
                is invalid.
        """
        if not value[0] == "^":
            raise ValueError(f"Cannot create CaretVersionSpecifier from string: {value}")

        return cls(LibraryVersion(value[1:].strip()))


ComparisonOperator = Literal[">=", "<=", ">", "<"]
"""Type alias for valid comparison operators."""


class ComparisonVersionSpecifier(VersionSpecifier):
    """Version specifier for comparison requirements (>=, <=, >, <).

    Compares versions using a single comparison operator. Supports
    greater-than, less-than, and their inclusive variants.

    Example:
        >>> spec = ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))
        >>> spec.satisfied_by(LibraryVersion("1.5.0"))
        True
        >>> spec.satisfied_by(LibraryVersion("0.9.0"))
        False
    """

    VALID_OPERATORS: set[str] = {">=", "<=", ">", "<"}
    """Valid comparison operator strings."""

    def __init__(self, operator: ComparisonOperator, version: LibraryVersion) -> None:
        """Initialize a ComparisonVersionSpecifier.

        Args:
            operator: The comparison operator (">=", "<=", ">", or "<").
            version: The version to compare against.

        Raises:
            ValueError: If the operator is not one of the valid operators.
        """
        if operator not in self.VALID_OPERATORS:
            raise ValueError(f"Invalid comparison operator: {operator}")
        self.operator = operator
        self.version = version

    def satisfied_by(self, version: LibraryVersion) -> bool:
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
        """Check equality with another ComparisonVersionSpecifier.

        Args:
            value: The object to compare against.

        Returns:
            True if both specifiers have the same operator and version.
        """
        if not isinstance(value, ComparisonVersionSpecifier):
            return False

        return self.operator == value.operator and self.version == value.version

    def __repr__(self) -> str:
        """Return the repr string (same as str)."""
        return str(self)

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            A string like ``ComparisonVersionSpecifier(>=1.2.3)``.
        """
        return f"ComparisonVersionSpecifier({self.operator}{self.version!s})"

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create a ComparisonVersionSpecifier from a comparison string.

        Parses strings like ">=1.0.0" or "<2.0.0" into specifier objects.

        Args:
            value: A comparison requirement string (e.g., ">=1.2.3").

        Returns:
            A new ComparisonVersionSpecifier with the parsed operator and version.

        Raises:
            ValueError: If the string doesn't start with a valid operator
                or the version is invalid.
        """
        # Check longer operators first to avoid matching '<' when '<=' is intended
        for op in sorted(cls.VALID_OPERATORS, key=len, reverse=True):
            if value.startswith(op):
                version_str = value[len(op) :].strip()
                return cls(op, LibraryVersion(version_str))  # type: ignore[arg-type]

        raise ValueError(f"Invalid comparison version specifier: {value}")


class RangeVersionSpecifier(VersionSpecifier):
    """Version specifier for range requirements (e.g., >=1.0.0,<2.0.0).

    Combines exactly two comparison constraints. A version must satisfy both
    constraints to meet the specification. Typically used to specify a minimum
    and maximum version bound.

    Example:
        >>> spec = RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")
        >>> spec.satisfied_by(LibraryVersion("1.5.0"))
        True
        >>> spec.satisfied_by(LibraryVersion("2.0.0"))
        False
    """

    def __init__(self, c1: ComparisonVersionSpecifier, c2: ComparisonVersionSpecifier) -> None:
        """Initialize a RangeVersionSpecifier with two comparison constraints.

        Args:
            c1: The first comparison constraint.
            c2: The second comparison constraint.
        """
        self.constraints: tuple[ComparisonVersionSpecifier, ComparisonVersionSpecifier] = (c1, c2)
        """A tuple of two ComparisonVersionSpecifier objects."""

    @classmethod
    def from_string(cls, range_str: str) -> Self:
        """Create a RangeVersionSpecifier from a comma-separated range string.

        Parses strings like ">=1.0.0,<2.0.0" into a specifier with two
        comparison constraints.

        Args:
            range_str: A comma-separated string containing exactly two
                comparison requirements (e.g., ">=1.0.0,<2.0.0").

        Returns:
            A new RangeVersionSpecifier with the parsed constraints.

        Raises:
            ValueError: If the string doesn't contain exactly two constraints
                or if any constraint is invalid.
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

    def satisfied_by(self, version: LibraryVersion) -> bool:
        """Check if a version meets all range constraints.

        Args:
            version: The version to check.

        Returns:
            True if the version satisfies all constraints, False otherwise.
        """
        # All constraints must be satisfied
        return all(constraint.satisfied_by(version) for constraint in self.constraints)

    def __eq__(self, value: object, /) -> bool:
        """Check equality with another RangeVersionSpecifier.

        Args:
            value: The object to compare against.

        Returns:
            True if both specifiers have the same constraints, False otherwise.
        """
        if not isinstance(value, RangeVersionSpecifier):
            return False

        return self.constraints == value.constraints

    def __repr__(self) -> str:
        """Return the repr string (same as str)."""
        return str(self)

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            A string like ``RangeVersionSpecifier(>=1.0.0,<2.0.0)``.
        """
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

    return all(constraint.satisfied_by(version) for constraint in constraints)


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
