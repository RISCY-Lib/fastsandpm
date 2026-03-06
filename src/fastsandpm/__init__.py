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
"""A package management and dependency resolution tool for HDL Design and DV projects.

FastSandPM provides tools for managing RTL and Design Verification projects,
including semantic versioning, dependency resolution, and manifest file handling.

Main Features:
    - Parse and validate proj.toml manifest files
    - Resolve dependencies from git repositories, package indices, and local paths
    - Support for semantic versioning with pre-release identifiers
    - Registry-based dependency discovery (GitHub, GitLab, Bitbucket, custom)

Quick Start:
    >>> import fastsandpm
    >>> manifest = fastsandpm.get_manifest("./my-project")
    >>> print(manifest.package.name)
    'my-package'
    >>> resolved = fastsandpm.dependencies.resolve(manifest)
    >>> print(type(resolved))
    <class 'dict'>
    >>> build_library(resolved, pathlib.Path("my-library"))

Included Classes:
    - :py:class:`~manifest.Manifest`: The main manifest model representing a `proj.toml` file.
    - :py:class:`~manifest.Package`: Package metadata (name, version, description, authors).
    - :py:class:`~manifest.ManifestNotFoundError`: Raised when a manifest file cannot be found.
    - :py:class:`~manifest.ManifestParseError`: Raised when a manifest file cannot be parsed.

Functions:
    - :py:func:`~manifest.get_manifest`: Load and parse a manifest from a repository path.
    - :py:func:`~dependencies.resolve`: Resolve all dependencies for a manifest.
    - :py:func:`~install.build_library`: Build a library from a resovled dependency definition.
    - :py:func:`~install.library_from_manifest`: Build a library of dependencies from a manifest.

Attributes:
    __version__ (str): The current version of the FastSandPM package.
    __author__ (str): The primary author of the package.

See Also:
    - fastsandpm.dependencies: Dependency resolution subpackage
    - fastsandpm.versioning: Version handling subpackage
    - fastsandpm.registries: Registry definitions
"""

from __future__ import annotations

from fastsandpm import _info
from fastsandpm.dependencies import (
    resolve,
)
from fastsandpm.install import build_library, library_from_manifest
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
    "resolve",
    "library_from_manifest",
    "build_library",
]
