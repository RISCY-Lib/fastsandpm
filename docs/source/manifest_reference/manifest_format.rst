.. _manifest_file:

The Manifest Format
===================

The `proj.toml` file within a package is called its *manifest* file.
It is generally written in the `TOML <https://toml.io>`__ format.
Specifically, it currently supports `TOML v1.0.0 <https://toml.io/en/v1.0.0>`__.
It contains the metadata needed for inclusion of the package into a HDL/RTL project.

Every manifest contains some of the following:

- :ref:`[package] <package_section>`

  - :ref:`name <name_field>` - The name of the package
  - :ref:`version <version_field>` - The version of the package
  - :ref:`description <description_field>` - (Optional) The description of the package
  - :ref:`authors <authors_field>` - (Optional) The authors of the package
  - :ref:`readme <readme_field>` - The readme of the package
  - :ref:`flist <flist_field>` - The file list of the package

- :ref:`[dependencies] <dependencies_section>`
- :ref:`[optional_dependencies] <optional_dependencies_section>`
- :ref:`[registries] <registries_section>`


.. _package_section:

The ``[package]`` section
--------------------------

The only mandatory section in a manifest is the ``[package]`` section.

.. _name_field:

The ``name`` field
^^^^^^^^^^^^^^^^^^

The package name is a unique identifier used to refer to the package.
It is used when listed as a dependency in other manifests and as the default inferred name for certain other fields.

The name field is required and must be a non-empty string.
Empty strings and whitespace-only strings are not allowed and will result in a validation error.


.. _version_field:

The ``version`` field
^^^^^^^^^^^^^^^^^^^^^

The ``version`` of the package.
It must be formatted in accordance with `SemVar <https://semver.org/>`__.
The ``version`` does not support build-metadata.


.. _description_field:

The ``description`` field
^^^^^^^^^^^^^^^^^^^^^^^^^

The ``description`` is a short summary of the package.
This field is treated as a plain-text string.

This field is optional.
If not specified, it defaults to an empty string.
However, providing a description is strongly recommended as it helps users understand the purpose and functionality of the package.

Example TOML with description:

.. code-block:: TOML

    [package]
    name = "my-package"
    version = "1.0.0"
    description = "A package for HDL design and verification"

Example TOML without description (uses default empty string):

.. code-block:: TOML

    [package]
    name = "my-package"
    version = "1.0.0"


.. _authors_field:

The ``authors`` field
^^^^^^^^^^^^^^^^^^^^^^

The ``authors`` field specifies the authors of the package.
This field is optional. If not specified, no author information is included.

The ``authors`` field accepts several formats:

**Single string** (with optional email in angle brackets):

.. code-block:: TOML

     [package]
     authors = "John Doe"

     # Or with email:
     authors = "John Doe <john.doe@example.com>"

**List of strings**:

.. code-block:: TOML

     [package]
     authors = [
         "John Doe <john.doe@example.com>",
         "Jane Smith <jane.smith@example.com>"
     ]

**Dictionary with name and email**:

.. code-block:: TOML

     [package]
     authors = {name = "John Doe", email = "john.doe@example.com"}

     # Email is optional:
     authors = {name = "John Doe"}

Choose the format that best suits your needs. For multiple authors, the list format is most readable.


.. _readme_field:

The ``readme`` field
^^^^^^^^^^^^^^^^^^^^

The ``readme`` field points to the relative location of the ``README`` markdown or text file for the package.
This field is optional.
If not specified, it defaults to not including any readme information.
This field is relative to the location of the manifest file.


.. _flist_field:

The ``flist`` field
^^^^^^^^^^^^^^^^^^^

The ``flist`` field points to the relative location of the file list for the package.
A file list contains the paths to all source files that should be included when this package is used as a dependency in another project.

This field is optional.
If not specified, it defaults to ``<package-name>.f`` in the same directory as the manifest file.
For example, if the package name is ``my-package``, the default file list would be ``my-package.f``.
This field is relative to the location of the manifest file.

Example TOML with explicit file list:

.. code-block:: TOML

    [package]
    name = "my-package"
    version = "1.0.0"
    description = "A sample package"
    flist = "rtl/sources.f"

Example TOML using the default file list (``my-package.f``):

.. code-block:: TOML

    [package]
    name = "my-package"
    version = "1.0.0"
    description = "A sample package"

When a ``fastsandpm`` compatible package is used as a dependency, the specified file list is automatically included in the dependent project.
For projects that do not specify an ``flist`` field, FastSandPM will look for a file named ``<package-name>.f`` at the root of the dependency directory.


.. _dependencies_section:

The ``[dependencies]`` section
------------------------------

The ``fastsandpm`` manifest format supports specifying dependencies in the ``[dependencies]`` and ``[optional_dependencies]`` sections.
These the ``[dependencies]`` section and the ``[optional_dependencies]`` section are optional.

These sections can point at ``git`` repositories, registries (similar to ``pypi``), or local directories.
It is also possible to temporarily override the location of a dependency, which can be useful to test out a bug fix in the dependency.

The dependencies section contains a group of :ref:`dependency specifiers <specifying_dependencies>`.
These are always brought in to the project.
Additionally, if these point to projects with a ``fastsandpm`` manifest, their dependencies will also be brought in.

Once the dependencies are resolved a file list will be created.
For ``fastsandpm`` compatible projects, the file list is automatically included by pointing to the :ref:`flist <flist_field>` field of the ``[package]`` section.
Any other project will use a file list located at the top of the dependency's directory with the same name as the dependency.

For example:

