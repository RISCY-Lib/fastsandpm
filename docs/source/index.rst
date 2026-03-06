.. fastsandpm documentation master file

fastsandpm Documentation

===========================================

An RTL Design and DV package manager for python tools. Manage your RTL and
design verification library dependencies by cloning, updating, and
version-controlling git repositories.

Key Features
------------

- **Library Management**: Clone and update RTL/DV libraries from git repositories
- **Version Pinning**: Pin libraries to specific tags, branches, or commits
- **Version Ranges**: Specify flexible version constraints (e.g., ``>=1.0.0,<2.0.0``)
- **TOML Configuration**: Organize libraries in configuration files with sub-headings
- **Local Development**: Symlink local directories for development workflows
- **Multi-Remote Support**: Automatically discover repositories across configured remotes

Quick Start
-----------

Installation:

.. code-block:: bash

   # For UV Based projects
   uv add fastsandpm

   # For pip-based projects
   pip install fastsandpm

Command Line Usage:

The simplest way to use FastSandPM is via the ``fspm`` command:

.. code-block:: bash

   # Install dependencies from proj.toml in current or parent directory
   fspm

   # Install to a custom directory
   fspm --output ./vendor

   # Install with optional dependency groups
   fspm --optional dev,test

See :doc:`usage_guide/cli` for the complete CLI reference.

Python API Usage:

    >>> import pathlib
    >>> import fastsandpm
    >>> manifest = fastsandpm.get_manifest("./my-project")
    >>> print(manifest.package.name)
    'my-package'
    >>> resolved = fastsandpm.dependencies.resolve(manifest)
    >>> print(type(resolved))
    <class 'dict'>
    >>> fastsandpm.build_library(resolved, pathlib.Path("my-library"))

This will bring in the library dependencies for a project into the specified directory.
Additionally, a ``library.f`` file will be created which will point to the dependencies
file list in the required order.

For more examples, see the :doc:`usage_guide/index`.


User Information
----------------

:doc:`manifest_reference/index`

    How the manifest is to be structured.

:doc:`usage_guide/index`

    How to use ``fastsandpm`` in a different python project.

Developer Information
-----------------------

:doc:`CONTRIBUTING`

    Guide for contributing to ``fastsandpm``

:doc:`CHANGELOG`

    List of changes made to ``fastsandpm``


.. Hidden TOCs

.. toctree::
    :maxdepth: 2
    :caption: User Documentation
    :hidden:

    manifest_reference/index
    usage_guide/index

.. toctree::
    :maxdepth: 2
    :caption: Developer Documentation
    :hidden:

    CONTRIBUTING.md
    CHANGELOG.md

API
----

.. autosummary::
   :toctree: api
   :caption: API
   :template: module-template.rst
   :recursive:

   fastsandpm

