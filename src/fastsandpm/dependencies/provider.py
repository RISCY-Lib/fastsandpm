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

from fastsandpm.dependencies.candidates import Candidate
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
        backtrack_causes: Sequence[FastSandReqInfo]
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
        print("get_preference(")
        print(f"\t{identifier=}")
        print(f"\t{resolutions=}")
        print(f"\t{candidates=}")
        print(f"\t{information=}")
        print(f"\t{backtrack_causes=}")
        print(")\n")
        raise NotImplementedError

    def find_matches(
        self,
        identifier: str,
        requirements: Mapping[str, Iterator[ConcreteRequirement]],
        incompatibilities: Mapping[str, Iterator[Candidate]]
    ) -> Matches[Candidate]:
        raise NotImplementedError

    def is_satisfied_by(self, requirement: ConcreteRequirement, candidate: Candidate) -> bool:
        raise NotImplementedError

    def get_dependencies(self, candidate: Candidate) -> list[ConcreteRequirement]:
        raise NotImplementedError

    def narrow_requirement_selection(
        self,
        identifiers: Iterable[str],
        resolutions: Mapping[str, Candidate],
        candidates: Mapping[str, Iterator[Candidate]],
        information: Mapping[str, Iterator[FastSandReqInfo]],
        backtrack_causes: Sequence[FastSandReqInfo]
    ) -> list[str]:
        return [req for req in super().narrow_requirement_selection(
            identifiers,
            resolutions,
            candidates,
            information,
            backtrack_causes
        )]


FastSandReporter = resolvelib.BaseReporter[ConcreteRequirement, Candidate, str]


def resolve(manifest: Manifest):
    provider = FastSandProvider(manifest.registries)
    reporter: FastSandReporter = resolvelib.BaseReporter()

    resolver = resolvelib.Resolver(provider, reporter)
    result = resolver.resolve(manifest.dependencies)
    return result