.. code-block:: TOML

    [dependencies]

    uvm_utils = "^1.0.0"
    std_cells = ">0.1.0"
    amba_interfaces = {git = "PADC_AMBA_IP", branch = "main"}
    local_utils = {path = "./local_utils"}


.. _optional_dependencies_section:

The ``[optional_dependencies]`` section
----------------------------------------

In addition to the main dependencies it may be necessary to specify alternative dependencies for specific use cases.
These can be specified in the ``[optional_dependencies]`` section.

For example:

.. code-block:: TOML

     [optional_dependencies]

     uvm = [
         {name="uvm_utils", version="^1.0.0"},
         {name="improved_uvm_ral", version=">0.1.0", git="DCC_UVM"},
     ]

The above creates a UVM dependency group that contains the ``uvm_utils`` and ``improved_uvm_ral`` packages.

An alternative but equally valid way to write this TOML would be:

.. code-block:: TOML

     [optional_dependencies.uvm]

     uvm_utils = "^1.0.0"
     improved_uvm_ral = {version=">0.1.0", git="DCC_UVM"}


Format Equivalence
^^^^^^^^^^^^^^^^^^

The two formats shown above are completely equivalent. Both create the same dependency group structure.
Choose the format that is most readable for your use case:

- **List format** (``[optional_dependencies]`` with array): Better when copying dependency specifications or when dependencies have complex configurations
- **Table format** (``[optional_dependencies.group]``): More concise and readable for simple version specifications

The following two specifications are identical:

.. code-block:: TOML

     # List format
     [optional_dependencies]
     dev = [
         {name = "pytest", version = "^7.0.0"},
         {name = "mypy", version = "^1.0.0"}
     ]

.. code-block:: TOML

     # Table format (recommended for simple cases)
     [optional_dependencies.dev]
     pytest = "^7.0.0"
     mypy = "^1.0.0"

Choose whichever format makes your manifest more readable and maintainable for your project's needs.


.. _registries_section:

The ``[registries]`` section
-----------------------------

Additional registries can be specified in the ``[registries]`` section.
A registry type exists for each :ref:`dependency specifier <specifying_dependencies>` type.

The ``[registries]`` section manages custom registries used to locate and fetch dependencies.
FastSandPM supports three types of registries: Git registries, Package Index registries, and Path registries.
Default registries (GitHub, GitLab, Bitbucket, and a local path registry) are automatically added if not explicitly provided.


Git Registries
^^^^^^^^^^^^^^

Git registries are used to resolve dependencies from git hosts such as GitHub, GitLab, or custom Git servers.

A Git registry consists of the unique registry name and then the url to the remote root.
The remote is specified as a url in a inline TOML table.

Example TOML with custom Git registry:

.. code-block:: TOML

    [registries]
    internal-git = {remote = "https://git.company.com"}

Once defined, the registry can be referenced in dependency specifications:

.. code-block:: TOML

    [dependencies]
    my-lib = {git = "my-org"}  # Uses internal-git registry if https://git.company.com/my-org/my-lib exists
    other-lib = {git = "my-org/"}


Package Index Registries
^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::

    Package Index registries are not yet fully supported. All methods currently raise ``NotImplementedError`` as this feature is still under development.

Package Index registries are used to resolve dependencies from package indices similar to PyPI or JFrog Artifactory.

A package index registry consists of the unique registry name and then the url index to the index.
The index is specified as a url in a inline TOML table.

Example TOML with Package Index registry:

.. code-block:: TOML

    [registries]

    artifactory = {index = "https://artifactory.company.com/artifactory/api/pypi/pypi"}

Once defined, the registry can be referenced in dependency specifications:

.. code-block:: TOML

    [dependencies]
    my-lib = {index = "artifactory", version = "1.0.0"}


Path Registries
^^^^^^^^^^^^^^^

Path registries are used to resolve dependencies from local filesystem paths.
This is useful for monorepo setups or local development where dependencies are checked out locally.

A path registry consists of the unique registry name and then the path to the local repository.
The path is specified as a relative path from the current project in a inline TOML table.

Example TOML with Path registry:

.. code-block:: TOML

    [registries]
    local-deps = {path = "./local_dependencies"}

Once defined, the registry can be used in dependency specifications:

.. code-block:: TOML

    [dependencies]
    local-util = {path = "./util"}  # Uses local-deps registry


Complete Registry Example
^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a complete example showing all three registry types in use:

.. code-block:: TOML

    [package]
    name = "my-project"
    version = "1.0.0"

    [registries]
    # Internal Git registry
    internal-git = {remote = "https://git.company.com"}

    # Monorepo registry
    local-deps = {path = "./monorepo/libraries"}

    # Package Index registry (for future use)
    artifactory = {index = "https://artifactory.company.com/api/pypi"}

    [dependencies]
    # From GitHub (default registry)
    public-lib = {git = "github-org"}

    # From internal Git server (can match to https://git.company.com/internal-org/internal-lib.git)
    internal-lib = {git = "internal-org"}

    # From local path (can match to ./monorepo/libraries/util)
    local-util = {path = "./util"}

Default Registries
^^^^^^^^^^^^^^^^^^^

FastSandPM automatically adds the following default registries:

- **github**: ``https://github.com``
- **gitlab**: ``https://gitlab.com``
- **bitbucket**: ``https://bitbucket.org``
- **local_path**: ``.`` (current directory)

To use a default registry, simply reference it by name in your dependency specifications.
For example, to fetch from GitHub:

.. code-block:: TOML

    [dependencies]
    my-lib = {git = "my-org/my-lib"}  # Resolved via the default GitHub registry


