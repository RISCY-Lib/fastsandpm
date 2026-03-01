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
"""Tests for Version class in fastsandpm.versioning module.

These tests verify the fastsandpm.versioning.Version class can:
- Parse SemanticVersioning strings into major, minor, and patch numbers
- Parse pre-release information (appended with '.', '-', or no separator)
- Handle fully specified pre-release stages (e.g., 'alpha', 'beta', 'release-candidate')
- Handle abbreviated pre-release stages (e.g., 'a', 'b', 'rc')
- Handle abbreviated pre-release directly after patch (e.g., '1.2.3b3')
- Handle pre-release numbers (e.g., 'alpha1', 'rc3')
- Compare any two versions to determine which is newer
"""

from __future__ import annotations

import pytest

from fastsandpm.versioning import LibraryVersion as Version
from fastsandpm.versioning import PreReleaseStage


class TestVersionParsingBasic:
    """Tests for parsing basic semantic version strings (major.minor.patch)."""

    def test_parse_full_semver(self) -> None:
        """Test parsing a full semantic version string."""
        version = Version("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_parse_zero_version(self) -> None:
        """Test parsing version 0.0.0."""
        version = Version("0.0.0")
        assert version.major == 0
        assert version.minor == 0
        assert version.patch == 0

    def test_parse_large_numbers(self) -> None:
        """Test parsing version with large numbers."""
        version = Version("100.200.300")
        assert version.major == 100
        assert version.minor == 200
        assert version.patch == 300

    def test_parse_initial_development_version(self) -> None:
        """Test parsing initial development version (0.x.x)."""
        version = Version("0.1.0")
        assert version.major == 0
        assert version.minor == 1
        assert version.patch == 0

    def test_parse_version_with_zeros(self) -> None:
        """Test parsing version with zero components."""
        version = Version("1.0.0")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0


class TestVersionParsingPreReleaseDotSeparator:
    """Tests for parsing pre-release versions with dot separator."""

    def test_parse_alpha_prerelease_dot(self) -> None:
        """Test parsing alpha pre-release with dot separator."""
        version = Version("1.0.0.alpha")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre is None

    def test_parse_beta_prerelease_dot(self) -> None:
        """Test parsing beta pre-release with dot separator."""
        version = Version("2.1.0.beta")
        assert version.major == 2
        assert version.minor == 1
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre is None

    def test_parse_rc_prerelease_dot(self) -> None:
        """Test parsing release candidate pre-release with dot separator."""
        version = Version("3.0.0.rc")
        assert version.major == 3
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre is None

    def test_parse_release_candidate_full_dot(self) -> None:
        """Test parsing fully specified release-candidate with dot separator."""
        version = Version("1.0.0.release-candidate")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre is None


class TestVersionParsingPreReleaseDashSeparator:
    """Tests for parsing pre-release versions with dash separator."""

    def test_parse_alpha_prerelease_dash(self) -> None:
        """Test parsing alpha pre-release with dash separator."""
        version = Version("1.0.0-alpha")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre is None

    def test_parse_beta_prerelease_dash(self) -> None:
        """Test parsing beta pre-release with dash separator."""
        version = Version("2.1.0-beta")
        assert version.major == 2
        assert version.minor == 1
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre is None

    def test_parse_rc_prerelease_dash(self) -> None:
        """Test parsing release candidate pre-release with dash separator."""
        version = Version("3.0.0-rc")
        assert version.major == 3
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre is None

    def test_parse_release_candidate_full_dash(self) -> None:
        """Test parsing fully specified release-candidate with dash separator."""
        version = Version("1.0.0-release-candidate")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre is None


class TestVersionParsingAbbreviatedPreRelease:
    """Tests for parsing abbreviated pre-release notation."""

    def test_parse_abbreviated_alpha(self) -> None:
        """Test parsing abbreviated alpha notation (e.g., 1.0.0-a)."""
        version = Version("1.0.0-a")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre is None

    def test_parse_abbreviated_beta(self) -> None:
        """Test parsing abbreviated beta notation (e.g., 1.0.0-b)."""
        version = Version("1.0.0-b")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre is None

    def test_parse_abbreviated_alpha_with_number(self) -> None:
        """Test parsing abbreviated alpha with number (e.g., 1.0.0-a1)."""
        version = Version("1.0.0-a1")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre == 1

    def test_parse_abbreviated_beta_with_number(self) -> None:
        """Test parsing abbreviated beta with number (e.g., 1.0.0-b2)."""
        version = Version("1.0.0-b2")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre == 2

    def test_parse_abbreviated_rc_with_number(self) -> None:
        """Test parsing abbreviated rc with number (e.g., 1.2.1-rc3)."""
        version = Version("1.2.1-rc3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 1
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre == 3


class TestVersionParsingNoSeparatorPreRelease:
    """Tests for parsing pre-release notation without separator (e.g., 1.2.3b3)."""

    def test_parse_no_separator_alpha(self) -> None:
        """Test parsing alpha directly after patch (e.g., 1.0.0a)."""
        version = Version("1.0.0a")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre is None

    def test_parse_no_separator_beta(self) -> None:
        """Test parsing beta directly after patch (e.g., 1.0.0b)."""
        version = Version("1.0.0b")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre is None

    def test_parse_no_separator_rc(self) -> None:
        """Test parsing rc directly after patch (e.g., 1.0.0rc)."""
        version = Version("1.0.0rc")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre is None

    def test_parse_no_separator_alpha_with_number(self) -> None:
        """Test parsing alpha with number directly after patch (e.g., 1.0.0a1)."""
        version = Version("1.0.0a1")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre == 1

    def test_parse_no_separator_beta_with_number(self) -> None:
        """Test parsing beta with number directly after patch (e.g., 1.2.3b3)."""
        version = Version("1.2.3b3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre == 3

    def test_parse_no_separator_rc_with_number(self) -> None:
        """Test parsing rc with number directly after patch (e.g., 2.0.0rc2)."""
        version = Version("2.0.0rc2")
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre == 2

    def test_parse_no_separator_large_prerelease_number(self) -> None:
        """Test parsing large pre-release number without separator."""
        version = Version("1.0.0b123")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre == 123


class TestVersionParsingPreReleaseWithNumber:
    """Tests for parsing pre-release versions with numeric identifiers."""

    def test_parse_alpha_with_number_dot(self) -> None:
        """Test parsing alpha with number using dot separator."""
        version = Version("1.0.0.alpha1")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre == 1

    def test_parse_beta_with_number_dot(self) -> None:
        """Test parsing beta with number using dot separator."""
        version = Version("1.0.0.beta2")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre == 2

    def test_parse_rc_with_number_dot(self) -> None:
        """Test parsing rc with number using dot separator."""
        version = Version("1.0.0.rc1")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre == 1

    def test_parse_alpha_with_number_dash(self) -> None:
        """Test parsing alpha with number using dash separator."""
        version = Version("1.0.0-alpha1")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA
        assert version.pre == 1

    def test_parse_beta_with_number_dash(self) -> None:
        """Test parsing beta with number using dash separator."""
        version = Version("1.0.0-beta2")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre == 2

    def test_parse_rc_with_number_dash(self) -> None:
        """Test parsing rc with number using dash separator."""
        version = Version("1.0.0-rc3")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre == 3

    def test_parse_prerelease_with_large_number(self) -> None:
        """Test parsing pre-release with large number."""
        version = Version("1.0.0-rc99")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.RELEASE_CANDIDATE
        assert version.pre == 99


class TestVersionParsingInvalid:
    """Tests for invalid version string handling."""

    def test_parse_invalid_missing_patch(self) -> None:
        """Test that parsing version without patch raises error."""
        with pytest.raises(ValueError):
            Version("1.2")

    def test_parse_invalid_missing_minor(self) -> None:
        """Test that parsing version without minor raises error."""
        with pytest.raises(ValueError):
            Version("1")

    def test_parse_invalid_empty_string(self) -> None:
        """Test that parsing empty string raises error."""
        with pytest.raises(ValueError):
            Version("")

    def test_parse_invalid_non_numeric_major(self) -> None:
        """Test that parsing non-numeric major raises error."""
        with pytest.raises(ValueError):
            Version("a.2.3")

    def test_parse_invalid_non_numeric_minor(self) -> None:
        """Test that parsing non-numeric minor raises error."""
        with pytest.raises(ValueError):
            Version("1.b.3")

    def test_parse_invalid_non_numeric_patch(self) -> None:
        """Test that parsing non-numeric patch raises error."""
        with pytest.raises(ValueError):
            Version("1.2.c")


class TestVersionConstructorKeyword:
    """Tests for Version construction using keyword arguments."""

    def test_construct_with_keywords(self) -> None:
        """Test constructing version with keyword arguments."""
        version = Version(major=1, minor=2, patch=3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_construct_with_keywords_and_pre_stage(self) -> None:
        """Test constructing version with pre-release stage."""
        version = Version(major=1, minor=0, patch=0, pre_stage=PreReleaseStage.ALPHA)
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.ALPHA

    def test_construct_with_keywords_and_pre_number(self) -> None:
        """Test constructing version with pre-release stage and number."""
        version = Version(major=1, minor=0, patch=0, pre_stage=PreReleaseStage.BETA, pre=2)
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.pre_stage == PreReleaseStage.BETA
        assert version.pre == 2


class TestVersionComparisonMajor:
    """Tests for version comparison based on major version."""

    def test_compare_major_less_than(self) -> None:
        """Test that lower major version is less than higher."""
        v1 = Version("1.0.0")
        v2 = Version("2.0.0")
        assert v1 < v2

    def test_compare_major_greater_than(self) -> None:
        """Test that higher major version is greater than lower."""
        v1 = Version("2.0.0")
        v2 = Version("1.0.0")
        assert v1 > v2

    def test_compare_major_equal(self) -> None:
        """Test that same major versions are equal (with same minor/patch)."""
        v1 = Version("1.0.0")
        v2 = Version("1.0.0")
        assert v1 == v2


class TestVersionComparisonMinor:
    """Tests for version comparison based on minor version."""

    def test_compare_minor_less_than(self) -> None:
        """Test that lower minor version is less than higher (same major)."""
        v1 = Version("1.1.0")
        v2 = Version("1.2.0")
        assert v1 < v2

    def test_compare_minor_greater_than(self) -> None:
        """Test that higher minor version is greater than lower (same major)."""
        v1 = Version("1.2.0")
        v2 = Version("1.1.0")
        assert v1 > v2

    def test_compare_minor_major_takes_precedence(self) -> None:
        """Test that major version takes precedence over minor."""
        v1 = Version("1.9.0")
        v2 = Version("2.0.0")
        assert v1 < v2


class TestVersionComparisonPatch:
    """Tests for version comparison based on patch version."""

    def test_compare_patch_less_than(self) -> None:
        """Test that lower patch version is less than higher (same major/minor)."""
        v1 = Version("1.0.1")
        v2 = Version("1.0.2")
        assert v1 < v2

    def test_compare_patch_greater_than(self) -> None:
        """Test that higher patch version is greater than lower (same major/minor)."""
        v1 = Version("1.0.2")
        v2 = Version("1.0.1")
        assert v1 > v2

    def test_compare_patch_minor_takes_precedence(self) -> None:
        """Test that minor version takes precedence over patch."""
        v1 = Version("1.0.9")
        v2 = Version("1.1.0")
        assert v1 < v2


class TestVersionComparisonPreRelease:
    """Tests for version comparison with pre-release versions."""

    def test_release_greater_than_prerelease(self) -> None:
        """Test that release version is greater than pre-release of same base."""
        v_release = Version("1.0.0")
        v_alpha = Version("1.0.0.alpha")
        assert v_release > v_alpha

    def test_prerelease_less_than_release(self) -> None:
        """Test that pre-release version is less than release of same base."""
        v_alpha = Version("1.0.0.alpha")
        v_release = Version("1.0.0")
        assert v_alpha < v_release

    def test_alpha_less_than_beta(self) -> None:
        """Test that alpha is less than beta (lexicographic comparison)."""
        v_alpha = Version("1.0.0.alpha")
        v_beta = Version("1.0.0.beta")
        assert v_alpha < v_beta

    def test_beta_less_than_rc(self) -> None:
        """Test that beta is less than rc (lexicographic comparison)."""
        v_beta = Version("1.0.0.beta")
        v_rc = Version("1.0.0.rc")
        assert v_beta < v_rc

    def test_alpha_less_than_rc(self) -> None:
        """Test that alpha is less than rc."""
        v_alpha = Version("1.0.0.alpha")
        v_rc = Version("1.0.0.rc")
        assert v_alpha < v_rc

    def test_prerelease_number_comparison(self) -> None:
        """Test that pre-release numbers are compared correctly."""
        v_rc1 = Version("1.0.0.rc1")
        v_rc2 = Version("1.0.0.rc2")
        assert v_rc1 < v_rc2

    def test_prerelease_same_stage_equal(self) -> None:
        """Test that same pre-release versions are equal."""
        v1 = Version("1.0.0.alpha")
        v2 = Version("1.0.0.alpha")
        assert v1 == v2

    def test_prerelease_with_dash_separator(self) -> None:
        """Test comparison of pre-release versions with dash separator."""
        v_alpha = Version("1.0.0-alpha")
        v_release = Version("1.0.0")
        assert v_alpha < v_release


class TestVersionComparisonAbbreviated:
    """Tests for version comparison with abbreviated pre-release notation."""

    def test_abbreviated_alpha_less_than_release(self) -> None:
        """Test that abbreviated alpha (a1) is less than release."""
        v_a1 = Version("1.0.0-a1")
        v_release = Version("1.0.0")
        assert v_a1 < v_release

    def test_abbreviated_rc_less_than_release(self) -> None:
        """Test that abbreviated rc is less than release."""
        v_rc = Version("1.0.0-rc3")
        v_release = Version("1.0.0")
        assert v_rc < v_release

    def test_abbreviated_alpha_sequence(self) -> None:
        """Test that abbreviated alpha versions are ordered correctly."""
        v_a1 = Version("1.0.0-a1")
        v_a2 = Version("1.0.0-a2")
        assert v_a1 < v_a2

    def test_abbreviated_rc_sequence(self) -> None:
        """Test that abbreviated rc versions are ordered correctly."""
        v_rc1 = Version("1.0.0-rc1")
        v_rc3 = Version("1.0.0-rc3")
        assert v_rc1 < v_rc3


class TestVersionComparisonEquality:
    """Tests for version equality comparison."""

    def test_equal_versions(self) -> None:
        """Test that identical versions are equal."""
        v1 = Version("1.2.3")
        v2 = Version("1.2.3")
        assert v1 == v2

    def test_equal_versions_with_prerelease(self) -> None:
        """Test that identical pre-release versions are equal."""
        v1 = Version("1.0.0.alpha")
        v2 = Version("1.0.0.alpha")
        assert v1 == v2

    def test_not_equal_different_major(self) -> None:
        """Test that versions with different major are not equal."""
        v1 = Version("1.0.0")
        v2 = Version("2.0.0")
        assert v1 != v2

    def test_not_equal_different_prerelease(self) -> None:
        """Test that versions with different pre-release are not equal."""
        v1 = Version("1.0.0.alpha")
        v2 = Version("1.0.0.beta")
        assert v1 != v2

    def test_not_equal_prerelease_vs_release(self) -> None:
        """Test that pre-release and release of same base are not equal."""
        v1 = Version("1.0.0.alpha")
        v2 = Version("1.0.0")
        assert v1 != v2


class TestVersionComparisonOperators:
    """Tests for all comparison operators."""

    def test_less_than_or_equal_less(self) -> None:
        """Test <= when less than."""
        v1 = Version("1.0.0")
        v2 = Version("2.0.0")
        assert v1 <= v2

    def test_less_than_or_equal_equal(self) -> None:
        """Test <= when equal."""
        v1 = Version("1.0.0")
        v2 = Version("1.0.0")
        assert v1 <= v2

    def test_greater_than_or_equal_greater(self) -> None:
        """Test >= when greater than."""
        v1 = Version("2.0.0")
        v2 = Version("1.0.0")
        assert v1 >= v2

    def test_greater_than_or_equal_equal(self) -> None:
        """Test >= when equal."""
        v1 = Version("1.0.0")
        v2 = Version("1.0.0")
        assert v1 >= v2


class TestVersionStringRepresentation:
    """Tests for version string representation."""

    def test_str_basic_version(self) -> None:
        """Test string representation of basic version."""
        version = Version("1.2.3")
        assert str(version) == "1.2.3"

    def test_str_version_with_prerelease(self) -> None:
        """Test string representation of version with pre-release."""
        version = Version("1.0.0.alpha")
        assert str(version) == "1.0.0.alpha"

    def test_repr_basic_version(self) -> None:
        """Test repr of basic version."""
        version = Version("1.2.3")
        assert repr(version) == "LibraryVersion(1.2.3)"

    def test_repr_version_with_prerelease(self) -> None:
        """Test repr of version with pre-release."""
        version = Version("1.0.0.alpha")
        assert repr(version) == "LibraryVersion(1.0.0.alpha)"


class TestVersionHashability:
    """Tests for version hashability (usable in sets and as dict keys)."""

    def test_version_hashable(self) -> None:
        """Test that versions can be hashed."""
        version = Version("1.0.0")
        assert hash(version) is not None

    def test_equal_versions_same_hash(self) -> None:
        """Test that equal versions have the same hash."""
        v1 = Version("1.0.0")
        v2 = Version("1.0.0")
        assert hash(v1) == hash(v2)

    def test_version_usable_in_set(self) -> None:
        """Test that versions can be used in sets."""
        v1 = Version("1.0.0")
        v2 = Version("1.0.0")
        v3 = Version("2.0.0")
        version_set = {v1, v2, v3}
        assert len(version_set) == 2  # v1 and v2 are equal

    def test_version_usable_as_dict_key(self) -> None:
        """Test that versions can be used as dictionary keys."""
        version = Version("1.0.0")
        version_dict = {version: "value"}
        assert version_dict[version] == "value"


class TestVersionComparisonComplex:
    """Complex version comparison scenarios."""

    def test_comparison_chain_alpha_beta_rc_release(self) -> None:
        """Test full pre-release progression: alpha < beta < rc < release."""
        v_alpha = Version("1.0.0.alpha")
        v_beta = Version("1.0.0.beta")
        v_rc = Version("1.0.0.rc")
        v_release = Version("1.0.0")

        assert v_alpha < v_beta < v_rc < v_release

    def test_comparison_prerelease_numbers_sequence(self) -> None:
        """Test pre-release number sequence."""
        v_rc1 = Version("1.0.0.rc1")
        v_rc2 = Version("1.0.0.rc2")
        v_rc3 = Version("1.0.0.rc3")

        assert v_rc1 < v_rc2 < v_rc3

    def test_comparison_mixed_versions(self) -> None:
        """Test comparison of various version formats."""
        versions = [
            Version("0.9.0"),
            Version("1.0.0.alpha"),
            Version("1.0.0.beta"),
            Version("1.0.0.rc1"),
            Version("1.0.0"),
            Version("1.0.1"),
            Version("1.1.0"),
            Version("2.0.0.alpha"),
            Version("2.0.0"),
        ]
        sorted_versions = sorted(versions)
        assert sorted_versions == versions

    def test_prerelease_of_newer_base_greater_than_older_release(self) -> None:
        """Test that pre-release of newer base is greater than older release."""
        v_old_release = Version("1.0.0")
        v_new_alpha = Version("2.0.0.alpha")
        assert v_new_alpha > v_old_release
