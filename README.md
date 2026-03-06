# FastSandPM
An RTL Design and DV package manager for python tools. Manage your RTL and
design verification library dependencies by cloning, updating, and
version-controlling git repositories.

[![Tests](https://github.com/RISCY-Lib/fastsandpm/actions/workflows/run-ci-tests.yml/badge.svg)](https://github.com/RISCY-Lib/fastsandpm/actions/workflows/run-ci-tests.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/fastsandpm.svg)](https://pypi.org/project/fastsandpm/)
[![docs](https://readthedocs.org/projects/fastsandpm/badge)](https://fastsandpm.readthedocs.io/en/latest/index.html)

See [Read-The-Docs](https://fastsandpm.readthedocs.io/en/latest/index.html) for details

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

```bash
# For UV Based projects
uv add fastsandpm

# For pip-based projects
pip install fastsandpm
```

### Command Line Usage

The simplest way to use FastSandPM is via the `fspm` command:

```bash
# Install dependencies from proj.toml in current or parent directory
fspm

# Install from a specific manifest file
fspm --manifest /path/to/proj.toml

# Install to a custom output directory
fspm --output ./vendor

# Install with optional dependency groups
fspm --optional dev,test

# Clean conflicting directories during installation
fspm --clean
```

#### CLI Options

| Option | Description |
|--------|-------------|
| `-m, --manifest PATH` | Path to manifest file or directory (default: search up tree for `proj.toml`) |
| `-o, --output PATH` | Output directory for installed libraries (default: `./lib`) |
| `-c, --clean` | Clean conflicting directories during installation |
| `--no-clean` | Don't clean conflicting directories (default) |
| `--optional GROUPS` | Comma-separated list of optional dependency groups |
| `-v, --verbose` | Increase verbosity (can stack: `-v`, `-vv`, `-vvv`) |
| `-q, --quiet` | Suppress all output except errors |
| `-V, --version` | Show version and exit |

### Python API Usage

```python
import pathlib
import fastsandpm

# Load a manifest
manifest = fastsandpm.get_manifest("./my-project")
print(manifest.package.name)
# 'my-package'

# Resolve dependencies
resolved = fastsandpm.dependencies.resolve(manifest)

# Build the library
fastsandpm.build_library(resolved, pathlib.Path("my-library"))
```

This will bring in the library dependencies for a project into the specified directory.
Additionally, a `library.f` file will be created which will point to the dependencies
file list in the required order.

For more examples, see [the docs](https://fastsandpm.readthedocs.io/en/latest/usage_guide/index.html) for details.
