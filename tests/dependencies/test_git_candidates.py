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
"""Tests for GitCandidate.get_manifest() with git archive optimization.

These tests verify that GitCandidate.get_manifest() correctly:
1. Attempts to use git archive for fast manifest fetching
2. Falls back to hosting provider REST APIs (GitHub/GitLab)
3. Falls back to full clone when other methods fail
4. Properly handles various error conditions
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from fastsandpm._git_utils import parse_github_url, parse_gitlab_url
from fastsandpm.dependencies.candidates import (
    GitCandidate,
    _fetch_git_manifest_cached,
)
from fastsandpm.manifest import MANIFEST_FILENAME


@pytest.fixture(autouse=True)
def clear_manifest_cache():
    """Clear the manifest cache before each test to ensure test isolation."""
    _fetch_git_manifest_cached.cache_clear()
    yield
    _fetch_git_manifest_cached.cache_clear()


class TestParseGitHubUrl:
    """Tests for parse_github_url function."""

    def test_parse_https_url(self) -> None:
        """Test parsing HTTPS GitHub URLs."""
        assert parse_github_url("https://github.com/owner/repo.git") == ("owner", "repo")
        assert parse_github_url("https://github.com/owner/repo") == ("owner", "repo")
        assert parse_github_url("https://github.com/my-org/my-repo.git") == ("my-org", "my-repo")

    def test_parse_ssh_url(self) -> None:
        """Test parsing SSH GitHub URLs."""
        assert parse_github_url("git@github.com:owner/repo.git") == ("owner", "repo")
        assert parse_github_url("git@github.com:owner/repo") == ("owner", "repo")

    def test_parse_ssh_protocol_url(self) -> None:
        """Test parsing SSH protocol GitHub URLs."""
        assert parse_github_url("ssh://git@github.com/owner/repo.git") == ("owner", "repo")
        assert parse_github_url("ssh://git@github.com/owner/repo") == ("owner", "repo")

    def test_non_github_url_returns_none(self) -> None:
        """Test that non-GitHub URLs return None."""
        assert parse_github_url("https://gitlab.com/owner/repo.git") is None
        assert parse_github_url("https://bitbucket.org/owner/repo.git") is None
        assert parse_github_url("https://example.com/owner/repo.git") is None


class TestParseGitLabUrl:
    """Tests for parse_gitlab_url function."""

    def test_parse_https_url(self) -> None:
        """Test parsing HTTPS GitLab URLs."""
        assert parse_gitlab_url("https://gitlab.com/owner/repo.git") == (
            "gitlab.com",
            "owner/repo",
        )
        assert parse_gitlab_url("https://gitlab.com/owner/repo") == ("gitlab.com", "owner/repo")

    def test_parse_https_url_with_subgroups(self) -> None:
        """Test parsing GitLab URLs with nested groups."""
        assert parse_gitlab_url("https://gitlab.com/group/subgroup/repo.git") == (
            "gitlab.com",
            "group/subgroup/repo",
        )

    def test_parse_ssh_url(self) -> None:
        """Test parsing SSH GitLab URLs."""
        assert parse_gitlab_url("git@gitlab.com:owner/repo.git") == ("gitlab.com", "owner/repo")
        assert parse_gitlab_url("git@gitlab.com:owner/repo") == ("gitlab.com", "owner/repo")

    def test_parse_ssh_protocol_url(self) -> None:
        """Test parsing SSH protocol GitLab URLs."""
        assert parse_gitlab_url("ssh://git@gitlab.com/owner/repo.git") == (
            "gitlab.com",
            "owner/repo",
        )

    def test_parse_self_hosted_gitlab(self) -> None:
        """Test parsing self-hosted GitLab URLs."""
        assert parse_gitlab_url("https://gitlab.example.com/owner/repo.git") == (
            "gitlab.example.com",
            "owner/repo",
        )

    def test_non_gitlab_url_returns_none(self) -> None:
        """Test that non-GitLab URLs return None."""
        assert parse_gitlab_url("https://github.com/owner/repo.git") is None
        assert parse_gitlab_url("https://bitbucket.org/owner/repo.git") is None


class TestGitCandidateGetManifest:
    """Tests for GitCandidate.get_manifest() method."""

    @pytest.fixture
    def sample_manifest_bytes(self) -> bytes:
        """Return sample manifest content as bytes."""
        return b"""
[package]
name = "test-package"
version = "1.0.0"
description = "A test package for git candidate tests"

