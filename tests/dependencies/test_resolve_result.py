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
"""Tests for the ResolveResult class."""

from __future__ import annotations

import pathlib

import pytest

from fastsandpm.dependencies import PathCandidate, ResolveResult


def _make_candidate(name: str) -> PathCandidate:
    """Create a minimal PathCandidate for testing."""
    return PathCandidate(name=name, version=None, path=pathlib.Path(f"/tmp/{name}"))


class TestResolveResult:
    """Tests for the ResolveResult dict-like interface."""

    @pytest.fixture
    def result(self) -> ResolveResult:
        """Create a ResolveResult with two independent packages."""
        a = _make_candidate("alpha")
        b = _make_candidate("beta")
        return ResolveResult(
            mapping={"alpha": a, "beta": b},
            graph={"alpha": set(), "beta": set()},
            direct_dependencies=frozenset({"alpha", "beta"}),
        )

    def test_items_returns_mapping_items(self, result: ResolveResult) -> None:
        """Test that items() delegates to the mapping."""
        items = dict(result.items())
        assert set(items.keys()) == {"alpha", "beta"}

    def test_getitem_returns_candidate(self, result: ResolveResult) -> None:
        """Test that [] returns the correct candidate."""
        assert result["alpha"].name == "alpha"
        assert result["beta"].name == "beta"

    def test_getitem_missing_raises_key_error(self, result: ResolveResult) -> None:
        """Test that [] raises KeyError for unknown packages."""
        with pytest.raises(KeyError):
            result["missing"]

    def test_iter_yields_keys(self, result: ResolveResult) -> None:
        """Test that iterating yields package names."""
        assert set(result) == {"alpha", "beta"}

    def test_len_returns_count(self, result: ResolveResult) -> None:
        """Test that len() returns the number of packages."""
        assert len(result) == 2

    def test_contains_checks_membership(self, result: ResolveResult) -> None:
        """Test that 'in' checks the mapping."""
        assert "alpha" in result
        assert "missing" not in result

    def test_frozen(self, result: ResolveResult) -> None:
        """Test that the dataclass is immutable."""
        with pytest.raises(AttributeError):
            result.mapping = {}  # type: ignore[misc]

    def test_empty_result(self) -> None:
        """Test that an empty ResolveResult works correctly."""
        result = ResolveResult(
            mapping={},
            graph={},
            direct_dependencies=frozenset(),
        )
        assert len(result) == 0
        assert list(result) == []
        assert "anything" not in result


class TestResolveResultTopologicalOrder:
    """Tests for the topological_order() method."""

    def test_no_dependencies_returns_alphabetical(self) -> None:
        """Test that independent packages are returned alphabetically."""
        result = ResolveResult(
            mapping={
                "cherry": _make_candidate("cherry"),
                "apple": _make_candidate("apple"),
                "banana": _make_candidate("banana"),
            },
            graph={"cherry": set(), "apple": set(), "banana": set()},
            direct_dependencies=frozenset({"cherry", "apple", "banana"}),
        )
        assert result.topological_order() == ["apple", "banana", "cherry"]

    def test_linear_chain(self) -> None:
        """Test a linear dependency chain: a -> b -> c."""
        result = ResolveResult(
            mapping={
                "a": _make_candidate("a"),
                "b": _make_candidate("b"),
                "c": _make_candidate("c"),
            },
            graph={"a": {"b"}, "b": {"c"}, "c": set()},
            direct_dependencies=frozenset({"a"}),
        )
        order = result.topological_order()
        assert order.index("c") < order.index("b") < order.index("a")

    def test_diamond(self) -> None:
        """Test a diamond: a -> b, a -> c, b -> d, c -> d."""
        result = ResolveResult(
            mapping={
                "a": _make_candidate("a"),
                "b": _make_candidate("b"),
                "c": _make_candidate("c"),
                "d": _make_candidate("d"),
            },
            graph={"a": {"b", "c"}, "b": {"d"}, "c": {"d"}, "d": set()},
            direct_dependencies=frozenset({"a"}),
        )
        order = result.topological_order()
        assert order.index("d") < order.index("b")
        assert order.index("d") < order.index("c")
        assert order.index("b") < order.index("a")
        assert order.index("c") < order.index("a")

    def test_single_package(self) -> None:
        """Test with a single package."""
        result = ResolveResult(
            mapping={"only": _make_candidate("only")},
            graph={"only": set()},
            direct_dependencies=frozenset({"only"}),
        )
        assert result.topological_order() == ["only"]

    def test_empty(self) -> None:
        """Test with no packages."""
        result = ResolveResult(
            mapping={},
            graph={},
            direct_dependencies=frozenset(),
        )
        assert result.topological_order() == []

    def test_multiple_roots(self) -> None:
        """Test with two direct dependencies sharing a transitive dep."""
        result = ResolveResult(
            mapping={
                "app_a": _make_candidate("app_a"),
                "app_b": _make_candidate("app_b"),
                "shared": _make_candidate("shared"),
            },
            graph={"app_a": {"shared"}, "app_b": {"shared"}, "shared": set()},
            direct_dependencies=frozenset({"app_a", "app_b"}),
        )
        order = result.topological_order()
        assert order.index("shared") < order.index("app_a")
        assert order.index("shared") < order.index("app_b")
