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
"""Module which contains the types for the package manifest.

This module provides:
- Manifest: The main manifest model representing a proj.toml file
- Package: The package metadata section of the manifest
- get_manifest: Function to load and parse a manifest from a repository path
"""

from __future__ import annotations

import os
import pathlib
import tomllib
from typing import Annotated, Any, Self, SupportsIndex

from pydantic import (
    BaseModel,
    Field,
    PlainSerializer,
    PlainValidator,
    RootModel,
    ValidationError,
    WithJsonSchema,
    model_validator,
)

from fastsandpm.dependencies.requirements import ConcreteRequirement
from fastsandpm.registries import Registries
from fastsandpm.versioning import LibraryVersion

_Version = Annotated[
    LibraryVersion,
    PlainValidator(lambda v: LibraryVersion(v), json_schema_input_type=str),
    PlainSerializer(lambda v: str(v), return_type=str),
    WithJsonSchema({"type": "string"}),
]


class ManifestNotFoundError(FileNotFoundError):
    """Raised when a manifest file cannot be found at the specified path."""

    def __init__(self, path: pathlib.Path) -> None:
        """Initialize the error with the path that was searched.

        Args:
            path: The path where the manifest was expected.
        """
        self.path = path
        super().__init__(f"Manifest file not found: {path / MANIFEST_FILENAME}")


class ManifestParseError(ValueError):
    """Raised when a manifest file cannot be parsed."""

    def __init__(self, path: pathlib.Path, reason: str) -> None:
        """Initialize the error with the path and reason for failure.

        Args:
            path: The path to the manifest file.
            reason: Description of why parsing failed.
        """
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to parse manifest at {path}: {reason}")


class Package(BaseModel):
    """The package details from a package manifest.

    Example TOML:

    .. code-block:: TOML

        [package]
        name = "package_name"
        version = "1.2.3-a4"
        description = "A sample package"

        authors = "Jane Doe <jdoe@doelife.com>"
        readme = "README.txt"

    .. seealso::

        See `Pydantic BaseModel <https://docs.pydantic.dev/latest/api/base_model/>`__
        for details on the parent BaseModel class and it's methods.
    """

    name: str
    """The name of the package."""
    version: _Version
    """The version of the package."""
    description: str
    """The description of the package."""

    authors: str | list[str] | dict[str, str] | None = None
    """The authors of the package."""
    readme: pathlib.Path | None = None  # TODO: Field(default_factory=_find_readme)
    """The readme of the package."""


class Dependencies(RootModel[list[ConcreteRequirement]]):
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

    def __getitem__(self, index: int) -> ConcreteRequirement:
        """Get a dependency by index.

        Args:
            index: The index of the dependency to retrieve.

        Returns:
            The dependency at the specified index.
        """
        return self.root[index]

    def append(self, object: ConcreteRequirement) -> None:
        """Append a dependency to the collection.

        Args:
            object: The dependency to append to the end of the collection.
        """
        self.root.append(object)

    def insert(self, index: SupportsIndex, object: ConcreteRequirement) -> None:
        """Insert a dependency at a specific position.

        Args:
            index: The position where the dependency should be inserted.
            object: The dependency to insert into the collection.
        """
        self.root.insert(index, object)

    def get_by_name(self, name: str) -> ConcreteRequirement | None:
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


