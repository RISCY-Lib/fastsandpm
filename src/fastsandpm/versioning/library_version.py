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
"""Semantic version representation and comparison.

This module provides the LibraryVersion class for parsing, representing, and
comparing semantic versions. Versions follow the semantic versioning specification
with optional pre-release identifiers.

Supported Version Formats:
    - Standard: ``major.minor.patch`` (e.g., "1.2.3")
    - Pre-release with dash: ``major.minor.patch-pre`` (e.g., "1.2.3-alpha")
    - Pre-release with dot: ``major.minor.patch.pre`` (e.g., "1.2.3.rc1")
    - Pre-release abbreviated: ``major.minor.patchpre`` (e.g., "1.2.3b2")

Pre-release Stages (in order):
    - alpha (a): Development/testing phase
    - beta (b): Feature-complete but may have bugs
    - rc (release-candidate): Ready for release

Classes:
    PreReleaseStage: Enum for pre-release stages.
    LibraryVersion: Represents and compares semantic versions.

Example:
    >>> v1 = LibraryVersion("1.2.3")
    >>> v2 = LibraryVersion("1.2.3-alpha")
    >>> v1 > v2  # Release versions are greater than pre-release
    True
"""

from __future__ import annotations

import re
from enum import Enum
from functools import total_ordering
from typing import overload


class PreReleaseStage(Enum):
    """Enum representing pre-release stages in semantic versioning.

    Pre-release stages indicate the maturity level of a version before
    its official release. They are ordered from least to most mature:
    ALPHA < BETA < RELEASE_CANDIDATE.

    Example:
        >>> stage = PreReleaseStage.from_string("rc")
        >>> stage
        <PreReleaseStage.RELEASE_CANDIDATE: 'rc'>
    """

    ALPHA = "alpha"
    """Early development/testing phase."""
    BETA = "beta"
    """Feature-complete but may contain bugs."""
    RELEASE_CANDIDATE = "rc"
    """Ready for release."""

    @classmethod
    def from_string(cls, value: str) -> PreReleaseStage | None:
        """Convert a string to a PreReleaseStage enum.

        Args:
            value: A string representing a pre-release stage.
                   Supports full names (alpha, beta, release-candidate)
                   and abbreviations (a, b, rc).

        Returns:
            The corresponding PreReleaseStage enum, or None if not recognized.
        """
        value_lower = value.lower()
        if value_lower in ("a", "alpha"):
            return cls.ALPHA
        if value_lower in ("b", "beta"):
            return cls.BETA
        if value_lower in ("rc", "release-candidate"):
            return cls.RELEASE_CANDIDATE
        return None


