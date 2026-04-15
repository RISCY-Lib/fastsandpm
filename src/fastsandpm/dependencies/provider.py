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
"""Dependency resolution provider for resolvelib integration.

This module provides the FastSandProvider class that implements the resolvelib
AbstractProvider interface. It handles candidate discovery, preference ordering,
and dependency extraction during the resolution process.

Classes:
    - :py:class:`~FastSandProvider`: The main dependency resolution provider.

Functions:
    - :py:func:`~resolve`: Convenience function to resolve dependencies for a manifest.

Type Aliases:
    - :py:type:`~FastSandReqInfo`: FastSandReqInfo: Type alias for requirement information tuples.
    - :py:type:`~FastSandReporter`: Type alias for the resolution reporter.
"""

from __future__ import annotations

from collections.abc import ItemsView, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import resolvelib
from resolvelib.structs import Matches, RequirementInformation

from fastsandpm.dependencies.candidates import Candidate, candidate_factory
from fastsandpm.dependencies.requirements import ConcreteRequirement, PathRequirement
from fastsandpm.manifest import Manifest
from fastsandpm.registries import Registries
from fastsandpm.versioning.library_version import LibraryVersion as LibraryVersion
from fastsandpm.versioning.specifier import (
    CaretVersionSpecifier,
    ComparisonVersionSpecifier,
    DirectVersionSpecifier,
    RangeVersionSpecifier,
    VersionSpecifier,
)

if TYPE_CHECKING:
    from resolvelib.providers import Preference


FastSandReqInfo = RequirementInformation[ConcreteRequirement, Candidate]
""".. py:type:: FastSandReqInfo:
    Type alias for requirement information tuples.
"""


class FastSandProvider(resolvelib.AbstractProvider[ConcreteRequirement, Candidate, str]):
    """Dependency resolution provider implementing the resolvelib interface.

    This provider handles the core dependency resolution logic, including
    candidate discovery, preference ordering, and requirement satisfaction
    checking. It uses the configured registries to find candidate packages.

    Attributes:
        _registries: The registries used for candidate discovery.
    """

    def __init__(self, registries: Registries) -> None:
        """Initialize the provider with the given registries.

        Args:
            registries: The registries to use for candidate discovery.
        """
        self._registries = registries

    def identify(self, requirement_or_candidate: ConcreteRequirement | Candidate) -> str:
        """Return the identifier for a requirement or candidate.

        The identifier is used to group related requirements and candidates
        during resolution.

        Args:
            requirement_or_candidate: The requirement or candidate to identify.

        Returns:
            The name of the package, which serves as its unique identifier.
        """
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
        try:
            next(iter(information[identifier]))
        except StopIteration:
            has_information = False
        else:
            has_information = True

        if has_information:
            info_reqs: list[ConcreteRequirement] = [r for r, _ in information[identifier]]
        else:
            info_reqs = []

        has_path_req = any(isinstance(r, PathRequirement) for r in info_reqs)
        has_pinned = any(
            isinstance(getattr(r, "version", None), DirectVersionSpecifier) for r in info_reqs
        )

        def _req_has_upper_bound(req: ConcreteRequirement) -> bool:
            if not (version := getattr(req, "version", None)):
                return False
            assert isinstance(version, VersionSpecifier)

            if isinstance(version, CaretVersionSpecifier):
                return True

            if isinstance(version, RangeVersionSpecifier):
                return any(c.operator in ["<", "<=", "^"] for c in version.constraints)

            if isinstance(version, ComparisonVersionSpecifier):
                return version.operator in ["<", "<=", "^"]

            return False

        has_upper_bound = any(_req_has_upper_bound(r) for r in info_reqs)

        return (not has_path_req, not has_pinned, not has_upper_bound, identifier)

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
        """Check if a candidate satisfies a requirement.

        Args:
            requirement: The requirement to check.
            candidate: The candidate to evaluate.

        Returns:
            True if the candidate satisfies the requirement, False otherwise.
        """
        return candidate.satisfies(requirement)

    def get_dependencies(self, candidate: Candidate) -> list[ConcreteRequirement]:
        """Get the dependencies declared by a candidate.

        Retrieves the candidate's manifest and extracts its declared dependencies.
        Also merges any registries declared in the candidate's manifest into the
        provider's registry list.

        Args:
            candidate: The candidate to get dependencies for.

        Returns:
            A list of requirements declared as dependencies by the candidate.
            Returns an empty list if the candidate has no manifest.
        """
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
        """Narrow down which requirements to resolve next.

        This method can be used to optimize the resolution order by filtering
        or reordering the identifiers. Currently passes through to the base
        implementation without modification.

        Args:
            identifiers: Iterable of requirement identifiers to consider.
            resolutions: Mapping of already-resolved identifiers to candidates.
            candidates: Mapping of identifiers to their candidate iterators.
            information: Mapping of identifiers to requirement information.
            backtrack_causes: Sequence of requirements that caused backtracking.

        Returns:
            A filtered/reordered list of identifiers to process next.
        """
        return [
            req
            for req in super().narrow_requirement_selection(
                identifiers, resolutions, candidates, information, backtrack_causes
            )
        ]


