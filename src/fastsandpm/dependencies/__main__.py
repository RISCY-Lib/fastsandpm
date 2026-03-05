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
"""CLI entry point for the dependencies module.

This module provides a demonstration of the dependency resolution functionality.
It can be run directly with `python -m fastsandpm.dependencies` to resolve
dependencies for a sample manifest.

Example:
    To run the dependency resolution demo::

        $ python -m fastsandpm.dependencies

Note:
    This module is primarily intended for development and testing purposes.
    For production use, import the resolve function from the provider module.
"""

from __future__ import annotations

import pprint

from fastsandpm.dependencies.provider import resolve
from fastsandpm.manifest import Manifest

if __name__ == "__main__":
    definition = {
        "package": {
            "name": "demo",
            "version": "1.0.0",
            "description": "",
        },
        "dependencies": {
            "ahb_agent": {"git": "RISCY-Lib", "version": "0.1.0"},
            "apb_agent": {"git": "https://github.com/RISCY-Lib/apb_agent", "branch": "test_branch"},
            "local": {"path": "./.tmp"},
        },
    }

    try:
        import os

        import certifi  # type: ignore[import-not-found]

        os.environ["SSL_CERT_FILE"] = certifi.where()
    except ImportError:
        pass

    pkg_manifest = Manifest.model_validate(definition)
    pprint.pprint(pkg_manifest)
    print("")
    pprint.pprint(resolve(pkg_manifest))
