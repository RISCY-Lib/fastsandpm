.. _specifying_dependencies:

Specifying Dependencies
=======================

Dependency specifiers control how a dependency is found and brought in.
There are currently the following supported specifiers:

- :ref:`package index <package_index_specifier>`
- :ref:`git <git_specifier>`
- :ref:`path <path_specifier>`

.. _package_index_specifier:

Package Index Specifier
-----------------------

.. warning::

   The ``package index`` specifier is not yet supported as there is not an existing index to use.


The ``package index`` specifier is the easiest specifier.
Only a name and version string are required.
Using these two pieces of information the dependency will be fetched from the ``package index``.
For example you can specify a dependency named ``time`` and version ``1.0.0`` as follows:

.. code-block:: TOML

    [dependencies]
    time = "1.0.0"

The version string is a known as a :ref:`version specifier <version_specifier>`.
These specifiers can be used to set a range of valid versions used for resolving dependencies.


Dependencies from Other Registries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is also possible to point to a different index using the ``index`` key in the dependency.
For example you can specify a dependency named ``time`` and version ``1.0.0`` from a custom registry as follows:

.. code-block:: TOML

    [dependencies]
    time = {index = "my-registry", version = "1.0.0"}

The value of ``index`` points to a registry definition from the ``[registries]`` section of the manifest.
See the :ref:`registries section documentation <registries_section>` for more information.


.. _git_specifier:

Git Specifier
-------------

The ``git`` specifier allows you to use a git repository as a dependency.
It allows you to specify the entire url to a git repository to use or the project/org name.
Minimally you just need to include the ``git`` key in the dependency:

.. code-block:: TOML

    [dependencies]
    time = {git = "https://github.com/username/repo.git"}
    dep2 = {git = "SOME_ORG"}

In the first case ``time`` will be fetched from the ``https://github.com/username/repo.git`` repository.
In the second case ``dep2`` will be fetched from the by looking in the following locations in order to find a valid git remote:

- ``https://bitbucket.itg.ti.com/projects/SOME_ORG/dep2.git``
- ``https://github.com/SOME_ORG/dep2.git``

If no corresponding repository can be found an error will be raised.

By default the upstream default branch will be used.

.. note::

   If when the dependencies are updated the existing local copy is dirty an error will be raised.
   A user of the library can force the update by setting the ``force_update`` flag to ``true`` or ignore the error by setting ``ignore_dirty`` to ``true``.


Git Commit & Tag Specifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the user needs more control than fetching the latest remote head they can also specify the commit or tag to use:

.. code-block:: TOML

    [dependencies]
    time = {git = "https://github.com/username/repo.git", commit = "deadbeef"}

    [dependencies]
    time = {git = "https://github.com/username/repo.git", tag = "v1.0.0"}

This will cause ``fastsandpm`` to use the commit ``deadbeef`` instead of the latest remote head.

Git Branch Specifiers
^^^^^^^^^^^^^^^^^^^^^^

However, a sometimes an exact commit is not necessary.
In these cases the user can specify the branch to use:

.. code-block:: TOML

    [dependencies]
    time = {git = "https://github.com/username/repo.git", branch = "some_branch"}

Git Version Specifiers
^^^^^^^^^^^^^^^^^^^^^^

If the git repository uses tags which follow it's semantic versioning then the user can specify the version to use:

.. code-block:: TOML

    [dependencies]
    time = {git = "https://github.com/username/repo.git", version = "1.0.0"}

This :ref:`version specifier <version_specifier>` will be used to resolve the dependency by looking at the tags for a matching version.
The tags of the repo must be a valid semantic versioning specification. A 'v' or 'V' may also be used as a prefix for the version string.
If the tags of the repo do not properly follow the semantic version spec it the tool may be unable to find a corresponding version.

.. _path_specifier:

Path Specifiers
---------------

Path dependecy specifiers allow a user to specify a local path (usually under the current project) to treat as a dependecy.
This path should contain a ``fastsandpm`` manifest.

.. code-block:: TOML

    [dependencies]
    time = {path = "./some/path/to/dep1"}
