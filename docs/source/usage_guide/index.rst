Library User Guide
==================

This guide provides information on how to use fastsandpm to manage RTL and
design verification library dependencies.

Installation
------------

To install fastsandpm, use uv:

.. code-block:: bash

   uv add fastsandpm

Or with pip:

.. code-block:: bash

   pip install fastsandpm


Command Line Interface
----------------------

FastSandPM provides the ``fspm`` command for quick dependency management:

.. code-block:: bash

   # Install dependencies from proj.toml
   fspm

   # Install to a custom directory
   fspm --output ./vendor

   # Install with optional dependencies
   fspm --optional dev,test

See :doc:`cli` for the complete CLI reference.

Python API
----------

For programmatic usage, fastsandpm provides a Python API:

.. code-block:: python

   import pathlib
   import fastsandpm

   # Load a manifest
   manifest = fastsandpm.get_manifest("./my-project")

   # Resolve dependencies
   resolved = fastsandpm.dependencies.resolve(manifest)

   # Build the library
   fastsandpm.build_library(resolved, pathlib.Path("lib"))

.. toctree::
   :maxdepth: 2
   :caption: Contents

   cli
