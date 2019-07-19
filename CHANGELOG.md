# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed

- Update `build.sh` script to support `keep` version
- Update info messages
- Check OS during local-only commands (restrict macOS users from running stuff locally)
- Add `--mta-endpoint` option to `node install` and `node update` commands

## [0.0.16] - 2019-07-12

### Added

- `@local_only` decorator for commands that could be executed only locally
- Ability to reset SKALE node host and clean cookies (`skale host --reset`)
- Node update functionality (`skale node update` cmd)

### Changed

- `skale attach` now supports different options (with or without port and schema)
- Documentation updated


## [0.0.14] - 2019-07-11

### Added

- `skale version` command.
- This CHANGELOG file.

### Fixed

- Passing of `DB_USER` variable for `node init` command.