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

Included Classes:
    - :py:class:`~requirements.ConcreteRequirement`: Union type of all concrete requirement types.
    - :py:class:`~requirements.GitRequirement`: Base class for git-based requirements.
    - :py:class:`~requirements.BranchGitRequirement`: Git requirement pinned to a specific branch.
    - :py:class:`~requirements.CommitGitRequirement`: Git requirement pinned to a specific commit.
    - :py:class:`~requirements.TaggedGitRequirement`: Git requirement pinned to a specific tag.
    - :py:class:`~requirements.VersionedGitRequirement`: Git requirement with version constraints.
    - :py:class:`~requirements.PackageIndexRequirement`: Requirement from a package index.
    - :py:class:`~requirements.PathRequirement`: Requirement from a local filesystem path.
    - :py:class:`~candidates.Candidate`: Abstract base class for dependency candidates.
    - :py:class:`~candidates.PackageIndexCandidate`: Candidate from a package index registry.
    - :py:class:`~candidates.PathCandidate`: Candidate from a local filesystem path.
    - :py:class:`~candidates.GitCandidate`: Candidate from a git repository.

Included Classes (continued):
    - :py:class:`~provider.ResolveResult`: Result of dependency resolution containing the resolved
      packages and their dependency graph.

Included Functions:
    - :py:func:`~candidates.candidate_factory`: Singledispatch function to create candidates
      from requirements.

    - :py:func:`~provider.resolve`: Resolve all dependencies for a manifest.
"""

from __future__ import annotations

from .candidates import (
    Candidate,
    GitCandidate,
    PackageIndexCandidate,
    PathCandidate,
    candidate_factory,
)
from .provider import ResolveResult, resolve
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
    "Candidate",
    "PackageIndexCandidate",
    "PathCandidate",
    "GitCandidate",
    "candidate_factory",
    "ResolveResult",
    "resolve",
]