[dependencies]
some_dep = "^1.0.0"
"""

    @pytest.fixture
    def git_candidate(self) -> GitCandidate:
        """Create a sample GitCandidate for testing."""
        return GitCandidate(
            name="test-package",
            version=None,
            remote="https://example.com/org/repo.git",
            commit_hash="abc123def456",
            corresponding_heads=frozenset(["main"]),
            corresponding_tags=frozenset(["v1.0.0"]),
        )

    def test_get_manifest_uses_git_archive_when_available(
        self, git_candidate: GitCandidate, sample_manifest_bytes: bytes
    ) -> None:
        """Test that get_manifest uses git archive when the remote supports it."""
        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            mock_git.get_remote_file.return_value = sample_manifest_bytes

            manifest = git_candidate.get_manifest()

            # Verify git archive was called
            mock_git.get_remote_file.assert_called_once_with(
                git_candidate.remote,
                git_candidate.commit_hash,
                MANIFEST_FILENAME,
            )
            # Verify clone was NOT called (fast path succeeded)
            mock_git.clone.assert_not_called()

            # Verify manifest was parsed correctly
            assert manifest is not None
            assert manifest.package.name == "test-package"
            assert str(manifest.package.version) == "1.0.0"

    def test_get_manifest_falls_back_to_clone_when_git_archive_fails(
        self, git_candidate: GitCandidate, sample_manifest_bytes: bytes, tmp_path
    ) -> None:
        """Test that get_manifest falls back to clone when git archive is not supported."""
        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # Simulate git archive failure (e.g., GitHub doesn't support it)
            mock_git.get_remote_file.side_effect = ValueError(
                "Could not fetch file proj.toml from remote"
            )

            # Set up mock for the fallback clone path
            def mock_clone(remote, dest):
                # Create the manifest file in the temp directory
                dest.mkdir(parents=True, exist_ok=True)
                (dest / MANIFEST_FILENAME).write_bytes(sample_manifest_bytes)

            mock_git.clone.side_effect = mock_clone
            mock_git.checkout.return_value = None

            manifest = git_candidate.get_manifest()

            # Verify git archive was attempted first
            mock_git.get_remote_file.assert_called_once()
            # Verify fallback to clone occurred
            mock_git.clone.assert_called_once()
            mock_git.checkout.assert_called_once()

            # Verify manifest was parsed correctly via fallback
            assert manifest is not None
            assert manifest.package.name == "test-package"

    def test_get_manifest_returns_none_when_manifest_not_found(
        self, git_candidate: GitCandidate
    ) -> None:
        """Test that get_manifest returns None when no manifest exists."""
        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # git archive fails (file doesn't exist)
            mock_git.get_remote_file.side_effect = ValueError("File not found")

            # Clone succeeds but no manifest file exists
            def mock_clone(remote, dest):
                dest.mkdir(parents=True, exist_ok=True)
                # Don't create proj.toml

            mock_git.clone.side_effect = mock_clone
            mock_git.checkout.return_value = None

            manifest = git_candidate.get_manifest()

            assert manifest is None

    def test_get_manifest_returns_none_when_clone_fails(self, git_candidate: GitCandidate) -> None:
        """Test that get_manifest returns None when both git archive and clone fail."""
        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # git archive fails
            mock_git.get_remote_file.side_effect = ValueError("Not supported")
            # Clone also fails
            mock_git.clone.side_effect = Exception("Clone failed")

            manifest = git_candidate.get_manifest()

            assert manifest is None

    def test_get_manifest_returns_none_when_checkout_fails(
        self, git_candidate: GitCandidate, sample_manifest_bytes: bytes
    ) -> None:
        """Test that get_manifest returns None when checkout fails."""
        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # git archive fails
            mock_git.get_remote_file.side_effect = ValueError("Not supported")

            # Clone succeeds
            def mock_clone(remote, dest):
                dest.mkdir(parents=True, exist_ok=True)
                (dest / MANIFEST_FILENAME).write_bytes(sample_manifest_bytes)

            mock_git.clone.side_effect = mock_clone
            # But checkout fails
            mock_git.checkout.side_effect = Exception("Checkout failed")

            manifest = git_candidate.get_manifest()

            assert manifest is None

    def test_get_manifest_handles_invalid_manifest_content(
        self, git_candidate: GitCandidate
    ) -> None:
        """Test that get_manifest handles invalid manifest content gracefully."""
        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # Return invalid TOML content
            mock_git.get_remote_file.return_value = b"[invalid toml"

            # The function should fall back to clone when parsing fails
            # Then clone should also fail (for this test)
            mock_git.clone.side_effect = Exception("Clone failed")

            manifest = git_candidate.get_manifest()

            # Should return None after both attempts fail
            assert manifest is None


class TestGitCandidateGetManifestPerformance:
    """Tests verifying performance characteristics of get_manifest."""

    def test_git_archive_is_preferred_over_clone(self) -> None:
        """Verify that git archive is always attempted before clone.

        This test ensures the optimization is in place: git archive should be
        tried first as it only fetches a single file, which is much faster than
        cloning the entire repository.
        """
        candidate = GitCandidate(
            name="perf-test",
            version=None,
            remote="https://example.com/repo.git",
            commit_hash="abc123",
            corresponding_heads=frozenset(),
            corresponding_tags=frozenset(),
        )

        call_order = []

        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:

            def track_archive(*args, **kwargs):
                call_order.append("get_remote_file")
                raise ValueError("Not supported")

            def track_clone(*args, **kwargs):
                call_order.append("clone")
                raise Exception("Clone failed")

            mock_git.get_remote_file.side_effect = track_archive
            mock_git.clone.side_effect = track_clone

            candidate.get_manifest()

            # Verify git archive was attempted before clone
            assert call_order == ["get_remote_file", "clone"]


class TestGitCandidateHostingApiIntegration:
    """Tests for hosting provider API integration in get_manifest."""

    @pytest.fixture
    def sample_manifest_bytes(self) -> bytes:
        """Return sample manifest content as bytes."""
        return b"""
