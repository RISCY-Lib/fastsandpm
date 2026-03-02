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
"""Module which contains the types for package dependencies.

This module provides classes for specifying package dependencies using
different specifiers:

- Registry: Fetch from a package registry (name + version)
- Git: Fetch from a git repository (URL or project ID)
- Path: Use a local path as a dependency

Classes:
    Dependency: Base dependency with just a name.
    RegistryDependency: Registry-based dependency with name, version, and optional registry.
    GitDependency: Git-based dependency with URL/project ID and version specifiers.
    PathDependency: Local path-based dependency.
    Dependencies: Collection of dependencies with parsing support.
"""

from __future__ import annotations

import pathlib
from typing import Annotated, Any, Protocol, Self

from pydantic import BaseModel, Field, RootModel, model_validator


class Dependency(Protocol):
    """A basic dependency which only contains the package name.

    This is used as a base for other dependency types and for simple
    dependency references without version constraints.

    """

    name: str
    """The name of the dependency package."""


class RegistryDependency(BaseModel):
    """A registry-based dependency specifier.

    Registry dependencies are fetched from a package registry (e.g., JFrog Artifactory).
    They require a name and version, with an optional registry specification for
    fetching from alternative registries.

    Example TOML formats:

    .. code-block:: TOML

        [dependencies]
        time = "1.0.0"

        [dependencies]
        time = {version = "1.0.0", registry = "my-registry"}

    .. seealso::

        See `Pydantic BaseModel <https://docs.pydantic.dev/latest/api/base_model/>`__
        for details on the parent BaseModel class and it's methods.
    """

    name: str
    """The name of the dependency package."""

    version: str
    """The version specifier of the registry dependency package.

    This can be an exact version (e.g., "1.0.0") or a version range
    (e.g., ">=1.0.0,<2.0.0", "^1.2.3").
    """

    registry: str | None = None
    """Optional registry name to fetch the dependency from.

    If not specified, the default registry is used. The value should
    correspond to a registry defined in the [registries] section of
    the manifest.
    """


class GitDependency(BaseModel):
    """A git-based dependency specifier.

    Git dependencies are fetched from a git repository. They can be specified
    using a full URL or a project/organization name. The version can be
    controlled using version specifiers, branches, tags, or specific commits.

    Example TOML formats:

    .. code-block:: TOML

        [dependencies]
        time = {git = "https://github.com/username/repo.git"}
        dep2 = {git = "SOME_ORG"}
        dep3 = {git = "https://github.com/username/repo.git", version = "1.0.0"}
        dep4 = {git = "https://github.com/username/repo.git", branch = "develop"}
        dep5 = {git = "https://github.com/username/repo.git", tag = "v1.0.0"}
        dep6 = {git = "https://github.com/username/repo.git", commit = "deadbeef"}

    .. seealso::

        See `Pydantic BaseModel <https://docs.pydantic.dev/latest/api/base_model/>`__
        for details on the parent BaseModel class and it's methods.
    """

    name: str
    """The name of the dependency package."""

    git: str
    """The git URL or project ID of the dependency package.

    Can be a full URL (e.g., "https://github.com/username/repo.git")
    or a project/organization name (e.g., "SOME_ORG") which will be
    resolved to a git URL by searching known git hosts.
    """

    version: str | None = None
    """The version specifier of the git dependency package.

    When specified, the dependency resolver will look for git tags that
    match the semantic version. Tags must follow semantic versioning
    (optionally prefixed with 'v' or 'V').
    """

    branch: str | None = None
    """The branch of the git dependency package to use.

    When specified, the latest commit from this branch will be used.
    """

    tag: str | None = None
    """The tag of the git dependency package to use.

    When specified, the exact tag will be checked out.
    """

    commit: str | None = None
    """The commit hash of the git dependency package to use.

    When specified, the exact commit will be checked out. Can be a
    full or abbreviated commit hash.
    """

    @model_validator(mode="after")
    def mutually_exclusive_version_specifiers(self) -> Self:
        """Validate that only one version specifier type is used.

        Raises:
            ValueError: If more than one of version, branch, tag, or commit
                is specified.

        Returns:
            Self: The validated model instance.
        """
        specifiers = [self.version, self.branch, self.tag, self.commit]
        if sum(x is not None for x in specifiers) > 1:
            raise ValueError(
                "Only one version specifier type can be used: version, branch, tag, or commit"
            )
        return self


