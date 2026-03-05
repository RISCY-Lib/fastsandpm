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
"""Dependency resolution subpackage for FastSandPM.

This subpackage provides the core dependency resolution functionality,
including requirement definitions, candidate generation, and resolution
algorithms.

Modules:
    requirements: Defines requirement types for different dependency sources.
    candidates: Implements candidate generation from requirements.
    provider: Provides the dependency resolution provider for resolvelib.

Classes:
    ConcreteRequirement: Union type of all concrete requirement types.
    GitRequirement: Base class for git-based requirements.
    BranchGitRequirement: Git requirement pinned to a specific branch.
    CommitGitRequirement: Git requirement pinned to a specific commit.
    TaggedGitRequirement: Git requirement pinned to a specific tag.
    VersionedGitRequirement: Git requirement with version constraints.
    PackageIndexRequirement: Requirement from a package index.
    PathRequirement: Requirement from a local filesystem path.
"""

from __future__ import annotations

from .requirements import (
    BranchGitRequirement,
    CommitGitRequirement,
    ConcreteRequirement,
    GitRequirement,
    PackageIndexRequirement,
    PathRequirement,
    TaggedGitRequirement,
    VersionedGitRequirement,
)

__all__ = [
    "ConcreteRequirement",
    "GitRequirement",
    "BranchGitRequirement",
    "CommitGitRequirement",
    "TaggedGitRequirement",
    "VersionedGitRequirement",
    "PackageIndexRequirement",
    "PathRequirement",
]
