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
"""Tests for version constraints module in fastsandpm.versioning.

These tests verify the fastsandpm.versioning.constraints module can:
- Create and evaluate DirectVersionSpecifier for exact version matches
- Create and evaluate CaretVersionSpecifier for semver-compatible updates (^1.2.3)
- Create and evaluate ComparisonVersionSpecifier for comparison constraints (>=, <=, >, <)
- Create and evaluate RangeVersionSpecifier for version ranges (>=1.0.0,<2.0.0)
- Parse version specifier strings into appropriate specifier objects
- Check if a version meets a list of constraints
- Find the best compatible version from a list of versions

Based on the Version Specifiers documentation:
- Direct Versions: Exact version match (e.g., "1.0.0")
- Caret Requirements: Semver-compatible updates (e.g., "^1.2.3" allows >=1.2.3, <2.0.0)
- Comparison Requirements: Using operators (>=, <=, >, <)
- Range Requirements: Combining comparisons (e.g., ">=1.0.0,<2.0.0")
- Pre-releases: Excluded from ranges unless directly specified
"""

from __future__ import annotations

import pytest

from fastsandpm.versioning import LibraryVersion
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


class TestDirectVersionSpecifierBasic:
    """Tests for DirectVersionSpecifier with basic version matching."""

    def test_direct_specifier_exact_match(self) -> None:
        """Test that DirectVersionSpecifier matches exact version."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is True

    def test_direct_specifier_no_match_different_patch(self) -> None:
        """Test that DirectVersionSpecifier does not match different patch."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.1")) is False

    def test_direct_specifier_no_match_different_minor(self) -> None:
        """Test that DirectVersionSpecifier does not match different minor."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.1.0")) is False

    def test_direct_specifier_no_match_different_major(self) -> None:
        """Test that DirectVersionSpecifier does not match different major."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is False

    def test_direct_specifier_zero_version(self) -> None:
        """Test DirectVersionSpecifier with zero version."""
        specifier = DirectVersionSpecifier(LibraryVersion("0.0.0"))
        assert specifier.satisfied_by(LibraryVersion("0.0.0")) is True
        assert specifier.satisfied_by(LibraryVersion("0.0.1")) is False

    def test_direct_specifier_large_version_numbers(self) -> None:
        """Test DirectVersionSpecifier with large version numbers."""
        specifier = DirectVersionSpecifier(LibraryVersion("100.200.300"))
        assert specifier.satisfied_by(LibraryVersion("100.200.300")) is True
        assert specifier.satisfied_by(LibraryVersion("100.200.301")) is False