class Manifest(BaseModel):
    """The package manifest.

    .. seealso::

        See `Pydantic BaseModel <https://docs.pydantic.dev/latest/api/base_model/>`__
        for details on the parent BaseModel class and it's methods.

    .. seealso::

        See :py:class:`Package` and :py:class:`Dependencies` for details on the child sections of
        the manifest.
    """

    package: Package
    """The package metadata found in the 'package' section of the manifest."""

    dependencies: Dependencies = Field(default_factory=lambda: Dependencies(list()))
    """The package dependencies found in the 'dependencies' section of the manifest."""
    optional_dependencies: dict[str, Dependencies] = Field(default_factory=dict)
    """The package optional dependencies found in the 'optional_dependencies'
    section of the manifest.
    """

    registries: Registries = Field(default_factory=lambda: Registries(list()))
    """Registries found in the 'registries' section of the manifest."""

    @model_validator(mode="before")
    @classmethod
    def parse_optional_dependencies(cls, data: Any) -> Any:
        """Parse optional_dependencies from various TOML formats.

        Handles conversion from TOML-style optional dependency specifications:
        - List format: [optional_dependencies] group = [{name="foo", version="1.0"}]
        - Table format: [optional_dependencies.group] foo = "1.0"

        Args:
            data: Raw manifest data from TOML parsing.

        Returns:
            The data with optional_dependencies converted to list format.
        """
        if not isinstance(data, dict):
            return data

        if "optional_dependencies" not in data:
            return data

        opt_deps = data["optional_dependencies"]
        if not isinstance(opt_deps, dict):
            return data

        new_opt_deps: dict[str, list[dict[str, Any]]] = {}

        for group_name, group_deps in opt_deps.items():
            if isinstance(group_deps, list):
                # Already in list format: [{name="foo", version="1.0"}]
                new_opt_deps[group_name] = group_deps
            elif isinstance(group_deps, dict):
                # Table format: {foo = "1.0", bar = {version = "2.0"}}
                # Convert to list format
                deps_list: list[dict[str, Any]] = []
                for dep_name, dep_spec in group_deps.items():
                    if isinstance(dep_spec, dict):
                        deps_list.append({"name": dep_name, **dep_spec})
                    elif isinstance(dep_spec, str):
                        deps_list.append({"name": dep_name, "version": dep_spec})
                    else:
                        deps_list.append({"name": dep_name, "version": dep_spec})
                new_opt_deps[group_name] = deps_list
            else:
                # Pass through as-is (will fail validation if invalid)
                new_opt_deps[group_name] = group_deps

        data["optional_dependencies"] = new_opt_deps
        return data


#: The default manifest filename
MANIFEST_FILENAME = "proj.toml"


def get_manifest(path: os.PathLike) -> Manifest:
    """Load and parse a manifest from a repository path.

    Looks for a `proj.toml` file in the specified directory, parses it,
    and returns a Manifest object.

    Args:
        path: Path to the repository directory containing the proj.toml file.

    Returns:
        The parsed Manifest object.

    Raises:
        ManifestNotFoundError: If the proj.toml file does not exist at the path.
        ManifestParseError: If the TOML file is malformed or doesn't match
            the expected manifest schema.

    Example:
        >>> import pathlib
        >>> import fastsandpm
        >>> manifest = fastsandpm.get_manifest(pathlib.Path("some/repo/path"))
        >>> print(manifest.package.name)
        'my-package'
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    manifest_path = path / MANIFEST_FILENAME

    # Check if the manifest file exists
    if not manifest_path.exists():
        raise ManifestNotFoundError(path)

    if not manifest_path.is_file():
        raise ManifestParseError(path, f"{MANIFEST_FILENAME} is not a file")

    # Read and parse the TOML file
    try:
        with manifest_path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ManifestParseError(path, f"Invalid TOML syntax: {e}") from e

    # Parse the data into a Manifest object
    try:
        return Manifest.model_validate(data)
    except ValidationError as e:
        raise ManifestParseError(path, str(e)) from e


def get_manifest_from_bytes(content: bytes, source: str = "<bytes>") -> Manifest:
    """Parse a manifest from raw bytes content.

    This function is useful for parsing manifest content that has been fetched
    from a remote source (e.g., via `git archive`) without writing to disk.

    Args:
        content: The raw bytes content of a proj.toml file.
        source: A string identifying the source of the content (for error messages).

    Returns:
        The parsed Manifest object.

    Raises:
        ManifestParseError: If the TOML content is malformed or doesn't match
            the expected manifest schema.

    Example:
        >>> content = b'[package]\\nname = "my-pkg"\\nversion = "1.0.0"\\n...'
        >>> manifest = get_manifest_from_bytes(content, source="git://repo")
        >>> print(manifest.package.name)
        'my-pkg'
    """
    # Parse the TOML content
    try:
        data = tomllib.loads(content.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise ManifestParseError(pathlib.Path(source), f"Invalid TOML syntax: {e}") from e

    # Parse the data into a Manifest object
    try:
        return Manifest.model_validate(data)
    except ValidationError as e:
        raise ManifestParseError(pathlib.Path(source), str(e)) from e