[package]
name = "test-package"
version = "1.0.0"
description = "A test package"

[dependencies]
some_dep = "^1.0.0"
"""

    def test_github_api_used_when_git_archive_fails(self, sample_manifest_bytes: bytes) -> None:
        """Test that GitHub raw API is used when git archive fails."""
        candidate = GitCandidate(
            name="test-package",
            version=None,
            remote="https://github.com/owner/repo.git",
            commit_hash="abc123def456",
            corresponding_heads=frozenset(["main"]),
            corresponding_tags=frozenset(),
        )

        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # get_remote_file succeeds via hosting API (it tries hosting API first internally)
            # This simulates the hosting API working while git archive would fail
            mock_git.get_remote_file.return_value = sample_manifest_bytes

            manifest = candidate.get_manifest()

            # Verify clone was NOT called (get_remote_file succeeded)
            mock_git.clone.assert_not_called()
            # Verify manifest was parsed
            assert manifest is not None
            assert manifest.package.name == "test-package"

    def test_gitlab_api_used_when_git_archive_fails(self, sample_manifest_bytes: bytes) -> None:
        """Test that GitLab API is used when git archive fails."""
        candidate = GitCandidate(
            name="test-package",
            version=None,
            remote="https://gitlab.com/group/subgroup/repo.git",
            commit_hash="abc123def456",
            corresponding_heads=frozenset(["main"]),
            corresponding_tags=frozenset(),
        )

        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # get_remote_file succeeds via hosting API (it tries hosting API first internally)
            # This simulates the hosting API working while git archive would fail
            mock_git.get_remote_file.return_value = sample_manifest_bytes

            manifest = candidate.get_manifest()

            # Verify clone was NOT called (get_remote_file succeeded)
            mock_git.clone.assert_not_called()
            # Verify manifest was parsed
            assert manifest is not None
            assert manifest.package.name == "test-package"

    def test_clone_used_when_both_git_archive_and_api_fail(
        self, sample_manifest_bytes: bytes
    ) -> None:
        """Test that clone is used as last resort when get_remote_file fails."""
        candidate = GitCandidate(
            name="test-package",
            version=None,
            remote="https://github.com/owner/repo.git",
            commit_hash="abc123def456",
            corresponding_heads=frozenset(["main"]),
            corresponding_tags=frozenset(),
        )

        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:
            # get_remote_file fails (both hosting API and git archive already tried inside it)
            mock_git.get_remote_file.side_effect = ValueError("Not supported")

            # Set up mock for the clone fallback
            def mock_clone(remote, dest):
                dest.mkdir(parents=True, exist_ok=True)
                (dest / "proj.toml").write_bytes(sample_manifest_bytes)

            mock_git.clone.side_effect = mock_clone
            mock_git.checkout.return_value = None

            manifest = candidate.get_manifest()

            # Verify get_remote_file was attempted
            mock_git.get_remote_file.assert_called_once()
            # Verify clone was used as fallback
            mock_git.clone.assert_called_once()
            # Verify manifest was parsed via clone fallback
            assert manifest is not None
            assert manifest.package.name == "test-package"

    def test_fallback_order_git_archive_then_api_then_clone(self) -> None:
        """Test that get_remote_file is tried first, then clone as fallback."""
        candidate = GitCandidate(
            name="test-package",
            version=None,
            remote="https://github.com/owner/repo.git",
            commit_hash="abc123",
            corresponding_heads=frozenset(),
            corresponding_tags=frozenset(),
        )

        call_order = []

        with patch("fastsandpm.dependencies.candidates._git_utils") as mock_git:

            def track_remote_file(*args, **kwargs):
                call_order.append("get_remote_file")
                raise ValueError("Not supported")

            def track_clone(*args, **kwargs):
                call_order.append("clone")
                raise Exception("Clone failed")

            mock_git.get_remote_file.side_effect = track_remote_file
            mock_git.clone.side_effect = track_clone

            candidate.get_manifest()

            # Verify the order: get_remote_file (internal API first) followed by clone
            assert call_order == ["get_remote_file", "clone"]