class TestDirectVersionSpecifierPreRelease:
    """Tests for DirectVersionSpecifier with pre-release versions."""

    def test_direct_specifier_prerelease_exact_match(self) -> None:
        """Test DirectVersionSpecifier matches exact pre-release version."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0-beta.1"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0-beta.1")) is True

    def test_direct_specifier_prerelease_no_match_release(self) -> None:
        """Test DirectVersionSpecifier pre-release does not match release."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0-alpha"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is False

    def test_direct_specifier_release_no_match_prerelease(self) -> None:
        """Test DirectVersionSpecifier release does not match pre-release."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0-alpha")) is False

    def test_direct_specifier_different_prerelease_stages(self) -> None:
        """Test DirectVersionSpecifier does not match different pre-release stages."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0-alpha"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0-beta")) is False

    def test_direct_specifier_different_prerelease_numbers(self) -> None:
        """Test DirectVersionSpecifier does not match different pre-release numbers."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0-rc1"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0-rc2")) is False


class TestDirectVersionSpecifierStringRepresentation:
    """Tests for DirectVersionSpecifier string representation."""

    def test_direct_specifier_str_basic(self) -> None:
        """Test string representation of DirectVersionSpecifier."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.2.3"))
        assert str(specifier) == "DirectVersionSpecifier(1.2.3)"

    def test_direct_specifier_str_with_prerelease(self) -> None:
        """Test string representation of DirectVersionSpecifier with pre-release."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0.alpha"))
        assert str(specifier) == "DirectVersionSpecifier(1.0.0.alpha)"


class TestCaretVersionSpecifierBasic:
    """Tests for CaretVersionSpecifier basic functionality.

    Caret requirements allow semver-compatible updates:
    ^1.2.3 allows >=1.2.3, <2.0.0
    """

    def test_caret_specifier_exact_match(self) -> None:
        """Test CaretVersionSpecifier matches exact version."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("1.2.3")) is True

    def test_caret_specifier_allows_patch_bump(self) -> None:
        """Test CaretVersionSpecifier allows patch version bump."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("1.2.4")) is True
        assert specifier.satisfied_by(LibraryVersion("1.2.10")) is True

    def test_caret_specifier_allows_minor_bump(self) -> None:
        """Test CaretVersionSpecifier allows minor version bump."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("1.3.0")) is True
        assert specifier.satisfied_by(LibraryVersion("1.9.9")) is True

    def test_caret_specifier_rejects_major_bump(self) -> None:
        """Test CaretVersionSpecifier rejects major version bump."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is False
        assert specifier.satisfied_by(LibraryVersion("3.0.0")) is False

    def test_caret_specifier_rejects_older_version(self) -> None:
        """Test CaretVersionSpecifier rejects older versions."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("1.2.2")) is False
        assert specifier.satisfied_by(LibraryVersion("1.1.0")) is False
        assert specifier.satisfied_by(LibraryVersion("0.9.0")) is False


class TestCaretVersionSpecifierZeroMajor:
    """Tests for CaretVersionSpecifier with 0.x.x versions.

    For 0.x.x versions, caret works differently since API is considered unstable:
    ^0.2.3 should allow >=0.2.3, <0.3.0 (minor bump breaks compatibility)
    """

    def test_caret_specifier_zero_major_exact_match(self) -> None:
        """Test CaretVersionSpecifier with 0.x.x matches exact version."""
        specifier = CaretVersionSpecifier(LibraryVersion("0.2.3"))
        assert specifier.satisfied_by(LibraryVersion("0.2.3")) is True

    def test_caret_specifier_zero_major_allows_patch_bump(self) -> None:
        """Test CaretVersionSpecifier with 0.x.x allows patch bump."""
        specifier = CaretVersionSpecifier(LibraryVersion("0.2.3"))
        assert specifier.satisfied_by(LibraryVersion("0.2.4")) is True
        assert specifier.satisfied_by(LibraryVersion("0.2.99")) is True

    def test_caret_specifier_zero_major_rejects_minor_bump(self) -> None:
        """Test CaretVersionSpecifier with 0.x.x rejects minor bump."""
        specifier = CaretVersionSpecifier(LibraryVersion("0.2.3"))
        assert specifier.satisfied_by(LibraryVersion("0.3.0")) is False

    def test_caret_specifier_zero_major_rejects_major_bump(self) -> None:
        """Test CaretVersionSpecifier with 0.x.x rejects major bump."""
        specifier = CaretVersionSpecifier(LibraryVersion("0.2.3"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is False


class TestCaretVersionSpecifierPreRelease:
    """Tests for CaretVersionSpecifier with pre-release versions.
    """

    def test_caret_specifier_excludes_prerelease(self) -> None:
        """Test CaretVersionSpecifier excludes pre-release versions."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("1.3.0-beta.1")) is True
        assert specifier.satisfied_by(LibraryVersion("1.2.4-alpha")) is True
        assert specifier.satisfied_by(LibraryVersion("1.2.3a0")) is False

    def test_caret_specifier_excludes_prerelease_of_next_major(self) -> None:
        """Test CaretVersionSpecifier excludes pre-release of next major."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0-alpha")) is False