FastSandReporter = resolvelib.BaseReporter[ConcreteRequirement, Candidate, str]
"""Type alias for the resolution reporter."""


@dataclass(frozen=True)
class ResolveResult:
    """Result of dependency resolution, containing resolved packages and their dependency graph.

    The mapping contains all resolved packages keyed by name. The graph preserves
    the dependency relationships computed by the resolver, avoiding the need to
    re-read manifests from disk to reconstruct them.

    Attributes:
        mapping: Dictionary mapping package names to their resolved Candidate objects.
        graph: Dictionary mapping each package name to the set of package names it
            depends on. Only includes dependencies that are themselves in the resolved set.
        direct_dependencies: The set of package names that were direct (user-specified)
            dependencies, as opposed to transitive dependencies.
    """

    mapping: dict[str, Candidate]
    graph: dict[str, set[str]]
    direct_dependencies: frozenset[str]

    def items(self) -> ItemsView[str, Candidate]:
        """Return items view of the mapping, for dict-like iteration."""
        return self.mapping.items()

    def __getitem__(self, key: str) -> Candidate:
        """Get a candidate by package name."""
        return self.mapping[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over package names."""
        return iter(self.mapping)

    def __len__(self) -> int:
        """Return the number of resolved packages."""
        return len(self.mapping)

    def __contains__(self, key: object) -> bool:
        """Check if a package name is in the resolved set."""
        return key in self.mapping

    def topological_order(self) -> list[str]:
        """Return package names in topological order (dependencies first).

        Packages that have no dependencies on other resolved packages appear
        first, followed by packages whose dependencies have already appeared.
        Ties are broken alphabetically for deterministic output.

        Returns:
            List of package names sorted so that every package appears after
            all of its dependencies.
        """
        # Count unresolved dependencies for each node
        remaining_deps: dict[str, int] = {
            name: len(deps) for name, deps in self.graph.items()
        }

        # Build reverse lookup: for each dep, which nodes depend on it?
        dependents: dict[str, set[str]] = {name: set() for name in self.graph}
        for name, deps in self.graph.items():
            for dep in deps:
                if dep in dependents:
                    dependents[dep].add(name)

        # Start with nodes that have no dependencies
        queue = sorted(
            name for name in self.graph if remaining_deps[name] == 0
        )
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for dependent in dependents.get(node, set()):
                remaining_deps[dependent] -= 1
                if remaining_deps[dependent] == 0:
                    queue.append(dependent)
                    queue.sort()

        return result


def resolve(
    manifest: Manifest, optional_deps: list[str] | None = None
) -> ResolveResult:
    """Resolve all dependencies for a manifest.

    Creates a FastSandProvider with the manifest's registries and runs the
    resolvelib resolver to find a compatible set of candidates for all
    declared dependencies.

    Args:
        manifest: The manifest containing dependencies to resolve.
        optional_deps: Optional dependency groups to include in the library.

    Returns:
        A ResolveResult containing the resolved packages, their dependency graph,
        and the set of direct dependencies.

    Raises:
        resolvelib.ResolutionImpossible: If no compatible resolution exists.

    Example:
        >>> from fastsandpm import get_manifest
        >>> from fastsandpm.dependencies.provider import resolve
        >>> manifest = get_manifest("./my-project")
        >>> resolved = resolve(manifest)
        >>> for name, candidate in resolved.items():
        ...     print(f"{name}: {candidate.version}")
    """
    provider = FastSandProvider(manifest.registries)
    reporter: FastSandReporter = resolvelib.BaseReporter()

    resolver = resolvelib.Resolver(provider, reporter)

    dependencies = [dep for dep in manifest.dependencies]
    if optional_deps:
        for group in optional_deps:
            if group in manifest.optional_dependencies:
                dependencies.extend(manifest.optional_dependencies[group])

    result = resolver.resolve(dependencies)

    # Convert resolvelib's DirectedGraph to a plain dict,
    # excluding the None root vertex.
    dep_graph: dict[str, set[str]] = {}
    for name in result.mapping:
        dep_graph[name] = {
            child for child in result.graph.iter_children(name)
            if child is not None
        }

    direct_deps = frozenset(
        child for child in result.graph.iter_children(None)
        if child is not None
    )

    return ResolveResult(
        mapping=result.mapping,
        graph=dep_graph,
        direct_dependencies=direct_deps,
    )
