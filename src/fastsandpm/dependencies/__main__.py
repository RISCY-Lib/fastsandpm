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
from __future__ import annotations

from fastsandpm.manifest import Manifest
import pprint

from .provider import resolve

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
            "local": {"path": "./.tmp"}
        }
    }

    pkg_manifest = Manifest.model_validate(definition)
    print(pkg_manifest)
    print("")
    pprint.pprint(resolve(pkg_manifest))