class TestComparisonVersionSpecifierGreaterThanOrEqual:
    """Tests for ComparisonVersionSpecifier with >= operator."""

    def test_comparison_gte_exact_match(self) -> None:
        """Test >= matches exact version."""
        specifier = ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is True

    def test_comparison_gte_higher_patch(self) -> None:
        """Test >= matches higher patch version."""
        specifier = ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.1")) is True

    def test_comparison_gte_higher_minor(self) -> None:
        """Test >= matches higher minor version."""
        specifier = ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.1.0")) is True

    def test_comparison_gte_higher_major(self) -> None:
        """Test >= matches higher major version."""
        specifier = ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is True

    def test_comparison_gte_rejects_lower(self) -> None:
        """Test >= rejects lower versions."""
        specifier = ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("0.9.9")) is False


class TestComparisonVersionSpecifierLessThanOrEqual:
    """Tests for ComparisonVersionSpecifier with <= operator."""

    def test_comparison_lte_exact_match(self) -> None:
        """Test <= matches exact version."""
        specifier = ComparisonVersionSpecifier("<=", LibraryVersion("2.0.0"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is True

    def test_comparison_lte_lower_patch(self) -> None:
        """Test <= matches lower patch version."""
        specifier = ComparisonVersionSpecifier("<=", LibraryVersion("2.0.1"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is True

    def test_comparison_lte_lower_minor(self) -> None:
        """Test <= matches lower minor version."""
        specifier = ComparisonVersionSpecifier("<=", LibraryVersion("2.1.0"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is True

    def test_comparison_lte_lower_major(self) -> None:
        """Test <= matches lower major version."""
        specifier = ComparisonVersionSpecifier("<=", LibraryVersion("2.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is True

    def test_comparison_lte_rejects_higher(self) -> None:
        """Test <= rejects higher versions."""
        specifier = ComparisonVersionSpecifier("<=", LibraryVersion("2.0.0"))
        assert specifier.satisfied_by(LibraryVersion("2.0.1")) is False


class TestComparisonVersionSpecifierGreaterThan:
    """Tests for ComparisonVersionSpecifier with > operator."""

    def test_comparison_gt_rejects_exact_match(self) -> None:
        """Test > does not match exact version."""
        specifier = ComparisonVersionSpecifier(">", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is False

    def test_comparison_gt_higher_patch(self) -> None:
        """Test > matches higher patch version."""
        specifier = ComparisonVersionSpecifier(">", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.0.1")) is True

    def test_comparison_gt_rejects_lower(self) -> None:
        """Test > rejects lower versions."""
        specifier = ComparisonVersionSpecifier(">", LibraryVersion("1.0.0"))
        assert specifier.satisfied_by(LibraryVersion("0.9.9")) is False


class TestComparisonVersionSpecifierLessThan:
    """Tests for ComparisonVersionSpecifier with < operator."""

    def test_comparison_lt_rejects_exact_match(self) -> None:
        """Test < does not match exact version."""
        specifier = ComparisonVersionSpecifier("<", LibraryVersion("2.0.0"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is False

    def test_comparison_lt_lower_patch(self) -> None:
        """Test < matches lower patch version."""
        specifier = ComparisonVersionSpecifier("<", LibraryVersion("2.0.1"))
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is True

    def test_comparison_lt_rejects_higher(self) -> None:
        """Test < rejects higher versions."""
        specifier = ComparisonVersionSpecifier("<", LibraryVersion("2.0.0"))
        assert specifier.satisfied_by(LibraryVersion("2.0.1")) is False


class TestComparisonVersionSpecifierPreRelease:
    """Tests for ComparisonVersionSpecifier with pre-release versions.
    """

    def test_comparison_gte_excludes_prerelease(self) -> None:
        """Test >= excludes pre-release versions."""
        specifier = ComparisonVersionSpecifier(">=", LibraryVersion("1.2.3"))
        assert specifier.satisfied_by(LibraryVersion("1.3.0-beta.1")) is True
        assert specifier.satisfied_by(LibraryVersion("1.2.3-beta.1")) is False

    def test_comparison_lt_excludes_prerelease(self) -> None:
        """Test < excludes pre-release versions."""
        specifier = ComparisonVersionSpecifier("<", LibraryVersion("2.0.0"))
        assert specifier.satisfied_by(LibraryVersion("1.9.0-rc1")) is True


class TestRangeVersionSpecifierBasic:
    """Tests for RangeVersionSpecifier combining multiple comparison constraints."""

    def test_range_specifier_within_range(self) -> None:
        """Test RangeVersionSpecifier matches versions within the range."""
        specifier = RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is True
        assert specifier.satisfied_by(LibraryVersion("1.5.0")) is True
        assert specifier.satisfied_by(LibraryVersion("1.9.9")) is True

    def test_range_specifier_at_lower_bound(self) -> None:
        """Test RangeVersionSpecifier matches lower bound (inclusive)."""
        specifier = RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is True

    def test_range_specifier_at_upper_bound(self) -> None:
        """Test RangeVersionSpecifier excludes upper bound (exclusive)."""
        specifier = RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is False

    def test_range_specifier_below_range(self) -> None:
        """Test RangeVersionSpecifier rejects version below range."""
        specifier = RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("0.9.9")) is False

    def test_range_specifier_above_range(self) -> None:
        """Test RangeVersionSpecifier rejects version above range."""
        specifier = RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("2.0.1")) is False


class TestRangeVersionSpecifierExclusiveBounds:
    """Tests for RangeVersionSpecifier with exclusive bounds."""

    def test_range_specifier_exclusive_lower_bound(self) -> None:
        """Test RangeVersionSpecifier with exclusive lower bound."""
        specifier = RangeVersionSpecifier.from_string(">1.0.0,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is False
        assert specifier.satisfied_by(LibraryVersion("1.0.1")) is True

    def test_range_specifier_inclusive_upper_bound(self) -> None:
        """Test RangeVersionSpecifier with inclusive upper bound."""
        specifier = RangeVersionSpecifier.from_string(">=1.0.0,<=2.0.0")
        assert specifier.satisfied_by(LibraryVersion("2.0.0")) is True


class TestRangeVersionSpecifierPreRelease:
    """Tests for RangeVersionSpecifier with pre-release versions.
    """

    def test_range_specifier_excludes_prerelease(self) -> None:
        """Test RangeVersionSpecifier excludes pre-release versions from range."""
        specifier = RangeVersionSpecifier.from_string(">=1.2.3,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("1.3.0a1")) is True
        assert specifier.satisfied_by(LibraryVersion("1.3.0")) is True

    def test_range_specifier_excludes_prerelease_at_lower_bound(self) -> None:
        """Test RangeVersionSpecifier excludes pre-release at lower bound."""
        specifier = RangeVersionSpecifier.from_string(">=1.2.3,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("1.3.0-beta.1")) is True
        assert specifier.satisfied_by(LibraryVersion("1.5.0-alpha")) is True
        # 1.2.3-beta.1 is technically < 1.2.3 release, so excluded
        assert specifier.satisfied_by(LibraryVersion("1.2.3-beta.1")) is False


class TestVersionSpecifierFromStrDirect:
    """Tests for version_specifier_from_str with direct version strings."""

    def test_parse_direct_version_basic(self) -> None:
        """Test parsing a basic direct version."""
        specifier = version_specifier_from_str("1.0.0")
        assert isinstance(specifier, DirectVersionSpecifier)
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is True

    def test_parse_direct_version_with_prerelease(self) -> None:
        """Test parsing a direct version with pre-release."""
        specifier = version_specifier_from_str("1.0.0-beta.1")
        assert isinstance(specifier, DirectVersionSpecifier)
        assert specifier.satisfied_by(LibraryVersion("1.0.0-beta.1")) is True


class TestVersionSpecifierFromStrCaret:
    """Tests for version_specifier_from_str with caret requirements."""

    def test_parse_caret_version_basic(self) -> None:
        """Test parsing a caret version specifier."""
        specifier = version_specifier_from_str("^1.2.3")
        assert isinstance(specifier, CaretVersionSpecifier)

    def test_parse_caret_version_with_zero_major(self) -> None:
        """Test parsing a caret version specifier with 0.x.x."""
        specifier = version_specifier_from_str("^0.2.3")
        assert isinstance(specifier, CaretVersionSpecifier)


class TestVersionSpecifierFromStrComparison:
    """Tests for version_specifier_from_str with comparison requirements."""

    def test_parse_comparison_gte(self) -> None:
        """Test parsing >= comparison specifier."""
        specifier = version_specifier_from_str(">=1.0.0")
        assert isinstance(specifier, ComparisonVersionSpecifier)

    def test_parse_comparison_lte(self) -> None:
        """Test parsing <= comparison specifier."""
        specifier = version_specifier_from_str("<=2.0.0")
        assert isinstance(specifier, ComparisonVersionSpecifier)

    def test_parse_comparison_gt(self) -> None:
        """Test parsing > comparison specifier."""
        specifier = version_specifier_from_str(">1.0.0")
        assert isinstance(specifier, ComparisonVersionSpecifier)

    def test_parse_comparison_lt(self) -> None:
        """Test parsing < comparison specifier."""
        specifier = version_specifier_from_str("<2.0.0")
        assert isinstance(specifier, ComparisonVersionSpecifier)


class TestVersionSpecifierFromStrRange:
    """Tests for version_specifier_from_str with range requirements."""

    def test_parse_range_basic(self) -> None:
        """Test parsing a basic range specifier."""
        specifier = version_specifier_from_str(">=1.0.0,<2.0.0")
        assert isinstance(specifier, RangeVersionSpecifier)

    def test_parse_range_with_spaces(self) -> None:
        """Test parsing a range specifier with spaces."""
        specifier = version_specifier_from_str(">= 1.0.0, < 2.0.0")
        assert isinstance(specifier, RangeVersionSpecifier)


class TestVersionSpecifierFromStrInvalid:
    """Tests for version_specifier_from_str with invalid inputs."""

    def test_parse_invalid_empty_string(self) -> None:
        """Test parsing empty string raises error."""
        with pytest.raises(ValueError):
            version_specifier_from_str("")

    def test_parse_invalid_malformed_version(self) -> None:
        """Test parsing malformed version raises error."""
        with pytest.raises(ValueError):
            version_specifier_from_str("not.a.version")

    def test_parse_invalid_operator(self) -> None:
        """Test parsing invalid operator raises error."""
        with pytest.raises(ValueError):
            version_specifier_from_str("==1.0.0")


class TestMeetsConstraintsBasic:
    """Tests for meets_constraints function with basic scenarios."""

    def test_meets_constraints_single_constraint(self) -> None:
        """Test meets_constraints with single constraint."""
        constraints = [DirectVersionSpecifier(LibraryVersion("1.0.0"))]
        assert meets_constraints("1.0.0", constraints) is True
        assert meets_constraints("1.0.1", constraints) is False

    def test_meets_constraints_multiple_constraints_all_met(self) -> None:
        """Test meets_constraints when all constraints are met."""
        constraints = [
            ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0")),
            ComparisonVersionSpecifier("<", LibraryVersion("2.0.0")),
        ]
        assert meets_constraints("1.5.0", constraints) is True

    def test_meets_constraints_multiple_constraints_one_not_met(self) -> None:
        """Test meets_constraints when one constraint is not met."""
        constraints = [
            ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0")),
            ComparisonVersionSpecifier("<", LibraryVersion("2.0.0")),
        ]
        assert meets_constraints("2.0.0", constraints) is False

    def test_meets_constraints_empty_list(self) -> None:
        """Test meets_constraints with empty constraint list."""
        assert meets_constraints("1.0.0", []) is True


class TestMeetsConstraintsWithLibraryVersion:
    """Tests for meets_constraints function with LibraryVersion input."""

    def test_meets_constraints_library_version_input(self) -> None:
        """Test meets_constraints accepts LibraryVersion input."""
        constraints = [DirectVersionSpecifier(LibraryVersion("1.0.0"))]
        assert meets_constraints(LibraryVersion("1.0.0"), constraints) is True

    def test_meets_constraints_library_version_with_range(self) -> None:
        """Test meets_constraints with LibraryVersion and range constraints."""
        constraints = [
            ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0")),
            ComparisonVersionSpecifier("<", LibraryVersion("2.0.0")),
        ]
        assert meets_constraints(LibraryVersion("1.5.0"), constraints) is True


class TestFindCompatibleVersionBasic:
    """Tests for find_compatible_version function."""

    def test_find_compatible_version_exact_match(self) -> None:
        """Test finding version with exact match constraint."""
        versions = ["1.0.0", "1.1.0", "2.0.0"]
        constraints = [DirectVersionSpecifier(LibraryVersion("1.1.0"))]
        result = find_compatible_version(versions, constraints)
        assert result == LibraryVersion("1.1.0")

    def test_find_compatible_version_returns_latest(self) -> None:
        """Test finding version returns latest compatible version."""
        versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]
        constraints = [
            ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0")),
            ComparisonVersionSpecifier("<", LibraryVersion("2.0.0")),
        ]
        result = find_compatible_version(versions, constraints)
        assert result == LibraryVersion("1.2.0")

    def test_find_compatible_version_no_match(self) -> None:
        """Test finding version when no match exists."""
        versions = ["1.0.0", "1.1.0"]
        constraints = [ComparisonVersionSpecifier(">=", LibraryVersion("2.0.0"))]
        with pytest.raises(ValueError):
            find_compatible_version(versions, constraints)

    def test_find_compatible_version_empty_list(self) -> None:
        """Test finding version with empty version list."""
        constraints = [DirectVersionSpecifier(LibraryVersion("1.0.0"))]
        with pytest.raises(ValueError):
            find_compatible_version([], constraints)


class TestFindCompatibleVersionWithLibraryVersion:
    """Tests for find_compatible_version with LibraryVersion list input."""

    def test_find_compatible_version_library_version_list(self) -> None:
        """Test finding version with LibraryVersion list input."""
        versions = [
            LibraryVersion("1.0.0"),
            LibraryVersion("1.1.0"),
            LibraryVersion("2.0.0"),
        ]
        constraints = [
            ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0")),
            ComparisonVersionSpecifier("<", LibraryVersion("2.0.0")),
        ]
        result = find_compatible_version(versions, constraints)
        assert result == LibraryVersion("1.1.0")


class TestFindCompatibleVersionPreRelease:
    """Tests for find_compatible_version with pre-release versions."""

    def test_find_compatible_version_excludes_prerelease(self) -> None:
        """Test finding version excludes pre-release from range constraints."""
        versions = ["1.0.0", "1.1.0-beta", "1.1.0", "2.0.0"]
        constraints = [
            ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0")),
            ComparisonVersionSpecifier("<", LibraryVersion("2.0.0")),
        ]
        result = find_compatible_version(versions, constraints)
        # Should return 1.1.0, not 1.1.0-beta
        assert result == LibraryVersion("1.1.0")

    def test_find_compatible_version_direct_prerelease_match(self) -> None:
        """Test finding version can match direct pre-release constraint."""
        versions = ["1.0.0", "1.0.0-beta.1", "1.1.0"]
        constraints = [DirectVersionSpecifier(LibraryVersion("1.0.0-beta.1"))]
        result = find_compatible_version(versions, constraints)
        assert result == LibraryVersion("1.0.0-beta.1")


class TestVersionSpecifierInheritance:
    """Tests to verify proper inheritance from VersionSpecifier base class."""

    def test_direct_specifier_is_version_specifier(self) -> None:
        """Test DirectVersionSpecifier inherits from VersionSpecifier."""
        specifier = DirectVersionSpecifier(LibraryVersion("1.0.0"))
        assert isinstance(specifier, VersionSpecifier)

    def test_caret_specifier_is_version_specifier(self) -> None:
        """Test CaretVersionSpecifier inherits from VersionSpecifier."""
        specifier = CaretVersionSpecifier(LibraryVersion("1.0.0"))
        assert isinstance(specifier, VersionSpecifier)

    def test_comparison_specifier_is_version_specifier(self) -> None:
        """Test ComparisonVersionSpecifier inherits from VersionSpecifier."""
        specifier = ComparisonVersionSpecifier(">=", LibraryVersion("1.0.0"))
        assert isinstance(specifier, VersionSpecifier)

    def test_range_specifier_is_version_specifier(self) -> None:
        """Test RangeVersionSpecifier inherits from VersionSpecifier."""
        specifier = RangeVersionSpecifier.from_string(">=1.0.0,<2.0.0")
        assert isinstance(specifier, VersionSpecifier)


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios based on documentation examples."""

    def test_toml_direct_version_scenario(self) -> None:
        """Test scenario: [dependencies] time = "1.0.0" requires exact version."""
        specifier = version_specifier_from_str("1.0.0")
        available = ["0.9.0", "1.0.0", "1.0.1", "2.0.0"]
        constraints = [specifier]
        result = find_compatible_version(available, constraints)
        assert result == LibraryVersion("1.0.0")

    def test_toml_caret_version_scenario(self) -> None:
        """Test scenario: ^1.2.3 allows compatible updates up to 2.0.0."""
        specifier = version_specifier_from_str("^1.2.3")
        available = ["1.0.0", "1.2.3", "1.5.0", "1.9.9", "2.0.0"]
        # Find latest that meets constraint
        compatible = [v for v in available if specifier.satisfied_by(LibraryVersion(v))]
        assert "1.2.3" in compatible
        assert "1.5.0" in compatible
        assert "1.9.9" in compatible
        assert "2.0.0" not in compatible
        assert "1.0.0" not in compatible

    def test_toml_range_version_scenario(self) -> None:
        """Test scenario: >=1.0.0,<2.0.0 limits version range."""
        specifier = version_specifier_from_str(">=1.0.0,<2.0.0")
        available = ["0.9.0", "1.0.0", "1.5.0", "2.0.0", "2.1.0"]
        compatible = [v for v in available if specifier.satisfied_by(LibraryVersion(v))]
        assert "1.0.0" in compatible
        assert "1.5.0" in compatible
        assert "0.9.0" not in compatible
        assert "2.0.0" not in compatible
        assert "2.1.0" not in compatible

    def test_prerelease_excluded_from_range_scenario(self) -> None:
        """Test scenario: >=1.2.3,<2.0.0 excludes 1.3.0-beta.1."""
        specifier = version_specifier_from_str(">=1.2.3,<2.0.0")
        assert specifier.satisfied_by(LibraryVersion("1.3.0")) is True
        assert specifier.satisfied_by(LibraryVersion("1.3.0-beta.1")) is True

    def test_direct_prerelease_included_scenario(self) -> None:
        """Test scenario: 1.0.0-beta.1 directly matches pre-release version."""
        specifier = version_specifier_from_str("1.0.0-beta.1")
        assert specifier.satisfied_by(LibraryVersion("1.0.0-beta.1")) is True
        assert specifier.satisfied_by(LibraryVersion("1.0.0")) is False
