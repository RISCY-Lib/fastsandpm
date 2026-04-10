Changelog
====================================================================================================

All notable changes to ``FastSandPM`` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

0.2.0
----------------------------------------------------------------------

### Fixed
- Path dependencies are now resolved to absolute paths relative to the manifest file's directory
  when loading via `get_manifest()`. Previously, relative paths were left as-is which could cause
  issues when the working directory differed from the manifest location.

0.1.0
----------------------------------------------------------------------

### Added
- Initial creation of API
- Initial spec for manifest defintion
- Initial creation of CLI tool