class PathDependency(BaseModel):
    """A local path-based dependency specifier.

    Path dependencies allow specifying a local directory as a dependency.
    The path should contain an FastSandPM manifest file. This is useful for
    monorepo setups or local development.

    Example TOML format:

    .. code-block:: TOML

        [dependencies]
        time = {path = "./some/path/to/dep1"}

    .. seealso::

        See `Pydantic BaseModel <https://docs.pydantic.dev/latest/api/base_model/>`__
        for details on the parent BaseModel class and it's methods.
    """

    name: str
    """The name of the dependency package."""

    path: pathlib.Path
    """The local path to the dependency.

    This path is relative to the location of the manifest file and
    should point to a directory containing an FastSandPM manifest.
    """


# Annotated type for discriminated union parsing
AnyDependency = Annotated[
    RegistryDependency | GitDependency | PathDependency,
    Field(discriminator=None),
]


class Dependencies(RootModel[list[GitDependency | PathDependency | RegistryDependency]]):
    """A collection of dependencies which the package relies on.

    This class handles parsing dependencies from various TOML formats into
    the appropriate dependency type objects. It supports:

    - Simple string format: `name = "version"`
    - Registry format: `name = {version = "1.0.0"}`
    - Git format: `name = {git = "url", ...}`
    - Path format: `name = {path = "./local/path"}`

    The model validator automatically converts dictionary-style TOML
    dependencies into the correct dependency type based on the keys present.

    .. seealso::

        See `Pydantic RootModel <https://docs.pydantic.dev/latest/api/root_model/>`__
        for details on the base class and it's methods.
    """

    @model_validator(mode="before")
    @classmethod
    def parse_dependencies(cls, data: Any) -> Any:
        """Parse dependency data from various formats.

        Handles conversion from TOML-style dependency specifications to
        the internal dependency model format.

        Args:
            data: Raw dependency data, either as a dict (from TOML) or list.

        Returns:
            A list of dependency dictionaries ready for model instantiation.

        Examples:
            Input formats supported:
            - {"name": "foo", "version": "1.0.0"} -> [{"name": "foo", ...}]
            - {"foo": "1.0.0"} -> [{"name": "foo", "version": "1.0.0"}]
            - {"foo": {"git": "url"}} -> [{"name": "foo", "git": "url"}]
            - {"foo": {"path": "./path"}} -> [{"name": "foo", "path": "./path"}]
        """
        if isinstance(data, dict):
            # Handle single dependency passed as dict with 'name' key
            if "name" in data:
                return [data]

            # Convert dict-style dependencies to list
            new_data = []
            for name, spec in data.items():
                if isinstance(spec, dict):
                    # Dict specification: {git: ..., version: ...} or {path: ...}
                    new_data.append({"name": name, **spec})
                elif isinstance(spec, str):
                    # Simple string specification: "version" -> RegistryDependency
                    new_data.append({"name": name, "version": spec})
                else:
                    # Pass through as-is (will fail validation if invalid)
                    new_data.append({"name": name, "version": spec})
            return new_data

        return data

    @model_validator(mode="after")
    def validate_unique_names(self) -> Self:
        """Validate that all dependency names are unique.

        Raises:
            ValueError: If duplicate dependency names are found.

        Returns:
            Self: The validated model instance.
        """
        names = [dep.name for dep in self.root]
        duplicates = [name for name in names if names.count(name) > 1]

        if duplicates:
            unique_duplicates = list(set(duplicates))
            raise ValueError(f"Duplicate dependency names found: {unique_duplicates}")

        return self

    def __iter__(self):
        """Iterate over the dependencies.

        Returns:
            Iterator over the dependency list.
        """
        return iter(self.root)

    def __len__(self) -> int:
        """Return the number of dependencies.

        Returns:
            The count of dependencies.
        """
        return len(self.root)

    def __getitem__(self, index: int) -> Dependency:
        """Get a dependency by index.

        Args:
            index: The index of the dependency to retrieve.

        Returns:
            The dependency at the specified index.
        """
        return self.root[index]

    def get_by_name(self, name: str) -> RegistryDependency | GitDependency | PathDependency | None:
        """Get a dependency by its name.

        Args:
            name: The name of the dependency to find.

        Returns:
            The dependency with the specified name, or None if not found.
        """
        for dep in self.root:
            if dep.name == name:
                return dep
        return None

    def registry_dependencies(self) -> list[RegistryDependency]:
        """Get all registry-type dependencies.

        Returns:
            A list of all RegistryDependency instances.
        """
        return [dep for dep in self.root if isinstance(dep, RegistryDependency)]

    def git_dependencies(self) -> list[GitDependency]:
        """Get all git-type dependencies.

        Returns:
            A list of all GitDependency instances.
        """
        return [dep for dep in self.root if isinstance(dep, GitDependency)]

    def path_dependencies(self) -> list[PathDependency]:
        """Get all path-type dependencies.

        Returns:
            A list of all PathDependency instances.
        """
        return [dep for dep in self.root if isinstance(dep, PathDependency)]
