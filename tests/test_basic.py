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
"""Tests for fastsandpm."""

from __future__ import annotations

import fastsandpm


def test_version():
    """Test that version is accessible."""
    assert fastsandpm.__version__ is not None
    assert isinstance(fastsandpm.__version__, str)


def test_author():
    """Test that author is accessible."""
    assert fastsandpm.__author__ is not None
    assert isinstance(fastsandpm.__author__, str)
