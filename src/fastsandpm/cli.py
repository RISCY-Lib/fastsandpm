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
"""Command-line interface for FastSandPM.

This module provides the main entry point for the ``fspm`` command-line tool.
It handles dependency resolution and installation for HDL/RTL projects.

Usage::

    fspm [OPTIONS]

Options:

- ``-m, --manifest PATH``: Path to manifest file (default: search up directory tree)
- ``-o, --output PATH``: Output directory for installed libraries (default: ./lib)
- ``-c, --clean``: Clean conflicting directories during installation
- ``--no-clean``: Don't clean conflicting directories (default)
- ``--optional GROUPS``: Comma-separated list of optional dependency groups to install

Example::

    # Install dependencies from proj.toml in current or parent directory
    fspm

    # Install from a specific manifest file
    fspm --manifest /path/to/proj.toml

    # Install to a custom output directory
    fspm --output ./vendor

    # Install with optional dependencies
    fspm --optional dev,test

    # Clean conflicting directories
    fspm --clean
"""

from __future__ import annotations

import argparse
import logging
import pathlib
import sys

from fastsandpm._info import __version__
from fastsandpm.install import library_from_manifest
from fastsandpm.manifest import (
    MANIFEST_FILENAME,
    ManifestNotFoundError,
    ManifestParseError,
    get_manifest,
)


def find_manifest(start_path: pathlib.Path | None = None) -> pathlib.Path:
    """Search up the directory tree to find a manifest file.

    Starting from the given path (or current working directory if not provided),
    searches up through parent directories until a proj.toml file is found.

    Args:
        start_path: The directory to start searching from. Defaults to cwd.

    Returns:
        The path to the directory containing the manifest file.

    Raises:
        ManifestNotFoundError: If no manifest file is found in any parent directory.
    """
    if start_path is None:
        start_path = pathlib.Path.cwd()

    current = start_path.resolve()

    # Search up the directory tree
    while True:
        manifest_path = current / MANIFEST_FILENAME
        if manifest_path.exists() and manifest_path.is_file():
            return current

        # Move to parent directory
        parent = current.parent
        if parent == current:
            # Reached root without finding manifest
            raise ManifestNotFoundError(start_path)

        current = parent


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the fspm CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="fspm",
        description="FastSandPM - Package manager for HDL Design and DV projects",
        epilog="For more information, visit https://fastsandpm.readthedocs.io/",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-m",
        "--manifest",
        type=pathlib.Path,
        metavar="PATH",
        help="Path to manifest file or directory containing it "
        f"(default: search up directory tree for {MANIFEST_FILENAME})",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("lib"),
        metavar="PATH",
        help="Output directory for installed libraries (default: ./lib)",
    )

    # Use mutually exclusive group for clean flags
    clean_group = parser.add_mutually_exclusive_group()
    clean_group.add_argument(
        "-c",
        "--clean",
        action="store_true",
        dest="clean",
        help="Clean conflicting directories during installation",
    )
    clean_group.add_argument(
        "--no-clean",
        action="store_false",
        dest="clean",
        help="Don't clean conflicting directories (default)",
    )
    parser.set_defaults(clean=False)

    parser.add_argument(
        "--optional",
        type=str,
        metavar="GROUPS",
        help="Comma-separated list of optional dependency groups to install",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times: -v, -vv, -vvv)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )

    return parser


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments to parse. Defaults to sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = create_parser()
    try:
        import argcomplete  # type: ignore
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    return parser.parse_args(args)


def setup_logging(verbose: int, quiet: bool) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG).
        quiet: If True, only show ERROR level messages.
    """
    if quiet:
        level = logging.ERROR
    elif verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def main(args: list[str] | None = None) -> int:
    """Main entry point for the fspm CLI.

    Args:
        args: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parsed_args = parse_args(args)
    setup_logging(parsed_args.verbose, parsed_args.quiet)

    logger = logging.getLogger(__name__)

    # Find or resolve manifest path
    try:
        if parsed_args.manifest is not None:
            manifest_path = parsed_args.manifest.resolve()
            # If user provided a file path, use its parent directory
            if manifest_path.is_file():
                manifest_path = manifest_path.parent
        else:
            # Search up the directory tree for manifest
            manifest_path = find_manifest()
            logger.info("Found manifest at %s", manifest_path / MANIFEST_FILENAME)
    except ManifestNotFoundError as e:
        logger.error(
            "No %s found in current directory or any parent directory. "
            "Use --manifest to specify a path.",
            MANIFEST_FILENAME,
        )
        logger.debug("Search started from: %s", e.path)
        return 1

    # Load and parse the manifest
    try:
        manifest = get_manifest(manifest_path)
        logger.info(
            "Loaded manifest for %s version %s",
            manifest.package.name,
            manifest.package.version,
        )
    except ManifestNotFoundError:
        logger.error("Manifest file not found at %s", manifest_path / MANIFEST_FILENAME)
        return 1
    except ManifestParseError as e:
        logger.error("Failed to parse manifest: %s", e.reason)
        return 1

    # Parse optional dependencies
    optional_deps: list[str] | None = None
    if parsed_args.optional:
        optional_deps = [g.strip() for g in parsed_args.optional.split(",") if g.strip()]
        logger.info("Including optional dependency groups: %s", ", ".join(optional_deps))

    # Resolve output path
    output_path = parsed_args.output.resolve()
    logger.info("Installing dependencies to %s", output_path)

    # Install dependencies
    try:
        library_from_manifest(
            manifest=manifest,
            dest=output_path,
            optional_deps=optional_deps,
            clean=parsed_args.clean,
        )
        logger.info("Successfully installed dependencies")
    except NotImplementedError as e:
        logger.error("%s", e)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
