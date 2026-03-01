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
"""A package management and dependency resolution tool for HDL Design and DV projects

This package provides tools for managing RTL and Design Verification projects for HDL projects
"""

from __future__ import annotations

from fastsandpm import _info
from fastsandpm.manifest import (
    Manifest,
    ManifestNotFoundError,
    ManifestParseError,
    Package,
    get_manifest,
)

__version__ = _info.__version__
__author__ = _info.__author__

__all__ = [
    "__version__",
    "__author__",
    "get_manifest",
    "Manifest",
    "ManifestNotFoundError",
    "ManifestParseError",
    "Package",
]