@total_ordering
class LibraryVersion:
    """Represents a semantic version with comparison support.

    A semantic version consists of major, minor, and patch numbers,
    with an optional pre-release identifier. Versions can be compared
    using standard comparison operators.

    The version format is: major.minor.patch[.pre] or major.minor.patch[-pre]
    Examples: "1.0.0", "2.3.1", "1.0.0.alpha", "2.0.0-rc1"

    Attributes:
        major: The major version number.
        minor: The minor version number.
        patch: The patch version number.
        pre_stage: Optional pre-release stage (ALPHA, BETA, RELEASE_CANDIDATE).
        pre: Optional pre-release number (e.g., 1 for rc1).

    Example:
        >>> v1 = LibraryVersion("1.2.3")
        >>> v2 = LibraryVersion(major=2, minor=0, patch=0)
        >>> v1 < v2
        True
    """

    @overload
    def __init__(self, version: str) -> None:
        """Initialize from a version string.

        Args:
            version: A version string in "major.minor.patch" or
                "major.minor.patch.pre" or "major.minor.patch-pre" format.

        Raises:
            ValueError: If the version string format is invalid.
        """
        ...

    @overload
    def __init__(
        self,
        *,
        major: int,
        minor: int,
        patch: int,
    ) -> None:
        """Initialize from individual version components.

        Args:
            major: The major version number.
            minor: The minor version number.
            patch: The patch version number.
        """
        ...

    @overload
    def __init__(self, *, major: int, minor: int, patch: int, pre_stage: PreReleaseStage) -> None:
        """Initialize from individual version components.

        Args:
            major: The major version number.
            minor: The minor version number.
            patch: The patch version number.
            pre_stage: Pre-release stage (ALPHA, BETA, RELEASE_CANDIDATE).
        """
        ...

    @overload
    def __init__(
        self, *, major: int, minor: int, patch: int, pre_stage: PreReleaseStage, pre: int
    ) -> None:
        """Initialize from individual version components.

        Args:
            major: The major version number.
            minor: The minor version number.
            patch: The patch version number.
            pre_stage: Pre-release stage (ALPHA, BETA, RELEASE_CANDIDATE).
            pre: Pre-release number (e.g., 1 for rc1).
        """

    def __init__(
        self,
        version: str | None = None,
        *,
        major: int | None = None,
        minor: int | None = None,
        patch: int | None = None,
        pre_stage: PreReleaseStage | str | None = None,
        pre: int | None = None,
    ):  # type: ignore[no-untyped-def]
        """Initialize a LibraryVersion instance.

        Can be initialized either from a version string or from individual
        version components (major, minor, patch, and optional pre-release).

        Raises:
            ValueError: If the version string format is invalid.
        """
        if version is not None:
            if (
                major is not None
                or minor is not None
                or patch is not None
                or pre_stage is not None
                or pre is not None
            ):
                raise ValueError(
                    "Cannot specify version string along with other version components"
                )

            self.major, self.minor, self.patch, self.pre_stage, self.pre = LibraryVersion.parse(
                version
            )
            return

        if major is None or minor is None or patch is None:
            raise ValueError(
                "'major', 'minor', and 'patch' must be specified when using version components"
            )

        self.major = major
        self.minor = minor
        self.patch = patch

        if pre_stage is None:
            if pre is not None:
                raise ValueError("Cannot specify 'pre' without 'pre_stage'")
            self.pre_stage = None
            self.pre = None
            return

        if isinstance(pre_stage, str):
            self.pre_stage = PreReleaseStage.from_string(pre_stage)
        else:
            self.pre_stage = pre_stage

        self.pre = pre

    def __eq__(self, other: object) -> bool:
        """Check equality with another LibraryVersion.

        Args:
            other: The object to compare against.

        Returns:
            True if both versions have identical components, False otherwise.
        """
        if not isinstance(other, LibraryVersion):
            return False

        return (self.major, self.minor, self.patch, self.pre_stage, self.pre) == (
            other.major,
            other.minor,
            other.patch,
            other.pre_stage,
            other.pre,
        )

    def __hash__(self) -> int:
        """Return a hash value for this version.

        Enables use in sets and as dictionary keys.

        Returns:
            An integer hash value.
        """
        return hash((self.major, self.minor, self.patch, self.pre_stage, self.pre))

    def _get_pre_for_comparison(self) -> tuple[int, int] | None:
        """Get a normalized pre-release tuple for comparison.

        Converts the pre-release stage and number into a comparable tuple
        that maintains the correct ordering (alpha < beta < rc).

        Returns:
            A tuple of ``(stage_order, pre_number)`` where stage_order is
            0 for alpha, 1 for beta, 2 for rc. Returns None if this version
            has no pre-release identifier.
        """
        if self.pre_stage is None:
            return None

        # Define ordering for stages (lower number = earlier in release cycle)
        stage_order_map = {
            PreReleaseStage.ALPHA: 0,
            PreReleaseStage.BETA: 1,
            PreReleaseStage.RELEASE_CANDIDATE: 2,
        }

        stage_order = stage_order_map.get(self.pre_stage, 99)
        pre_num = self.pre if self.pre is not None else 0

        return (stage_order, pre_num)

    def __lt__(self, other: LibraryVersion) -> bool:
        """Check if this version is less than another.

        Comparison follows semantic versioning rules:
        - Major, minor, patch are compared numerically
        - Pre-release versions are less than release versions (1.0.0.alpha < 1.0.0)
        - Pre-release identifiers are compared by stage (alpha < beta < rc) then number

        Args:
            other: The LibraryVersion to compare against.

        Returns:
            True if this version is less than the other, False otherwise.
        """
        # Compare major, minor, patch first
        base_self = (self.major, self.minor, self.patch)
        base_other = (other.major, other.minor, other.patch)

        if base_self != base_other:
            return base_self < base_other

        # Same base version - compare pre-release
        self_pre = self._get_pre_for_comparison()
        other_pre = other._get_pre_for_comparison()

        # A version without pre-release is greater than one with pre-release
        if self_pre is None and other_pre is None:
            return False  # Equal
        if self_pre is None:
            return False  # Release > pre-release
        if other_pre is None:
            return True  # Pre-release < release

        # Both have pre-release - compare by (stage_order, pre_number)
        return self_pre < other_pre

    @staticmethod
    def parse(version: str) -> tuple[int, int, int, PreReleaseStage | None, int | None]:
        """Parse a version string into its components.

        Args:
            version: A version string in "major.minor.patch" or
                "major.minor.patch.pre" or "major.minor.patch-pre" or
                "major.minor.patchpre" format (e.g., "1.2.3b3").

        Returns:
            A tuple of (major, minor, patch, pre_stage, pre) where pre_stage
            and pre are None if not specified.

        Raises:
            ValueError: If the version string doesn't match expected format,
                or if major/minor/patch are not valid integers.
        """
        # Pattern to match version strings with optional pre-release
        # Supports dot, dash, or no separator for pre-release
        # Pre-release can be: alpha, beta, rc, a, b, release-candidate
        # Optionally followed by a number (with optional dot separator before number)
        # No separator only supported for abbreviated forms (a, b, rc)
        pattern = r"""
            ^
            (\d+)\.(\d+)\.(\d+)     # major.minor.patch
            (?:                      # optional pre-release group
                (?:
                    [.\-]            # separator (dot or dash)
                    (                # pre-release identifier (with separator)
                        a|alpha|
                        b|beta|
                        rc|release-candidate
                    )
                    (?:\.)?          # optional dot before pre-release number
                    (\d+)?           # optional pre-release number
                )
                |
                (?:                  # no separator - only abbreviated forms
                    (a|b|rc)         # abbreviated pre-release identifier
                    (?:\.)?          # optional dot before pre-release number
                    (\d+)?           # optional pre-release number
                )
            )?
            $
        """

        match = re.match(pattern, version, re.IGNORECASE | re.VERBOSE)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3))

            # Groups 4-5 are for separator case, groups 6-7 for no-separator case
            pre_stage_str = match.group(4) or match.group(6)
            pre_num_str = match.group(5) or match.group(7)

            pre_stage = None
            pre_num = None

            if pre_stage_str:
                pre_stage = PreReleaseStage.from_string(pre_stage_str)
                if pre_num_str:
                    pre_num = int(pre_num_str)

            return major, minor, patch, pre_stage, pre_num

        # Try simple dot-separated format without pre-release
        values = version.split(".")
        if len(values) == 3:
            try:
                return int(values[0]), int(values[1]), int(values[2]), None, None
            except ValueError:
                pass

        raise ValueError(f"Invalid version: {version}")

    def __str__(self) -> str:
        """Return the string representation of this version.

        Returns:
            The version as "major.minor.patch" or "major.minor.patch.pre".
        """
        if self.pre_stage is not None:
            if self.pre is not None:
                return f"{self.major}.{self.minor}.{self.patch}.{self.pre_stage.value}{self.pre}"
            return f"{self.major}.{self.minor}.{self.patch}.{self.pre_stage.value}"
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            A string like "LibraryVersion(1.2.3)" or "LibraryVersion(1.2.3.alpha)".
        """
        return f"LibraryVersion({str(self)})"
