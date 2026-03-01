.. _version_specifier:

Version Specifiers
====================

Version specifier allow more fine control over what version of a package should be used.
These specifiers use `Semantic Versioning <https://semver.org>`__ to specify versions.


Direct Versions
---------------

If a single version is provided as the version specifier it will be used as-is.

For example the below will require the use of version ``1.0.0`` of the ``time`` package.

.. code-block:: TOML

    [dependencies]
    time = "1.0.0"

Caret Requirements
------------------

**Caret** requirements are a particularly useful versioning strategy.
This strategy allows for the use of any semantic version compatible updates.
They are specified with a version number preceded by a caret (``^``).

``^1.2.3`` is an example for a caret requirement.
It will require the use of version ``1.2.3`` or higher of the package, however will limit the version to below ``2.0.0``.
This guarantees that the package API will be backwards compatible to the version used when specified.


Comparison Requirements and Ranges
----------------------------------

The final method of specifying a version is to use comparison requirements.
These are specified with a version number followed by a comparison operator (``>=``, ``<=``, ``>``, or ``<``).

For example ``>=1.0.0`` is an example of a comparison requirement.
It will require the use of version ``1.0.0`` or higher of the package, however will **not** limit the version to below ``2.0.0``.

Two comparison requirements can be used together to specify a range of versions.
For example ``>=1.0.0,<2.0.0`` is an example of a range of versions.
It will require the use of version ``1.0.0`` or higher of the package, however will limit the version to between ``1.0.0`` and ``2.0.0``.

Pre-Releases
------------

Version requirements other than direct versions exclude pre-releases.
For example ``1.0.0-beta.1`` is an example of a pre-release.
It will require the use of version ``1.0.0-beta.1`` of the package.
But the version range ``>=1.2.3,<2.0.0`` will exlude ``1.3.0-beta.1`` from the version range.
