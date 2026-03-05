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

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING

import resolvelib
from resolvelib.structs import Matches, RequirementInformation

from fastsandpm.dependencies.candidates import Candidate, candidate_factory
from fastsandpm.dependencies.requirements import ConcreteRequirement
from fastsandpm.manifest import Manifest
from fastsandpm.registries import Registries
from fastsandpm.versioning.library_version import LibraryVersion as LibraryVersion

if TYPE_CHECKING:
    from resolvelib.providers import Preference


FastSandReqInfo = RequirementInformation[ConcreteRequirement, Candidate]


class FastSandProvider(resolvelib.AbstractProvider[ConcreteRequirement, Candidate, str]):
    def __init__(self, registries: Registries) -> None:
        self._registries = registries

    def identify(self, requirement_or_candidate: ConcreteRequirement | Candidate) -> str:
        return requirement_or_candidate.name

    def get_preference(
        self,
        identifier: str,
        resolutions: Mapping[str, Candidate],
        candidates: Mapping[str, Iterator[Candidate]],
        information: Mapping[str, Iterator[FastSandReqInfo]],
        backtrack_causes: Sequence[FastSandReqInfo],
    ) -> Preference:
        """Produce a sort key for given requirement based on preference.

        The lower the return value is, the more preferred this group of
        arguments is.

        Currently fastsandpm considers the following in order:

        * Any requirement that is a path
        * Any requirement that is "git" and "direct", e.g., points to an explicit URL.
        * Any requirement that is "git" and "pinned", i.e., points to a specific tag or version
          or ``==`` without a wildcard.
        * Any requirement that imposes an upper version limit, i.e., contains the
          operator ``<``, ``<=``, or ``^`` with a wildcard. Because
          fastsand prioritizes the latest version, preferring explicit upper bounds
          can rule out infeasible candidates sooner. This does not imply that
          upper bounds are good practice; they can make dependency management
          and resolution harder.
        * Order user-specified requirements as they are specified, placing
          other requirements afterward.
        * Any "non-free" requirement, i.e., one that contains at least one
          operator, such as ``>=`` or ``!=``.
        * Alphabetical order for consistency (aids debuggability).
        """
        return identifier

    def find_matches(
        self,
        identifier: str,
        requirements: Mapping[str, Iterator[ConcreteRequirement]],
        incompatibilities: Mapping[str, Iterator[Candidate]],
    ) -> Matches[Candidate]:
        """Find all possible candidates that satisfy the given constraints.

        Gets all candidates for all requirements of the identifier.
        Then filters out the Candidates previously marked as incompatible.

        Args:
            identifier: An identifier as returned by ``identify()``. All
                candidates returned by this method should produce the same
                identifier.
            requirements: A mapping of requirements that all returned
                candidates must satisfy. Each key is an identifier, and the value
                an iterator of requirements for that dependency.
            incompatibilities: A mapping of known incompatibile candidates of
                each dependency. Each key is an identifier, and the value an
                iterator of incompatibilities known to the resolver. All
                incompatibilities *must* be excluded from the return value.
        """
        # Collect all requirements for this identifier
        reqs_for_identifier = list(requirements.get(identifier, iter([])))

        # Collect all incompatible candidates for this identifier
        incompatible_candidates = set(incompatibilities.get(identifier, iter([])))

        # Get all candidates from all requirements
        all_candidates: list[Candidate] = []
        for req in reqs_for_identifier:
            all_candidates.extend(candidate_factory(req, self._registries))

        # Filter out incompatible candidates
        filtered_candidates = [c for c in all_candidates if c not in incompatible_candidates]

        # Filter to only candidates that satisfy ALL requirements
        def satisfies_all(candidate: Candidate) -> bool:
            return all(candidate.satisfies(req) for req in reqs_for_identifier)

        matching_candidates = [c for c in filtered_candidates if satisfies_all(c)]

        # Remove duplicates while preserving order
        seen: set[Candidate] = set()
        unique_candidates: list[Candidate] = []
        for c in matching_candidates:
            if c not in seen:
                seen.add(c)
                unique_candidates.append(c)

        return unique_candidates

    def is_satisfied_by(self, requirement: ConcreteRequirement, candidate: Candidate) -> bool:
        return candidate.satisfies(requirement)

    def get_dependencies(self, candidate: Candidate) -> list[ConcreteRequirement]:
        """Get the dependencies of a candidate."""
        if candidate_manifest := candidate.get_manifest():
            self._registries.root.extend(candidate_manifest.registries)
            return candidate_manifest.dependencies.root
        return []

    def narrow_requirement_selection(
        self,
        identifiers: Iterable[str],
        resolutions: Mapping[str, Candidate],
        candidates: Mapping[str, Iterator[Candidate]],
        information: Mapping[str, Iterator[FastSandReqInfo]],
        backtrack_causes: Sequence[FastSandReqInfo],
    ) -> list[str]:
        return [
            req
            for req in super().narrow_requirement_selection(
                identifiers, resolutions, candidates, information, backtrack_causes
            )
        ]


FastSandReporter = resolvelib.BaseReporter[ConcreteRequirement, Candidate, str]


def resolve(manifest: Manifest) -> dict[str, Candidate]:
    provider = FastSandProvider(manifest.registries)
    reporter: FastSandReporter = resolvelib.BaseReporter()

    resolver = resolvelib.Resolver(provider, reporter)
    result = resolver.resolve(manifest.dependencies)
    return result.mapping
