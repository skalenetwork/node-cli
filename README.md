# Node CLI

![Build and publish](https://github.com/skalenetwork/node-cli/workflows/Build%20and%20publish/badge.svg)
![Test](https://github.com/skalenetwork/node-cli/workflows/Test/badge.svg)
[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

SKALE Node CLI, part of the SKALE suite of validator tools, is the command line interface to setup, register and maintain your SKALE node. It comes in three distinct build types: Standard (for validator nodes), Sync (for dedicated sChain synchronization), and Mirage (for the Mirage network).

## Table of Contents

1. [Installation](#installation)
   1. [Standard Node Binary](#standard-node-binary)
   2. [Sync Node Binary](#sync-node-binary)
   3. [Mirage Node Binary](#mirage-node-binary)
   4. [Permissions and Testing](#permissions-and-testing)
2. [Standard Node Usage (`skale` - Normal Build)](#standard-node-usage-skale---normal-build)
   1. [Top level commands (Standard)](#top-level-commands-standard)
   2. [Node commands (Standard)](#node-commands-standard)
   3. [Wallet commands (Standard)](#wallet-commands-standard)
   4. [sChain commands (Standard)](#schain-commands-standard)
   5. [Health commands (Standard)](#health-commands-standard)
   6. [SSL commands (Standard)](#ssl-commands-standard)
   7. [Logs commands (Standard)](#logs-commands-standard)
   8. [Resources allocation commands (Standard)](#resources-allocation-commands-standard)
3. [Sync Node Usage (`skale` - Sync Build)](#sync-node-usage-skale---sync-build)
   1. [Top level commands (Sync)](#top-level-commands-sync)
   2. [Sync node commands](#sync-node-commands)
4. [Mirage Node Usage (`mirage`)](#mirage-node-usage-mirage)
   1. [Top level commands (Mirage)](#top-level-commands-mirage)
   2. [Mirage Boot commands](#mirage-boot-commands)
   3. [Mirage Node commands](#mirage-node-commands)
5. [Exit codes](#exit-codes)
6. [Development](#development)

---

## Installation

### Prerequisites

Ensure that the following packages are installed: **docker**, **docker-compose** (1.27.4+)

### Standard Node Binary

This binary (`skale-VERSION-OS`) is used for managing standard SKALE validator nodes.

```shell
# Replace {version} with the desired release version (e.g., 2.6.0)
VERSION_NUM={version} && \
sudo -E bash -c "curl -L https://github.com/skalenetwork/node-cli/releases/download/$VERSION_NUM/skale-$VERSION_NUM-`uname -s`-`uname -m` > /usr/local/bin/skale"
```

### Sync Node Binary

This binary (`skale-VERSION-OS-sync`) is used for managing dedicated Sync nodes. **Ensure you download the correct `-sync` suffixed binary for Sync node operations.**

```shell
# Replace {version} with the desired release version (e.g., 2.6.0)
VERSION_NUM={version} && \
sudo -E bash -c "curl -L https://github.com/skalenetwork/node-cli/releases/download/$VERSION_NUM/skale-$VERSION_NUM-`uname -s`-`uname -m`-sync > /usr/local/bin/skale"
```

### Mirage Node Binary

This binary (`skale-VERSION-OS-mirage`) is used specifically for managing nodes on the Mirage network. It is named `mirage`.

```shell
# Replace {version} with the desired release version (e.g., 2.6.0)
VERSION_NUM={version} && \
sudo -E bash -c "curl -L https://github.com/skalenetwork/node-cli/releases/download/$VERSION_NUM/skale-$VERSION_NUM-`uname -s`-`uname -m`-mirage > /usr/local/bin/mirage"
```

### Permissions and Testing

Apply executable permissions to the downloaded binary (adjust name accordingly):

```shell
# For Standard or Sync binary
sudo chmod +x /usr/local/bin/skale

# For Mirage binary
sudo chmod +x /usr/local/bin/mirage
```

Test the installation:

```shell
# Standard or Sync build
skale --help

# Mirage build
mirage --help
```

---

## Standard Node Usage (`skale` - Normal Build)

Commands available in the **standard `skale` binary** for managing nodes.

### Top level commands (Standard)

#### Info

Print build info for the `skale` (normal) binary.

```shell
skale info
```

#### Version

Print version number for the `skale` (normal) binary.

```shell
skale version
```

Options:

- `--short` - prints version only, without additional text.

### Node commands (Standard)

> Prefix: `skale node`

#### Node information

Get base info about the standard SKALE node.

```shell
skale node info
```

Options:

- `-f/--format json/text` - optional.

#### Node initialization

Initialize a standard SKALE node on the current machine.

> :warning: **Avoid re-initializing a node that’s already initialized**: Run `skale node info` first to confirm the current initialization state.

```shell
skale node init [ENV_FILE]
```

Arguments:

- `ENV_FILE` - path to .env file (required).

Required environment variables in `ENV_FILE`:

- `SGX_SERVER_URL` - SGX server URL.
- `DISK_MOUNTPOINT` - Mount point for storing sChains data.
- `DOCKER_LVMPY_STREAM` - Stream of `docker-lvmpy` to use.
- `CONTAINER_CONFIGS_STREAM` - Stream of `skale-node` to use.
- `ENDPOINT` - RPC endpoint of the network where SKALE Manager is deployed.
- `MANAGER_CONTRACTS` - SKALE Manager `message_proxy_mainnet` contract alias or address.
- `IMA_CONTRACTS` - IMA `skale_manager` contract alias or address.
- `FILEBEAT_HOST` - URL of the Filebeat log server.
- `ENV_TYPE` - Environment type (e.g., 'mainnet', 'testnet', 'qanet', 'devnet').

> In `MANAGER_CONTRACTS` and `IMA_CONTRACTS` fields, if you are using a recognized network (e.g., 'Mainnet', 'Holesky', 'local'), you can use a recognized alias (e.g., 'production', 'grants'). You can check the list of recognized networks and aliases in [contract deployments](https://github.com/skalenetwork/skale-contracts/tree/deployments).
> :warning: If you are using a custom network or a contract which isn't recognized by the underlying `skale-contracts` library, you **MUST** provide a direct contract address.

Optional variables:

- `TG_API_KEY` - Telegram API key
- `TG_CHAT_ID` - Telegram chat ID
- `MONITORING_CONTAINERS` - Enable monitoring containers (`cadvisor`, `node-exporter`).

#### Node initialization from backup

Restore a standard SKALE node on another machine from a backup.

```shell
skale node restore [BACKUP_PATH] [ENV_FILE]
```

Arguments:

- `BACKUP_PATH` - Path to the archive created by `skale node backup`.
- `ENV_FILE` - Path to .env file with configuration for the restored node.

#### Node backup

Generate a backup archive of the standard SKALE node's state.

```shell
skale node backup [BACKUP_FOLDER_PATH]
```

Arguments:

- `BACKUP_FOLDER_PATH` - Path to the folder where the backup file will be saved.

#### Node Registration

Register the standard node with the SKALE Manager contract.

```shell
skale node register --name <NODE_NAME> --ip <PUBLIC_IP> --domain <DOMAIN_NAME> [--port <BASE_PORT>]
```

Required arguments:

- `--ip` - Public IP for RPC connections and consensus.
- `--domain`/`-d` - SKALE node domain name.
- `--name` - SKALE node name.

Optional arguments:

- `--port` - Base port for node sChains (default: `10000`).

#### Node update

Update the standard SKALE node software and configuration.

```shell
skale node update [ENV_FILEPATH] [--yes]
```

Arguments:

- `ENV_FILEPATH` - Path to the .env file containing potentially updated parameters.

Options:

- `--yes` - Update without confirmation prompt.

#### Node turn-off

Turn off the standard SKALE node containers.

```shell
skale node turn-off [--maintenance-on] [--yes]
```

Options:

- `--maintenance-on` - Set node to maintenance mode before turning off.
- `--yes` - Turn off without confirmation.

#### Node turn-on

Turn on the standard SKALE node containers.

```shell
skale node turn-on [ENV_FILEPATH] [--maintenance-off] [--yes]
```

Arguments:

- `ENV_FILEPATH` - Path to the .env file.

Options:

- `--maintenance-off` - Turn off maintenance mode after turning on.
- `--yes` - Turn on without additional confirmation.

#### Node maintenance

Control the node's maintenance status in SKALE Manager.

```shell
# Set maintenance ON
skale node maintenance-on [--yes]

# Set maintenance OFF
skale node maintenance-off
```

Options:

- `--yes` - Perform action without additional confirmation.

#### Domain name

Set the standard node's domain name.

```shell
skale node set-domain --domain <DOMAIN_NAME> [--yes]
```

Required Options:

- `--domain`/`-d` - The new SKALE node domain name.

Options:

- `--yes` - Set without additional confirmation.

#### Skale Node Signature

Get the node signature for a validator ID.

```shell
skale node signature <VALIDATOR_ID>
```

Arguments:

- `VALIDATOR_ID` - The ID of the validator requesting the signature.

### Wallet commands (Standard)

> Prefix: `skale wallet`

Commands related to the Ethereum wallet associated with the standard SKALE node.

#### Wallet information

```shell
skale wallet info [-f json/text]
```

Options:

- `-f/--format json/text` - optional.

#### Wallet setting

Set the local wallet private key for the node.

```shell
skale wallet set --private-key $ETH_PRIVATE_KEY
```

#### Send ETH tokens

Send ETH from the node's wallet.

```shell
skale wallet send <RECEIVER_ADDRESS> <AMOUNT_ETH> [--yes]
```

Arguments:

- `RECEIVER_ADDRESS` - Ethereum receiver address.
- `AMOUNT_ETH` - Amount of ETH tokens to send.

Optional arguments:

- `--yes` - Send without additional confirmation.

### sChain commands (Standard)

> Prefix: `skale schains`

Commands for interacting with sChains managed by the standard node.

#### List sChains

List of SKALE Chains served by connected node.

```shell
skale schains ls
```

#### Get sChain config

Show the configuration for a specific SKALE Chain.

```shell
skale schains config <SCHAIN_NAME>
```

#### Get DKG status

List DKG status for each SKALE Chain on the node.

```shell
skale schains dkg
```

#### Get sChain info

Show information about a specific SKALE Chain on the node.

```shell
skale schains info <SCHAIN_NAME> [--json]
```

Options:

- `--json` - Show info in JSON format.

#### Repair sChain

Turn on repair mode for a specific SKALE Chain.

```shell
skale schains repair <SCHAIN_NAME>
```

### Health commands (Standard)

> Prefix: `skale health`

Commands to check the health of the standard node and its components.

#### List containers

List all SKALE containers running on the connected node.

```shell
skale health containers [-a/--all]
```

Options:

- `-a/--all` - list all containers (by default - only running).

#### Get sChains healthchecks

Show health check results for all SKALE Chains on the node.

```shell
skale health schains [--json]
```

Options:

- `--json` - Show data in JSON format.

#### Check SGX server status

Status of the SGX server. Returns the SGX server URL and connection status.

```shell
skale health sgx
```

### SSL commands (Standard)

> Prefix: `skale ssl`

Manage SSL certificates for the standard node.

#### Check SSL Status

Status of the SSL certificates on the node.

```shell
skale ssl status
```

Admin API URL: `[GET] /api/ssl/status`

#### Upload certificates

Upload new SSL certificates.

```shell
skale ssl upload -c <CERT_PATH> -k <KEY_PATH> [-f/--force]
```

Options:

- `-c/--cert-path` - Path to the certificate file.
- `-k/--key-path` - Path to the key file.
- `-f/--force` - Overwrite existing certificates.

Admin API URL: `[POST] /api/ssl/upload`

#### Check certificate

Check SSL certificate by connecting to the health-check SSL server.

```shell
skale ssl check [-c <CERT_PATH>] [-k <KEY_PATH>] [--type <TYPE>] [--port <PORT>] [--no-client]
```

Options:

- `-c/--cert-path` - Path to the certificate file (default: uploaded using `skale ssl upload` certificate).
- `-k/--key-path` - Path to the key file (default: uploaded using `skale ssl upload` key).
- `--type/-t` - Check type (`openssl` - openssl cli check, `skaled` - skaled-based check, `all` - both).
- `--port/-p` - Port to start healthcheck server (default: `4536`).
- `--no-client` - Skip client connection (only make sure server started without errors).

### Logs commands (Standard)

> Prefix: `skale logs`

Access logs for the standard node.

#### Fetch CLI Logs

Fetch node CLI logs:

```shell
skale logs cli [--debug]
```

Options:

- `--debug` - show debug logs; more detailed output.

#### Dump All Node Logs

Dump all logs from the connected node:

```shell
skale logs dump [TARGET_PATH] [-c/--container <CONTAINER_NAME>]
```

Arguments:

- `TARGET_PATH` - Optional path to save the log dump archive.

Options:

- `--container`, `-c` - Dump logs only from specified container.

### Resources allocation commands (Standard)

> Prefix: `skale resources-allocation`

Manage the resources allocation file for the standard node.

#### Show allocation file

Show resources allocation file:

```shell
skale resources-allocation show
```

#### Generate/update allocation file

Generate/update allocation file:

```shell
skale resources-allocation generate [ENV_FILE] [--yes] [-f/--force]
```

Arguments:

- `ENV_FILE` - path to .env file (required parameters are listed in the `skale node init` command).

Options:

- `--yes` - generate without additional confirmation.
- `-f/--force` - rewrite allocation file if it exists.

---

## Sync Node Usage (`skale` - Sync Build)

Commands available in the **sync `skale` binary** for managing dedicated Sync nodes.
Note that this binary contains a **different set of commands** compared to the standard build.

### Top level commands (Sync)

#### Info (Sync)

Print build info for the `skale` (sync) binary.

```shell
skale info
```

#### Version (Sync)

Print version number for the `skale` (sync) binary.

```shell
skale version
```

Options:

- `--short` - prints version only, without additional text.

### Sync node commands

> Prefix: `skale sync-node`

#### Sync node initialization

Initialize a dedicated Sync node on the current machine.

```shell
skale sync-node init [ENV_FILE] [--indexer | --archive] [--snapshot] [--snapshot-from <IP>] [--yes]
```

Arguments:

- `ENV_FILE` - path to .env file (required).

Required environment variables in `ENV_FILE`:

- `DISK_MOUNTPOINT` - Mount point for storing sChain data.
- `DOCKER_LVMPY_STREAM` - Stream of `docker-lvmpy`.
- `CONTAINER_CONFIGS_STREAM` - Stream of `skale-node`.
- `ENDPOINT` - RPC endpoint of the network where SKALE Manager is deployed.
- `MANAGER_CONTRACTS` - SKALE Manager alias or address.
- `IMA_CONTRACTS` - IMA alias or address.
- `SCHAIN_NAME` - Name of the specific SKALE chain to sync.
- `ENV_TYPE` - Environment type (e.g., 'mainnet', 'testnet').

> In `MANAGER_CONTRACTS` and `IMA_CONTRACTS` fields, if you are using a recognized network (e.g., 'Mainnet', 'Holesky', 'local'), you can use a recognized alias (e.g., 'production', 'grants'). You can check the list of recognized networks and aliases in [contract deployments](https://github.com/skalenetwork/skale-contracts/tree/deployments).
> :warning: If you are using a custom network or a contract which isn't recognized by the underlying `skale-contracts` library, you **MUST** provide a direct contract address.

Options:

- `--indexer` - Run in indexer mode (disables block rotation).
- `--archive` - Run in archive mode (enable historic state and disable block rotation).
- `--snapshot` - Start sync node from snapshot.
- `--snapshot-from <IP>` - Specify the IP of another node to download a snapshot from.
- `--yes` - Initialize without additional confirmation.

#### Sync node update

Update the Sync node software and configuration.

```shell
skale sync-node update [ENV_FILEPATH] [--yes]
```

Arguments:

- `ENV_FILEPATH` - Path to the .env file.

Options:

- `--yes` - Update without additionalconfirmation.

> NOTE: You can just update a file with environment variables used during `skale sync-node init`.

#### Sync node cleanup

Remove all data and containers for the Sync node.

```shell
skale sync-node cleanup [--yes]
```

Options:

- `--yes` - Cleanup without confirmation.

> WARNING: This command removes all Sync node data.

---

## Mirage Node Usage (`mirage`)

Commands available in the **`mirage` binary** for managing nodes on the Mirage network.

### Top level commands (Mirage)

#### Mirage Info

Print build info for the `mirage` binary.

```shell
mirage info
```

#### Mirage Version

Print version number for the `mirage` binary.

```shell
mirage version [--short]
```

Options:

- `--short` - prints version only, without additional text.

### Mirage Boot commands

> Prefix: `mirage boot`

Commands for a Mirage node in the Boot phase.

#### Mirage Boot Initialization

Initialize the Mirage node boot phase.

```shell
mirage boot init [ENV_FILE]
```

Arguments:

- `ENV_FILE` - path to .env file (required).

Required environment variables in `ENV_FILE`:

- `SGX_SERVER_URL` - SGX server URL.
- `DISK_MOUNTPOINT` - Mount point for storing data (BTRFS recommended).
- `CONTAINER_CONFIGS_STREAM` - Stream of `skale-node` configs.
- `ENDPOINT` - RPC endpoint of the network where Mirage Manager is deployed.
- `MANAGER_CONTRACTS` - SKALE Manager alias or address.
- `IMA_CONTRACTS` - IMA alias or address (_Note: Required by boot service, may not be used by Mirage itself_).
- `FILEBEAT_HOST` - URL/IP:Port of the Filebeat log server.
- `ENV_TYPE` - Environment type (e.g., 'mainnet', 'devnet').

Optional variables:

- `MONITORING_CONTAINERS` - Enable monitoring containers (`cadvisor`, `node-exporter`).

#### Mirage Boot Registration

Register the Mirage node with Mirage Manager _during_ the boot phase.

```shell
mirage boot register --name <NODE_NAME> --ip <PUBLIC_IP> --domain <DOMAIN_NAME> [--port <BASE_PORT>]
```

Required arguments:

- `--name`/`-n` - Mirage node name.
- `--ip` - Public IP for RPC connections and consensus.
- `--domain`/`-d` - Mirage node domain name (e.g., `mirage1.example.com`).

Optional arguments:

- `--port`/`-p` - Base port for node sChains (default: `10000`).

#### Mirage Boot Signature

Get the node signature for a validator ID _during_ the boot phase.

```shell
mirage boot signature <VALIDATOR_ID>
```

Arguments:

- `VALIDATOR_ID` - The ID of the validator requesting the signature.

#### Mirage Boot Migrate

Migrate the Mirage node from the boot phase to the main phase (regular operation).

```shell
mirage boot migrate [ENV_FILEPATH] [--yes]
```

Arguments:

- `ENV_FILEPATH` - Path to the .env file.

Options:

- `--yes` - Migrate without confirmation.

### Mirage Node commands

> Prefix: `mirage node`

Commands for managing a Mirage node during its regular operation (main phase).

#### Mirage Node Initialization (Placeholder)

Initialize the regular operation phase of the Mirage node.

```shell
mirage node init
```

> **Note:** This command is currently a placeholder and not implemented.

#### Mirage Node Registration (Placeholder)

Register the node during regular operation.

```shell
mirage node register
```

> **Note:** This command is currently a placeholder and not implemented.

#### Mirage Node Update (Placeholder)

Update the Mirage node during regular operation.

```shell
mirage node update [ENV_FILEPATH] [--yes] [--unsafe]
```

> **Note:** This command is currently a placeholder and not implemented.

#### Mirage Node Signature

Get the node signature for a validator ID during regular operation.

```shell
mirage node signature <VALIDATOR_ID>
```

Arguments:

- `VALIDATOR_ID` - The ID of the validator requesting the signature.

#### Mirage Node Backup

Generate a backup archive of the Mirage node's state.

```shell
mirage node backup <BACKUP_FOLDER_PATH>
```

Arguments:

- `BACKUP_FOLDER_PATH` - Path to the folder where the backup file will be saved.

#### Mirage Node Restore

Restore a Mirage node from a backup archive.

```shell
mirage node restore <BACKUP_PATH> <ENV_FILE> [--config-only]
```

Arguments:

- `BACKUP_PATH` - Path to the archive.
- `ENV_FILE` - Path to the .env file for the restored node configuration.

Options:

- `--config-only` - Only restore configuration files.

---

## Exit codes

Exit codes conventions for SKALE CLI tools

- `0` - Everything is OK
- `1` - General error exit code
- `3` - Bad API response\*\*
- `4` - Script execution error\*\*
- `5` - Transaction error\*
- `6` - Revert error\*
- `7` - Bad user error\*\*
- `8` - Node state error\*\*

`*` - `validator-cli` only\
`**` - `node-cli` only

---

## Development

### Setup repo

#### Dependencies

- Python 3.11
- Git

#### Clone the repository

Clone with HTTPS:

```shell
git clone https://github.com/skalenetwork/node-cli.git
```

Or with SSH:

```shell
git clone git@github.com:skalenetwork/node-cli.git
```

#### Create and source virtual environment

```shell
python3.11 -m venv venv
source venv/bin/activate
```

#### Install development dependencies

```shell
pip install -e ".[dev]"
```

#### Generate info.py locally

Specify the build type (`normal`, `sync`, or `mirage`):

```shell
# Example for Standard build
./scripts/generate_info.sh 1.0.0 my-branch normal

# Example for Sync build
./scripts/generate_info.sh 1.0.0 my-branch sync

# Example for Mirage build
./scripts/generate_info.sh 1.0.0 my-branch mirage
```

#### Add linting git hook

In file `.git/hooks/pre-commit` add:

```shell
#!/bin/sh
./venv/bin/ruff check .
```

> **Note:** This hook assumes your virtual environment is named 'venv' and is located at the root of the repository.

Make the hook executable:

```shell
chmod +x .git/hooks/pre-commit
```

## Contributing

**If you have any questions please ask our development community on [Discord](https://discord.gg/vvUtWJB).**

[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

## License

[![License](https://img.shields.io/github/license/skalenetwork/node-cli.svg)](LICENSE)

Copyright (C) 2018-present SKALE Labs
