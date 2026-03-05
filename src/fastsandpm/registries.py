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
"""Module for package registry definitions and management.

This module provides registry types for resolving package dependencies from
various sources including git hosts, package indices, and local paths.

Classes:
    DependencyNotFoundError: Exception raised when a dependency cannot be found.
    GitRegistry: Registry for resolving dependencies from git hosts.
    PackageIndexRegistery: Registry for resolving dependencies from package indices.
    PathRegistry: Registry for resolving dependencies from local filesystem paths.
    Registries: Collection of registries used during dependency resolution.

Type Aliases:
    ConcreteRegistry: Union type of all concrete registry types.
"""

from __future__ import annotations

import pathlib
from typing import Any, ClassVar, Self

from pydantic import BaseModel, RootModel, model_validator


class DependencyNotFoundError(RuntimeError):
    """Exception raised when a dependency cannot be found in any registry.

    This error is raised during dependency resolution when a required package
    cannot be located in any of the configured registries.
    """


class GitRegistry(BaseModel):
    """A Git Remote Registry for resolving dependencies from git hosts.

    This registry handles dependencies that are resolved from git repositories
    at a remote host (e.g., GitHub, GitLab, Bitbucket). It manages looking up,
    fetching manifests from, and cloning dependencies from the specified remote.
    """

    name: str
    """Name of the registry"""
    remote: str
    """URL of the registry"""


_GITHUB_REGISTRY = GitRegistry(name="github", remote="https://github.com")
_GITLAB_REGISTRY = GitRegistry(name="gitlab", remote="https://gitlab.com")
_BITBUCKET_REGISTRY = GitRegistry(name="bitbucket", remote="https://bitbucket.org")


class PackageIndexRegistery(BaseModel):
    """A Package Index Registry for resolving dependencies from package indices.

    This registry handles dependencies resolved from package indices (e.g., JFrog
    Artifactory, PyPI). Implementation is not yet complete - all methods raise
    NotImplementedError as the feature is still under development.
    """

    name: str
    """Name of the registry"""
    index: str
    """URL of the registry"""


class PathRegistry(BaseModel):
    """A local Path Registry for resolving dependencies from the filesystem.

    This registry handles dependencies that are stored as local paths on the
    filesystem. It is useful for monorepo setups or local development where
    dependencies are checked out locally.
    """

    name: str
    """Name of the registry"""
    path: pathlib.Path
    """Path to the registry"""


_LOCAL_PATH_REGISTRY = PathRegistry(name="local_path", path=pathlib.Path("."))


ConcreteRegistry = GitRegistry | PackageIndexRegistery | PathRegistry


class Registries(RootModel[list[ConcreteRegistry]]):
    """A collection of registries for resolving dependencies.

    This class manages a list of registries (Git, Package Index, and Path) that
    are used to locate and fetch dependencies. It provides methods to query
    registries by type and to find the appropriate registry for a given dependency.

    Default registries are automatically added if not explicitly provided, including
    GitHub, GitLab, Bitbucket, a qualified git registry for full URLs, and a local
    path registry.

    .. seealso::

        See `Pydantic RootModel <https://docs.pydantic.dev/latest/api/root_model/>`__
        for details on the base class and its methods.
    """

    _DEFAULT_REGISTRIES: ClassVar[list[GitRegistry | PackageIndexRegistery | PathRegistry]] = [
        _GITHUB_REGISTRY,
        _GITLAB_REGISTRY,
        _BITBUCKET_REGISTRY,
        _LOCAL_PATH_REGISTRY,
    ]

    @model_validator(mode="before")
    @classmethod
    def parse_dependencies(cls, data: Any) -> Any:
        """Parse registry data from various formats.

        Handles conversion from TOML-style registry specifications to
        the internal registry model format.

        Args:
            data: Raw registry data, either as a dict (from TOML) or list.

        Returns:
            A list of registry dictionaries ready for model instantiation.

        Examples:
            Input formats supported:
            - {"name": "foo", "remote": "url"} -> [{"name": "foo", ...}]
            - {"foo": "url"} -> [{"name": "foo", "remote": "url"}]
            - {"foo": {"remote": "url"}} -> [{"name": "foo", "remote": "url"}]
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
                    new_data.append({"name": name, "index": spec})
                else:
                    # Pass through as-is (will fail validation if invalid)
                    new_data.append({"name": name, "version": spec})
            return new_data

        return data

    @model_validator(mode="after")
    def validate_unique_names(self) -> Self:
        """Validate that all registry names are unique.

        Raises:
            ValueError: If duplicate dependency names are found.

        Returns:
            Self: The validated model instance.
        """
        names = [reg.name for reg in self.root]
        duplicates = [name for name in names if names.count(name) > 1]

        if duplicates:
            unique_duplicates = list(set(duplicates))
            raise ValueError(f"Duplicate dependency names found: {unique_duplicates}")

        return self

    @model_validator(mode="after")
    def add_default_registries(self) -> Self:
        """Add default registries if none are present.

        Returns:
            Self: The validated model instance.
        """
        for reg in self._DEFAULT_REGISTRIES:
            if self.get_by_name(reg.name) is None:
                self.root.append(reg)

        return self

    def __iter__(self):
        """Iterate over the registries.

        Returns:
            Iterator over the registry list.
        """
        return iter(self.root)

    def __len__(self) -> int:
        """Return the number of dependencies.

        Returns:
            The count of dependencies.
        """
        return len(self.root)

    def __getitem__(self, index: int) -> GitRegistry | PackageIndexRegistery | PathRegistry:
        """Get a dependency by index.

        Args:
            index: The index of the dependency to retrieve.

        Returns:
            The dependency at the specified index.
        """
        return self.root[index]

    def get_by_name(self, name: str) -> GitRegistry | PackageIndexRegistery | PathRegistry | None:
        """Get a dependency by its name.

        Args:
            name: The name of the dependency to find.

        Returns:
            The dependency with the specified name, or None if not found.
        """
        for reg in self.root:
            if reg.name == name:
                return reg
        return None

    def git_registries(self) -> list[GitRegistry]:
        """Get all git registries.

        Returns:
            A list of all GitRegistry instances.
        """
        return [reg for reg in self.root if isinstance(reg, GitRegistry)]

    def package_index_registries(self) -> list[PackageIndexRegistery]:
        """Get all package index registries.

        Returns:
            A list of all PackageIndexRegistery instances.
        """
        return [reg for reg in self.root if isinstance(reg, PackageIndexRegistery)]

    def path_registries(self) -> list[PathRegistry]:
        """Get all path registries.

        Returns:
            A list of all PathRegistry instances.
        """
        return [reg for reg in self.root if isinstance(reg, PathRegistry)]
