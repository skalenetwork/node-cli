# Node CLI

![Build and publish](https://github.com/skalenetwork/node-cli/workflows/Build%20and%20publish/badge.svg)
![Test](https://github.com/skalenetwork/node-cli/workflows/Test/badge.svg)
[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

SKALE Node CLI, part of the SKALE suite of validator tools, is the command line interface to setup, register and maintain your SKALE node. It comes in three distinct build types: Standard (for validator nodes), Passive (for dedicated sChain synchronization), and Fair.

## Table of Contents

1. [Installation](#installation)
   1. [Standard Node Binary](#standard-node-binary)
   2. [Passive Node Binary](#passive-node-binary)
   3. [Fair Node Binary](#fair-node-binary)
   4. [Permissions and Testing](#permissions-and-testing)
2. [Standard Node Usage (`skale` - Normal Build)](#standard-node-usage-skale---normal-build)
   1. [Top level commands (Standard)](#top-level-commands-standard)
   2. [Node commands (Standard)](#node-commands-standard)
   3. [Wallet commands (Standard)](#wallet-commands-standard)
   4. [sChain commands (Standard)](#schain-commands-standard)
   5. [Health commands (Standard)](#health-commands-standard)
   6. [SSL commands (Standard)](#ssl-commands-standard)
   7. [Logs commands (Standard)](#logs-commands-standard)
3. [Passive Node Usage (`skale` - Passive Build)](#passive-node-usage-skale---passive-build)
   1. [Top level commands (Passive)](#top-level-commands-passive)
   2. [Passive node commands](#passive-node-commands)
4. [Fair Node Usage (`fair`)](#fair-node-usage-fair)
   1. [Top level commands (Fair)](#top-level-commands-fair)
   2. [Fair Boot commands](#fair-boot-commands)
   3. [Fair Node commands](#fair-node-commands)
   4. [Fair Chain commands](#fair-chain-commands)
   5. [Fair Wallet commands](#fair-wallet-commands)
   6. [Fair Logs commands](#fair-logs-commands)
   7. [Fair SSL commands](#fair-ssl-commands)
   8. [Fair Staking commands](#fair-staking-commands)
   9. [Passive Fair Node commands](#passive-fair-node-commands)
5. [Exit codes](#exit-codes)
6. [Development](#development)

***

## Installation

### Prerequisites

Ensure that the following packages are installed: **docker**, **docker-compose** (1.27.4+)

### SKALE Node Binary

This binary (`skale-VERSION-OS`) is used for managing SKALE validator nodes.

```shell
# Replace {version} with the desired release version (e.g., 3.0.0)
CLI_VERSION={version} && \
sudo -E bash -c "curl -L https://github.com/skalenetwork/node-cli/releases/download/$CLI_VERSION/skale-$CLI_VERSION-`uname -s`-`uname -m` > /usr/local/bin/skale"
```

### Fair Node Binary

This binary (`skale-VERSION-OS-fair`) is used for managing nodes on the Fair network.

```shell
# Replace {version} with the desired release version (e.g., 3.0.0)
CLI_VERSION={version} && \
sudo -E bash -c "curl -L https://github.com/skalenetwork/node-cli/releases/download/$CLI_VERSION/skale-$CLI_VERSION-`uname -s`-`uname -m`-fair > /usr/local/bin/fair"
```

### Permissions and Testing

Apply executable permissions to the downloaded binary (adjust name accordingly):

```shell
# For Standard or Passive binary
sudo chmod +x /usr/local/bin/skale

# For Fair binary
sudo chmod +x /usr/local/bin/fair
```

Test the installation:

```shell
# Standard or Passive build
skale --help

# Fair build
fair --help
```

***

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

* `--short` - prints version only, without additional text.

### Node commands (Standard)

> Prefix: `skale node`

#### Node information

Get base info about the standard SKALE node.

```shell
skale node info
```

Options:

* `-f/--format json/text` - optional.

#### Node initialization

Initialize a standard SKALE node on the current machine.

> :warning: **Avoid re-initializing a node that’s already initialized**: Run `skale node info` first to confirm the current initialization state.

```shell
skale node init [ENV_FILE]
```

Arguments:

* `ENV_FILE` - path to .env file (required).

Required environment variables in `ENV_FILE`:

* `SGX_SERVER_URL` - SGX server URL.
* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g. /dev/sdc)
* `DOCKER_LVMPY_VERSION` - Version of `docker-lvmpy`.
* `NODE_VERSION` - Version of `skale-node`.
* `ENDPOINT` - RPC endpoint of the network where SKALE Manager is deployed.
* `MANAGER_CONTRACTS` - SKALE Manager `message_proxy_mainnet` contract alias or address.
* `IMA_CONTRACTS` - IMA `skale_manager` contract alias or address.
* `FILEBEAT_HOST` - URL of the Filebeat log server.
* `ENV_TYPE` - Environment type (e.g., 'mainnet', 'testnet', 'qanet', 'devnet').

> In `MANAGER_CONTRACTS` and `IMA_CONTRACTS` fields, if you are using a recognized network (e.g., 'Mainnet', 'Holesky', 'local'), you can use a recognized alias (e.g., 'production', 'grants'). You can check the list of recognized networks and aliases in [contract deployments](https://github.com/skalenetwork/skale-contracts/tree/deployments).
> :warning: If you are using a custom network or a contract which isn't recognized by the underlying `skale-contracts` library, you **MUST** provide a direct contract address.

Optional variables:

* `TG_API_KEY` - Telegram API key
* `TG_CHAT_ID` - Telegram chat ID
* `MONITORING_CONTAINERS` - Enable monitoring containers (`cadvisor`, `node-exporter`).

#### Node initialization from backup

Restore a standard SKALE node on another machine from a backup.

```shell
skale node restore [BACKUP_PATH] [ENV_FILE]
```

Arguments:

* `BACKUP_PATH` - Path to the archive created by `skale node backup`.
* `ENV_FILE` - Path to .env file with configuration for the restored node.

#### Node backup

Generate a backup archive of the standard SKALE node's state.

```shell
skale node backup [BACKUP_FOLDER_PATH]
```

Arguments:

* `BACKUP_FOLDER_PATH` - Path to the folder where the backup file will be saved.

#### Node Registration

Register the standard node with the SKALE Manager contract.

```shell
skale node register --name <NODE_NAME> --ip <PUBLIC_IP> --domain <DOMAIN_NAME> [--port <BASE_PORT>]
```

Required arguments:

* `--ip` - Public IP for RPC connections and consensus.
* `--domain`/`-d` - SKALE node domain name.
* `--name` - SKALE node name.

Optional arguments:

* `--port` - Base port for node sChains (default: `10000`).

#### Node update

Update the standard SKALE node software and configuration.

```shell
skale node update [ENV_FILEPATH] [--yes]
```

Arguments:

* `ENV_FILEPATH` - Path to the .env file containing potentially updated parameters.

Options:

* `--yes` - Update without confirmation prompt.

#### Node turn-off

Turn off the standard SKALE node containers.

```shell
skale node turn-off [--maintenance-on] [--yes]
```

Options:

* `--maintenance-on` - Set node to maintenance mode before turning off.
* `--yes` - Turn off without confirmation.

#### Node turn-on

Turn on the standard SKALE node containers.

```shell
skale node turn-on [ENV_FILEPATH] [--maintenance-off] [--yes]
```

Arguments:

* `ENV_FILEPATH` - Path to the .env file.

Options:

* `--maintenance-off` - Turn off maintenance mode after turning on.
* `--yes` - Turn on without additional confirmation.

#### Node maintenance

Control the node's maintenance status in SKALE Manager.

```shell
# Set maintenance ON
skale node maintenance-on [--yes]

# Set maintenance OFF
skale node maintenance-off
```

Options:

* `--yes` - Perform action without additional confirmation.

#### Domain name

Set the standard node's domain name.

```shell
skale node set-domain --domain <DOMAIN_NAME> [--yes]
```

Required Options:

* `--domain`/`-d` - The new SKALE node domain name.

Options:

* `--yes` - Set without additional confirmation.

#### Skale Node Signature

Get the node signature for a validator ID.

```shell
skale node signature <VALIDATOR_ID>
```

Arguments:

* `VALIDATOR_ID` - The ID of the validator requesting the signature.

### Wallet commands (Standard)

> Prefix: `skale wallet`

Commands related to the Ethereum wallet associated with the standard SKALE node.

#### Wallet information

```shell
skale wallet info [-f json/text]
```

Options:

* `-f/--format json/text` - optional.

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

* `RECEIVER_ADDRESS` - Ethereum receiver address.
* `AMOUNT_ETH` - Amount of ETH tokens to send.

Optional arguments:

* `--yes` - Send without additional confirmation.

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

* `--json` - Show info in JSON format.

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

* `-a/--all` - list all containers (by default - only running).

#### Get sChains healthchecks

Show health check results for all SKALE Chains on the node.

```shell
skale health schains [--json]
```

Options:

* `--json` - Show data in JSON format.

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

* `-c/--cert-path` - Path to the certificate file.
* `-k/--key-path` - Path to the key file.
* `-f/--force` - Overwrite existing certificates.

Admin API URL: `[POST] /api/ssl/upload`

#### Check certificate

Check SSL certificate by connecting to the health-check SSL server.

```shell
skale ssl check [-c <CERT_PATH>] [-k <KEY_PATH>] [--type <TYPE>] [--port <PORT>] [--no-client]
```

Options:

* `-c/--cert-path` - Path to the certificate file (default: uploaded using `skale ssl upload` certificate).
* `-k/--key-path` - Path to the key file (default: uploaded using `skale ssl upload` key).
* `--type/-t` - Check type (`openssl` - openssl cli check, `skaled` - skaled-based check, `all` - both).
* `--port/-p` - Port to start healthcheck server (default: `4536`).
* `--no-client` - Skip client connection (only make sure server started without errors).

### Logs commands (Standard)

> Prefix: `skale logs`

Access logs for the standard node.

#### Fetch CLI Logs

Fetch node CLI logs:

```shell
skale logs cli [--debug]
```

Options:

* `--debug` - show debug logs; more detailed output.

#### Dump All Node Logs

Dump all logs from the connected node:

```shell
skale logs dump [TARGET_PATH] [-c/--container <CONTAINER_NAME>]
```

Arguments:

* `TARGET_PATH` - Optional path to save the log dump archive.

Options:

* `--container`, `-c` - Dump logs only from specified container.

***

## Passive Node Usage (`skale` - Passive Build)

Commands available in the **passive `skale` binary** for managing dedicated Passive nodes.
Note that this binary contains a **different set of commands** compared to the standard build.

### Top level commands (Passive)

#### Info (Passive)

Print build info for the `skale` (passive) binary.

```shell
skale info
```

#### Version (Passive)

Print version number for the `skale` (passive) binary.

```shell
skale version
```

Options:

* `--short` - prints version only, without additional text.

### Passive node commands

> Prefix: `skale passive-node`

#### Passive node initialization

Initialize a dedicated Passive node on the current machine.

```shell
skale passive-node init [ENV_FILE] [--indexer | --archive] [--snapshot] [--snapshot-from <IP>] [--yes]
```

Arguments:

* `ENV_FILE` - path to .env file (required).

Required environment variables in `ENV_FILE`:

* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g. /dev/sdc).
* `DOCKER_LVMPY_VERSION` - Version of `docker-lvmpy`.
* `NODE_VERSION` - Version of `skale-node`.
* `ENDPOINT` - RPC endpoint of the network where SKALE Manager is deployed.
* `MANAGER_CONTRACTS` - SKALE Manager alias or address.
* `IMA_CONTRACTS` - IMA alias or address.
* `SCHAIN_NAME` - Name of the specific SKALE chain to sync.
* `ENV_TYPE` - Environment type (e.g., 'mainnet', 'testnet').

> In `MANAGER_CONTRACTS` and `IMA_CONTRACTS` fields, if you are using a recognized network (e.g., 'Mainnet', 'Holesky', 'local'), you can use a recognized alias (e.g., 'production', 'grants'). You can check the list of recognized networks and aliases in [contract deployments](https://github.com/skalenetwork/skale-contracts/tree/deployments).
> :warning: If you are using a custom network or a contract which isn't recognized by the underlying `skale-contracts` library, you **MUST** provide a direct contract address.

Options:

* `--indexer` - Run in indexer mode (disables block rotation).
* `--archive` - Run in archive mode (enable historic state and disable block rotation).
* `--snapshot` - Start sync node from snapshot.
* `--snapshot-from <IP>` - Specify the IP of another node to download a snapshot from.
* `--yes` - Initialize without additional confirmation.

#### Passive node update

Update the Passive node software and configuration.

```shell
skale passive-node update [ENV_FILEPATH] [--yes]
```

Arguments:

* `ENV_FILEPATH` - Path to the .env file.

Options:

* `--yes` - Update without additionalconfirmation.

> NOTE: You can just update a file with environment variables used during `skale passive-node init`.

#### Passive node cleanup

Remove all data and containers for the Passive node.

```shell
skale passive-node cleanup [--yes]
```

Options:

* `--yes` - Cleanup without confirmation.

> WARNING: This command removes all Passive node data.

***

## Fair Node Usage (`fair`)

Commands available in the **`fair` binary** for managing nodes on the Fair network.

### Top level commands (Fair)

#### Fair Info

Print build info for the `fair` binary.

```shell
fair info
```

#### Fair Version

Print version number for the `fair` binary.

```shell
fair version [--short]
```

Options:

* `--short` - prints version only, without additional text.

### Fair Boot commands

> Prefix: `fair boot`

Commands for a Fair node in the Boot phase.

#### Fair Boot Info

Get information about the Fair node during boot phase.

```shell
fair boot info [--format FORMAT]
```

Options:

* `--format`/`-f` - Output format (`json` or `text`).

#### Fair Boot Initialization

Initialize the Fair node boot phase.

```shell
fair boot init <ENV_FILE>
```

Arguments:

* `ENV_FILE` - Path to the environment file containing configuration.

Required environment variables in `ENV_FILE`:

* `SGX_SERVER_URL` - SGX server URL.
* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g. /dev/sdc).
* `NODE_VERSION` - Version of `skale-node`.
* `ENDPOINT` - RPC endpoint of the network where Fair Manager is deployed.
* `MANAGER_CONTRACTS` - SKALE Manager alias or address.
* `IMA_CONTRACTS` - IMA alias or address (*Note: Required by boot service, may not be used by Fair itself*).
* `FILEBEAT_HOST` - URL/IP:Port of the Filebeat log server.
* `ENV_TYPE` - Environment type (e.g., 'mainnet', 'devnet').

Optional variables:

* `MONITORING_CONTAINERS` - Enable monitoring containers (`cadvisor`, `node-exporter`).

#### Fair Boot Registration

Register the Fair node with Fair Manager *during* the boot phase.

```shell
fair boot register --name <NODE_NAME> --ip <PUBLIC_IP> --domain <DOMAIN_NAME> [--port <BASE_PORT>]
```

Options:

* `--name`/`-n` - Fair node name (required).
* `--ip` - Public IP for RPC connections & consensus (required).
* `--domain`/`-d` - Fair node domain name (e.g., `fair1.example.com`, required).
* `--port`/`-p` - Base port for node sChains (default: from configuration).

#### Fair Boot Signature

Get the node signature for a validator ID during boot phase.

```shell
fair boot signature <VALIDATOR_ID>
```

Arguments:

* `VALIDATOR_ID` - The ID of the validator requesting the signature.

#### Fair Boot Update

Update the Fair node software during boot phase.

```shell
fair boot update <ENV_FILE> [--yes] [--pull-config SCHAIN]
```

Arguments:

* `ENV_FILE` - Path to the environment file for node configuration.

Required environment variables in `ENV_FILE`:

* `SGX_SERVER_URL` - SGX server URL.
* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g. /dev/sdc).
* `NODE_VERSION` - Version of `skale-node`.
* `ENDPOINT` - RPC endpoint of the network where Fair Manager is deployed.
* `MANAGER_CONTRACTS` - SKALE Manager alias or address.
* `IMA_CONTRACTS` - IMA alias or address (*Note: Required by boot service, may not be used by Fair itself*).
* `FILEBEAT_HOST` - URL/IP:Port of the Filebeat log server.
* `ENV_TYPE` - Environment type (e.g., 'mainnet', 'devnet').

Optional variables:

* `MONITORING_CONTAINERS` - Enable monitoring containers (`cadvisor`, `node-exporter`).

Options:

* `--yes` - Update without confirmation prompt.
* `--pull-config` - Pull configuration for specific sChain (hidden option).

### Fair Node commands

> Prefix: `fair node`

Commands for managing a Fair node during its regular operation (main phase).

#### Fair Node Info

Get information about the Fair node.

```shell
fair node info [--format FORMAT]
```

Options:

* `--format`/`-f` - Output format (`json` or `text`).

#### Fair Node Initialization

Initialize the regular operation phase of the Fair node.

```shell
fair node init <ENV_FILEPATH>
```

Arguments:

* `ENV_FILEPATH` - Path to the environment file for node configuration.

Required environment variables in `ENV_FILEPATH`:

* `FAIR_CONTRACTS` - Fair contracts alias or address (e.g., `mainnet`).
* `NODE_VERSION` - Version of `skale-node`.
* `BOOT_ENDPOINT` - RPC endpoint of the Fair network (e.g., `https://rpc.fair.cloud/`).
* `SGX_SERVER_URL` - SGX server URL (e.g., `https://127.0.0.1:1026/`).
* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g., `/dev/sdc`).
* `ENV_TYPE` - Environment type (e.g., `mainnet`).

Optional variables:

* `ENFORCE_BTRFS` - Format existing filesystem on attached disk (`True`/`False`).
* `FILEBEAT_HOST` - URL of the Filebeat log server to send logs.

#### Fair Node Registration

Register the Fair node with the specified IP address.

```shell
fair node register --ip <IP_ADDRESS>
```

Options:

* `--ip` - Public IP address for the Fair node (required).

#### Fair Node Update

Update the Fair node software.

```shell
fair node update <ENV_FILEPATH> [--yes] [--force-skaled-start]
```

Arguments:

* `ENV_FILEPATH` - Path to the environment file for node configuration.

Required environment variables in `ENV_FILEPATH`:

* `FAIR_CONTRACTS` - Fair contracts alias or address (e.g., `mainnet`).
* `NODE_VERSION` - Version of `skale-node`.
* `BOOT_ENDPOINT` - RPC endpoint of the Fair network (e.g., `https://rpc.fair.cloud/`).
* `SGX_SERVER_URL` - SGX server URL (e.g., `https://127.0.0.1:1026/`).
* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g., `/dev/sdc`).
* `ENV_TYPE` - Environment type (e.g., `mainnet`).

Optional variables:

* `ENFORCE_BTRFS` - Format existing filesystem on attached disk (`True`/`False`).
* `FILEBEAT_HOST` - URL of the Filebeat log server to send logs.

Options:

* `--yes` - Update without confirmation prompt.
* `--force-skaled-start` - Force skaled container to start (hidden option).

#### Fair Node turn-off

Turn off the Fair node containers.

```shell
fair node turn-off [--yes]
```

Options:

* `--yes` - Turn off without confirmation.

#### Fair Node turn-on

Turn on the Fair node containers.

```shell
fair node turn-on [ENV_FILEPATH] [--yes]
```

Arguments:

* `ENV_FILEPATH` - Path to the .env file.

Options:

* `--yes` - Turn on without additional confirmation.

#### Fair Node Migrate

Switch from boot phase to regular Fair node operation.

```shell
fair node migrate <ENV_FILEPATH> [--yes]
```

Arguments:

* `ENV_FILEPATH` - Path to the environment file for node configuration.

Required environment variables in `ENV_FILEPATH`:

* `FAIR_CONTRACTS` - Fair contracts alias or address (e.g., `mainnet`).
* `NODE_VERSION` - Version of `skale-node`.
* `BOOT_ENDPOINT` - RPC endpoint of the Fair network (e.g., `https://rpc.fair.cloud/`).
* `SGX_SERVER_URL` - SGX server URL (e.g., `https://127.0.0.1:1026/`).
* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g., `/dev/sdc`).
* `ENV_TYPE` - Environment type (e.g., `mainnet`).

Optional variables:

* `ENFORCE_BTRFS` - Format existing filesystem on attached disk (`True`/`False`).
* `FILEBEAT_HOST` - URL of the Filebeat log server to send logs.

Options:

* `--yes` - Migrate without confirmation prompt.

#### Fair Node Repair

Toggle fair chain repair mode.

```shell
fair node repair [--snapshot-from SOURCE] [--yes]
```

Options:

* `--snapshot-from` - Source for snapshots (`any` by default, hidden option).
* `--yes` - Proceed without confirmation prompt.

#### Fair Node Backup

Generate a backup archive of the Fair node's state.

```shell
fair node backup <BACKUP_FOLDER_PATH>
```

Arguments:

* `BACKUP_FOLDER_PATH` - Path to the folder where the backup file will be saved.

#### Fair Node Restore

Restore a Fair node from a backup archive.

```shell
fair node restore <BACKUP_PATH> <ENV_FILE> [--config-only]
```

Arguments:

* `BACKUP_PATH` - Path to the backup archive.
* `ENV_FILE` - Path to the .env file for the restored node configuration.

Options:

* `--config-only` - Only restore configuration files.

#### Fair Node Cleanup

Cleanup Fair node data and configuration.

```shell
fair node cleanup [--yes]
```

Options:

* `--yes` - Cleanup without confirmation prompt.

#### Fair Node Change IP

Change the IP address of the Fair node.

```shell
fair node change-ip <IP_ADDRESS>
```

Arguments:

* `IP_ADDRESS` - New public IP address for the Fair node.

### Fair Chain commands

> Prefix: `fair chain`

Commands for managing and monitoring the Fair chain state and configuration.

#### Fair Chain Record

Get information about the Fair chain record, including chain name, configuration status, DKG status, and operational metadata.

```shell
fair chain record [--json]
```

Options:

* `--json` - Output in JSON format instead of formatted table.

#### Fair Chain Checks

Get the status of Fair chain checks, including configuration checks and skaled checks.

```shell
fair chain checks [--json]
```

Options:

* `--json` - Output in JSON format instead of formatted table.

### Fair Wallet commands

> Prefix: `fair wallet`

Commands for managing the node wallet.

#### Fair Wallet Info

Get information about the SKALE node wallet.

```shell
fair wallet info [--format FORMAT]
```

Options:

* `--format`/`-f` - Output format (`json` or `text`).

#### Fair Wallet Send

Send ETH from SKALE node wallet to an address.

```shell
fair wallet send <ADDRESS> <AMOUNT> [--yes]
```

Arguments:

* `ADDRESS` - Destination address for ETH transfer.
* `AMOUNT` - Amount of ETH to send (as float).

Options:

* `--yes` - Send without confirmation prompt.

### Fair Logs commands

> Prefix: `fair logs`

Commands for managing and accessing node logs.

#### Fair CLI Logs

Fetch the logs of the node-cli.

```shell
fair logs cli [--debug]
```

Options:

* `--debug` - Show debug logs instead of regular logs.

#### Fair Logs Dump

Dump all logs from the connected node.

```shell
fair logs dump <PATH> [--container CONTAINER]
```

Arguments:

* `PATH` - Path where the logs dump will be saved.

Options:

* `--container`/`-c` - Dump logs only from specified container.

### Fair SSL commands

> Prefix: `fair ssl`

Commands for managing SSL certificates for sChains.

#### Fair SSL Status

Check the status of SSL certificates on the node.

```shell
fair ssl status
```

#### Fair SSL Upload

Upload SSL certificate files to the node.

```shell
fair ssl upload --cert-path <CERT_PATH> --key-path <KEY_PATH> [--force]
```

Options:

* `--cert-path`/`-c` - Path to the SSL certificate file (required).
* `--key-path`/`-k` - Path to the SSL private key file (required).
* `--force`/`-f` - Overwrite existing certificates.

#### Fair SSL Check

Check SSL certificate validity and connectivity.

```shell
fair ssl check [--cert-path CERT_PATH] [--key-path KEY_PATH] [--port PORT] [--type TYPE] [--no-client] [--no-wss]
```

Options:

* `--cert-path`/`-c` - Path to the certificate file (default: system default).
* `--key-path`/`-k` - Path to the key file (default: system default).
* `--port`/`-p` - Port to start SSL health check server (default: from configuration).
* `--type`/`-t` - Check type: `all`, `openssl`, or `skaled` (default: `all`).
* `--no-client` - Skip client connection for openssl check.
* `--no-wss` - Skip WSS server starting for skaled check.

### Fair Staking commands

> Prefix: `fair staking`

Commands for interacting with the Fair staking functionality.

#### Add allowed receiver

Allow an address to receive staking fees.

```shell
fair staking add-receiver <RECEIVER_ADDRESS>
```

Arguments:

* `RECEIVER_ADDRESS` - Address to add to the allowed receivers list.

#### Remove allowed receiver

Remove an address from the allowed receivers list.

```shell
fair staking remove-receiver <RECEIVER_ADDRESS>
```

Arguments:

* `RECEIVER_ADDRESS` - Address to remove from the allowed receivers list.

Workflow (fees): request fees -> review exit requests -> claim request.

#### Request fees

Create a request to claim a specific amount of earned fees (FAIR). Use `--all` to request all.

```shell
fair staking request-fees <AMOUNT>
fair staking request-fees --all
```

#### Request send fees

Create a request to send a specific amount (or all) of earned fees to an address.

```shell
fair staking request-send-fees <TO_ADDRESS> <AMOUNT>
fair staking request-send-fees <TO_ADDRESS> --all
```

Arguments:

* `TO_ADDRESS` - Destination address for the fee transfer.
* `AMOUNT` - Amount of fees to include in the request (FAIR).

#### Claim request

Claim a previously created request by its request ID once it is unlocked.

```shell
fair staking claim-request <REQUEST_ID>
```

#### Get exit requests

List exit (fee withdrawal) requests for the current wallet. Use `--json` for raw JSON output.

```shell
fair staking exit-requests
fair staking exit-requests --json
```

Default output (non-JSON) shows: `request_id`, `user`, `node_id`, `amount_wei`, `amount_fair`, `unlock_date (ISO)`.

#### Get earned fee amount

Get the currently earned (unrequested) fee amount.

```shell
fair staking earned-fee-amount
```

#### Set fee rate

Set the fee rate (uint16 value) used by the staking logic.

```shell
fair staking set-fee-rate <FEE_RATE>
```

Arguments:

* `FEE_RATE` - Fee rate value as integer (uint16).

### Passive Fair Node commands

> Prefix: `fair passive-node` (passive Fair build)

Commands for operating a passive Fair node (sync/indexer/archive).

#### Passive Fair Node Initialization

Initialize a passive Fair node.

```shell
fair passive-node init <ENV_FILEPATH> --id <NODE_ID> [--indexer | --archive] [--snapshot <URL|any>]
```

Arguments:

* `ENV_FILEPATH` - Path to the environment file with configuration.

Required environment variables in `ENV_FILEPATH`:

* `FAIR_CONTRACTS` - Fair Manager contracts alias or address.
* `NODE_VERSION` - Version of `skale-node`.
* `BOOT_ENDPOINT` - RPC endpoint of Fair network.
* `BLOCK_DEVICE` - Absolute path to a dedicated raw block device (e.g., `/dev/sdc`).
* `ENV_TYPE` - Environment type (e.g., `mainnet`, `devnet`).

Options:

* `--id` - Numerical node identifier (required).
* `--indexer` - Run in indexer mode (no block rotation).
* `--archive` - Run in archive mode (historical state kept; disables block rotation). Mutually exclusive with `--indexer`.
* `--snapshot <URL|any>` - Start from provided snapshot URL or from any available source (not allowed together with `--indexer` or `--archive`).

By default runs a regular sync node.

#### Passive Fair Node Update

Update software / configs for passive Fair node.

```shell
fair passive-node update <ENV_FILEPATH> [--yes]
```

#### Passive Fair Node turn-off

Turn off the Fair passive node containers.

```shell
fair passive-node turn-off [--yes]
```

Options:

* `--yes` - Turn off without confirmation.

#### Passive Fair Node turn-on

Turn on the Fair passive node containers.

```shell
fair passive-node turn-on [ENV_FILEPATH] [--yes]
```

Arguments:

* `ENV_FILEPATH` - Path to the .env file.

Options:

* `--yes` - Turn on without additional confirmation.

#### Passive Fair Node Cleanup

Remove all passive Fair node data and containers.

```shell
fair passive-node cleanup [--yes]
```

Options:

* `--yes` - Proceed without confirmation.

***

## Exit codes

Exit codes conventions for SKALE CLI tools

* `0` - Everything is OK
* `1` - General error exit code
* `3` - Bad API response\*\*
* `4` - Script execution error\*\*
* `5` - Transaction error\*
* `6` - Revert error\*
* `7` - Bad user error\*\*
* `8` - Node state error\*\*

`*` - `validator-cli` only\
`**` - `node-cli` only

***

## Development

### Setup repo

#### Dependencies

* Python 3.11
* Git

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

Specify the build type (`normal`, `passive`, or `fair`):

```shell
# Example for Standard build
./scripts/generate_info.sh 1.0.0 my-branch normal

# Example for Passive build
./scripts/generate_info.sh 1.0.0 my-branch passive

# Example for Fair build
./scripts/generate_info.sh 1.0.0 my-branch fair
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
