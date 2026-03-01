.. _manifest_file:

The Manifest Format
===================

The `proj.toml` file within a package is called its *manifest* file.
It is generally written i8n the `TOML <https://toml.io>`__ format.
Specifically, it currently supports `TOML v1.0.0 <https://toml.io/en/v1.0.0>`__.
It contains the metadata needed for inclusion of the package into a HDL/RTL project.

Every manifest contains some of the following:

- :ref:`[package] <package_section>`

  - :ref:`name <name_field>` - The name of the package
  - :ref:`version <version_field>` - The version of the package
  - :ref:`description <description_field>` - The description of the package
  - :ref:`authors <authors_field>` - The authors of the package
  - :ref:`readme <readme_field>` - The readme of the package

- :ref:`[dependencies] <dependencies_section>`
- :ref:`[optional_dependencies] <optional_dependencies_section>`
- :ref:`[regsistries] <registries_section>`


.. _package_section:

The ``[package]`` section
--------------------------

The only mandatory section in a manifest is the ``[package]`` section.

.. _name_field:

The ``name`` field
^^^^^^^^^^^^^^^^^^

The package name is a unique identifier used to refer to the package.
It is used when listed as a dependency in other manifests and as the default inferred name for certain other fields.


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


.. _authors_field:

The ``authors`` field
^^^^^^^^^^^^^^^^^^^^^^

The ``authors`` of the package.
This field is optional.
If not specified, it defaults to not including any author information.
This field can either be an array of strings, or an array of dictionaries.

If the ``authors`` field is an array of strings, it is treated as a list.
It is permissible to include the authors email within angled brackets at the end of the authors string.

If the ``authors`` field is an array of dictionaries, it is treated as a list of authors where the valid keys are ``name`` and ``email``.


.. _readme_field:

The ``readme`` field
^^^^^^^^^^^^^^^^^^^^

The ``readme`` field points to the relative location of the ``README`` markdown or text file for the package.
This field is optional.
If not specified, it defaults to not including any readme information.
This field is relative to the location of the manifest file.


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

Once the dpendencies are resolved a filelist will be created.
For ``fastsandpm`` compatible projects these will be included by pointing to the ``filelist`` field of the ``[package]`` section.
Any other project will point to a filelist at the top of the dependency's directory with the same name as the dependency.

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


.. _registries_section:

The ``[registeries]`` section
-----------------------------
