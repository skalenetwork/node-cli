# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- `@local_only` decorator for commands that could be executed only locally
- Ability to reset SKALE node host and clean cookies (`skale host --reset`)

### Changed

- `skale attach` now supports different options (with or without port and schema)


## [0.0.14] - 2019-07-11

### Added

- `skale version` command.
- This CHANGELOG file.

### Fixed

- Passing of `DB_USER` variable for `node init` command.