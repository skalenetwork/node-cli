# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased


### Added 
- Exception handler now logs error stacktrace
- `--endpoint` option for `node init` and `node update` commands
- `skale info` command with information about current build
- `skale logs container` command that fetch logs from one of the node containers

### Changed

- `--git-branch` option for `skale node init` command replaced with `--stream` and it's now required
- `name` and `port` params are no longer required
- build script updates info.py file

## [0.1.1] - 2019-08-06

### Added 

- Logger module
- Logs for most CLI calls
- `skale logs cli` command to fetch CLI logs, `--debug` option for more detailed output

### Changed

- Check disk exist and it's not a partition in `node init` command

### Fixed


## [0.1.0] - 2019-07-31

> Breaking changes, no backward compatibility with 0.0.x releases!

### Added

- Install `convoy` plugin during `node init`
- Creation of the `/skale_node_data` directory during `node init`
- Generation of the `resource_allocation.json` file during `node init`
- Required `--disk-mountpoint` option for `node init`
- Processing and running `systemd` service for `convoy`
- Script for disk preparation (`dm_dev_partition.sh`)
- Other disk allocation stuff
- `--short` option for `user token` command
- `wallet set` command for setting custom local wallet
- Support for 4 nodes test sChains


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