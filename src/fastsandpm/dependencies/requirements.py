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
"""

from __future__ import annotations

import pathlib
from typing import Annotated

from pydantic import (
    BaseModel,
    PlainSerializer,
    PlainValidator,
    WithJsonSchema,
)

from fastsandpm.versioning.specifier import VersionSpecifier, version_specifier_from_str

_Version = Annotated[
    VersionSpecifier,
    PlainValidator(lambda v: version_specifier_from_str(v), json_schema_input_type=str),
    PlainSerializer(lambda v: str(v), return_type=str),
    WithJsonSchema({"type": "string"}),
]


class LibraryRequirement(BaseModel):
    """A base class for a library requirement.
    """

    name: str
    """The name of the library for the requirement"""


class PackageIndexRequirement(LibraryRequirement):
    """A package index based library requirement
    Package Index dependencies are fetched from a package index (e.g., JFrog Artifactory).
    They require a name and version, with an optional registry specification for
    fetching from alternative indecies.

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

    version: _Version
    """The version specifier of the library to use from the package index.

    This can be an exact version (e.g., "1.0.0") or a version range
    (e.g., ">=1.0.0,<2.0.0", "^1.2.3").
    """

    index: str | None = None
    """Optional index name to fetch the dependency from.

    If not specified, the default index is used. The value should
    correspond to a index defined in the [registries] section of
    the manifest.
    """


class GitRequirement(LibraryRequirement):
    """A git-based libary specifier.

    Git libraries are fetched from a git repository. They can be specified
    using a full URL or a project/organization name.

    Example TOML formats:

    .. code-block:: TOML

        [dependencies]
        time = {git = "https://github.com/username/repo.git"}
        dep2 = {git = "SOME_ORG"}

    .. seealso::

        See `Pydantic BaseModel <https://docs.pydantic.dev/latest/api/base_model/>`__
        for details on the parent BaseModel class and it's methods.
    """

    git: str
    """the git url or project id of the dependency package.

    can be a full url (e.g., "https://github.com/username/repo.git")
    or a project/organization name (e.g., "some_org") which will be
    resolved to a git url by searching known git hosts.
    """

    def has_qualified_remote(self) -> bool:
        """Get the git remote URL for this dependency.

        Returns the fully qualified git remote URL. If the git attribute
        is already a URL (contains "://"), it is returned as-is. Otherwise,
        it is treated as a project ID which requires resolution.

        Returns:
            True iff the git attribute is a fully qualified git remote URL.
        """
        if "://" in self.git:
            return True
        return False


class VersionedGitRequirement(GitRequirement):
    """A git-based library specifier with a version tag.

    The version is a version constraint that is matched against tags in the Git Repo

    Example TOML Format:

    .. code-block:: TOML

        [dependency]

        time = {git = "https://github.com/username/repo.git", version = "1.0.0"}
    """

    version: _Version
    """The version specifier of the git library.

    The dependency resolver will look for git tags that
    match the semantic version. Tags must follow semantic versioning
    (optionally prefixed with 'v' or 'V').
    """


class TaggedGitRequirement(GitRequirement):
    """A git-based library specifier with a git tag.

    The tag is used to specify a tag in the git repo that should be used.

    Example TOML Format:

    .. code-block:: TOML

        [dependency]

        time = {git = "https://github.com/username/repo.git", tag = "v1.0.0"}
    """

    tag: str
    """The tag of the git library repo to use.

    The exact tag will be checked out.
    """


class BranchGitRequirement(GitRequirement):
    """A git-based library specifier which point to a specific branch.

    The branch is used to specify which branch of the git repo that should be used.

    Example TOML Format:

    .. code-block:: TOML

        [dependency]

        time = {git = "https://github.com/username/repo.git", branch = "develop"}
    """

    branch: str
    """The branch of the git library repo to use.
    """


class CommitGitRequirement(GitRequirement):
    """A git-based library specifier which points to a specific commit.

    The commit hash will be used exactly.

    Example TOML Format:

    .. code-block:: TOML

        [dependency]

        time = {git = "https://github.com/username/repo.git", commit = "deadbeef"}
    """

    commit: str
    """The commit of the git library to use.
    """


class PathRequirement(LibraryRequirement):
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

    path: pathlib.Path
    """The local path to the dependency.

    This path is relative to the location of the manifest file and
    should point to a directory containing an FastSandPM manifest.
    """


ConcreteGitRequirement = \
    CommitGitRequirement | BranchGitRequirement | TaggedGitRequirement | VersionedGitRequirement | \
    GitRequirement

ConcreteRequirement = PackageIndexRequirement | PathRequirement | ConcreteGitRequirement
