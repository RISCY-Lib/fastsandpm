Command Line Interface
======================

FastSandPM provides the ``fspm`` command-line tool for managing HDL/RTL library
dependencies directly from your terminal.

Basic Usage
-----------

The simplest way to install dependencies is to run ``fspm`` from a directory
containing (or with a parent containing) a ``proj.toml`` manifest file:

.. prompt:: bash

   fspm

This will:

1. Search up the directory tree to find a ``proj.toml`` manifest file
2. Resolve all dependencies specified in the manifest
3. Install them to the ``./lib`` directory
4. Create a ``library.f`` file listing all dependencies in the correct order

Command Reference
-----------------

.. autoprogram:: fastsandpm.cli:create_parser()
   :prog: fspm

Examples
--------

Install from Current Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Search for ``proj.toml`` in the current directory or any parent directory,
then install dependencies to ``./lib``:

.. prompt:: bash

   fspm

Specify a Manifest File
~~~~~~~~~~~~~~~~~~~~~~~

Install dependencies from a specific manifest file:

.. prompt:: bash

   fspm --manifest /path/to/my-project/proj.toml

You can also specify a directory containing a ``proj.toml``:

.. prompt:: bash

   fspm --manifest /path/to/my-project

Custom Output Directory
~~~~~~~~~~~~~~~~~~~~~~~

Install dependencies to a custom directory:

.. prompt:: bash

   fspm --output ./vendor
   fspm -o /absolute/path/to/libs

Install Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install optional dependency groups defined in your manifest:

.. prompt:: bash

   # Install the 'dev' optional group
   fspm --optional dev

   # Install multiple optional groups
   fspm --optional dev,test,simulation

Clean Installation
~~~~~~~~~~~~~~~~~~

By default, ``fspm`` will not overwrite directories that have local changes
or are in an unexpected state. Use the ``--clean`` flag to force replacement:

.. prompt:: bash

   # Clean conflicting directories during installation
   fspm --clean

   # Explicitly disable cleaning (default behavior)
   fspm --no-clean

.. warning::

   The ``--clean`` flag will delete directories with uncommitted changes.
   Make sure to commit or backup any local modifications before using this flag.

Verbose Output
~~~~~~~~~~~~~~

Increase logging verbosity for debugging:

.. prompt:: bash

   # Show INFO level messages
   fspm -v

   # Show DEBUG level messages
   fspm -vv

   # Maximum verbosity
   fspm -vvv

Quiet Mode
~~~~~~~~~~

Suppress all output except errors:

.. prompt:: bash

   fspm --quiet

Version Information
~~~~~~~~~~~~~~~~~~~

Display the installed version:

.. prompt:: bash

   fspm --version

Exit Codes
----------

The ``fspm`` command returns the following exit codes:

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Code
     - Meaning
   * - 0
     - Success - all dependencies installed successfully
   * - 1
     - Error - manifest not found, parse error, or installation failure

Typical Workflow
----------------

A typical workflow for using ``fspm`` in an HDL/RTL project:

1. **Create a manifest file** (``proj.toml``) in your project root:

   .. code-block:: toml

      [package]
      name = "my-rtl-project"
      version = "1.0.0"
      description = "My RTL design project"

      [dependencies]
      uvm = { git = "https://github.com/accellera/uvm.git", tag = "1800.2-2020-2.0" }
      my-lib = "^1.0.0"

      [optional_dependencies.sim]
      vip-axi = "2.0.0"

2. **Install dependencies**:

   .. prompt:: bash

      fspm

3. **Include the library** in your simulation by referencing ``lib/library.f``:

   .. code-block:: bash

      vcs -f lib/library.f -f my_project.f

4. **Update dependencies** after modifying the manifest:

   .. prompt:: bash

      fspm --clean

See Also
--------

- :doc:`index` - General usage guide
- :doc:`../manifest_reference/index` - Manifest file format reference
