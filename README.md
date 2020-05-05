# SKALE node CLI

[![Build Status](https://travis-ci.com/skalenetwork/skale-node-cli.svg?token=tLesVRTSHvWZxoyqXdoA&branch=develop)](https://travis-ci.com/skalenetwork/skale-node-cli)
[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

SKALE Node CLI, part of the SKALE suite of validator tools, is the command line to setup, register and maintain your SKALE node.

## Table of Contents

1.  [Installation](#installation)
2.  [CLI usage](#cli-usage)  
    2.1 [Top level commands](#top-level-commands)  
    2.2 [User](#user-commands)  
    2.3 [Node](#node-commands)  
    2.4 [Wallet](#wallet-commands)  
    2.5 [sChains](#schain-commands)  
    2.6 [Containers](#containers-commands)  
    2.7 [SGX](#sgx-commands)  
    2.8 [SSL](#ssl-commands)  
    2.9 [Logs](#logs-commands)  
    3.0 [Metrics](#metrics-commands)
3.  [Development](#development)

## Installation

-   Download executable

```bash
VERSION_NUM=0.0.0 && curl -L https://skale-cli.sfo2.cdn.digitaloceanspaces.com/skale-$VERSION_NUM-`uname -s`-`uname -m` > /usr/local/bin/skale
```

With `sudo`:

```bash
VERSION_NUM=0.0.0 && sudo -E bash -c "curl -L https://skale-cli.sfo2.cdn.digitaloceanspaces.com/skale-$VERSION_NUM-`uname -s`-`uname -m` >  /usr/local/bin/skale"
```

-   Apply executable permissions to the binary:

```bash
chmod +x /usr/local/bin/skale
```

-   Test the installation

```bash
skale --help
```

## CLI usage

### Top level commands

#### Info

Print build info

```bash
skale info
```

#### Version

Print version of the `skale-node-cli` tool

```bash
skale version
```

Options:

-   `--short` - prints version only, without additional text.


### Node commands

> Prefix: `skale node`

#### node init

Init SKALE node on current machine

```bash
skale node init
```

Required arguments:

-   `--install-deps` - install docker and other dependencies
-   `--dry-run` - only creates needed files and directories and don't create and containers
-   `--env-file` - path to env file where required parameters listed above are defined

You should also specify the following parameters through environment variables in env-file:

-   `SGX_SERVER_URL` - sgx server url
-   `DISK_MOUNTPOINT` - mount point of the disk to be used for storing sChains data
-   `DOCKER_LVMPY_STREAM` - stream of `docker-lvmpy` to use
-   `DB_PASSWORD` - MySQL password for local node database
-   `DISK_MOUNTPOINT` - Mount point of the disk to be used for storing sChains data
-   `CONTAINER_CONFIGS_STREAM` - stream of `skale-node` to use
-   `IMA_ENDPOINT` - IMA endpoint to connect
-   `ENDPOINT` - RPC endpoint of the node in the network where SKALE manager is deployed
-   `MANAGER_CONTRACTS_ABI_URL` - URL to SKALE Manager contracts ABI and addresses  
-   `IMA_CONTRACTS_ABI_URL` - URL to IMA contracts ABI and addresses  
-   `FILEBEAT_URL` - URL to the Filebeat log server
-   `DB_USER`'  - MySQL user for local node database
-   `DB_PASSWORD` - Password for root user of node internal database
      (equal to user password by default)
-   `DB_PORT` - Port for of node internal database (default is `3306`)

#### Node Register

```bash
skale node register
```

Required arguments:

-   `--ip` - public IP for RPC connections & consensus

Optional arguments:

-   `--name` - SKALE node name
-   `--port` - public port - beginning of the port range for node sChains (default: `10000`)

#### Node info

Get base info about SKALE node

```bash
skale node info
```

Options:

`-f/--format json/text` - optional

#### Node update

Update SKALE node on current machine

```bash
skale node update
```

Options:

-   `--yes` - remove without additional confirmation

You can also specify file with environment variables 
which will update parameters in env file used during skale node init 

-   `--env-file` - path to env file where parameters are defined

### Wallet commands

> Prefix: `skale wallet`

Commands related to Ethereum wallet associated with SKALE node

#### Wallet info

```bash
skale wallet info
```

Options:

`-f/--format json/text` - optional

#### Wallet set

Set local wallet for the SKALE node

```bash
skale wallet set --private-key $ETH_PRIVATE_KEY
```

### sChain commands

> Prefix: `skale schains`

#### sChains list

List of sChains served by connected node

```bash
skale schains ls
```

#### schains config

```bash
skale schains config SCHAIN_NAME
```

#### sChains DKG statuses

DKG statuses for each sChain on the node

```bash
skale schains dkg
```

#### sChains healthchecks

Healthchecks for all sChains on the node

```bash
skale schains checks
```

Options:

- `--json` - Show data in JSON format

### Containers commands

Node container commands

> Prefix: `skale containers`

#### SKALE containers

List of SKALE containers running on connected node

```bash
skale containers ls
```

Options:

-   `-a/--all` - list all containers (by default - only running)

#### sChain containers

List of sChain containers running on connected node

```bash
skale containers schains
```

Options:

-   `-a/--all` - list all sChain containers (by default - only running)

### SGX commands

> Prefix: `skale sgx`

#### Status

Status of the SGX server. Returns SGX server URL and connection status.

```bash
$ skale sgx status

SGX server status:
┌────────────────┬────────────────────────────┐
│ SGX server URL │ https://0.0.0.0:1026/      │
├────────────────┼────────────────────────────┤
│ Status         │ CONNECTED                  │
└────────────────┴────────────────────────────┘
```

Admin API URL: \[GET] `/api/ssl/sgx`

### SSL commands

> Prefix: `skale ssl`

#### SSL Status

Status of the SSL certificates on the node

```bash
skale ssl status
```

Admin API URL: \[GET] `/api/ssl/status`

#### Upload

Upload new SSL certificates

```bash
skale ssl upload
```

##### Options

-   `-c/--cert-path` - Path to the certificate file
-   `-k/--key-path` - Path to the key file
-   `-f/--force` - Overwrite existing certificates

Admin API URL: \[GET] `/api/ssl/upload`

### Logs commands

> Prefix: `skale logs`

#### CLI Logs

Fetch node CLI logs:

```bash
skale logs cli
```

Options:

-   `--debug` - show debug logs; more detailed output

#### Dump Logs

Dump all logs from the connected node:

```bash
skale logs dump [PATH]
```

Optional arguments:

-   `--container`, `-c` - Dump logs only from specified container

### Metrics commands

Shows a list of metrics and bounties for a node

```bash
skale metrics
```
Collecting metrics from the SKALE Manager may take a long time. It is therefore recommended to use optional arguments to limit output by filtering by time period or limiting the number of records to show.

Optional arguments:

-   `--since/-s` - Show requested data since a given date inclusively (e.g. 2020-01-20)
-   `--till/-t` - Show requested data before a given date not inclusively (e.g. 2020-01-21)
-   `--limit/-l` - Number of records to show
-   `--wei/-w` - Show bounty amount in wei

## Development

### Setup repo

#### Install development dependencies

```bash
pip install -e .[dev]
```

##### Add flake8 git hook

In file `.git/hooks/pre-commit` add:

```bash
#!/bin/sh
flake8 .
```

### Debugging

Run commands in dev mode:

```bash
ENV=dev python main.py YOUR_COMMAND
```

### Setting up Travis

Required environment variables:

-   `ACCESS_KEY_ID` - DO Spaces/AWS S3 API Key ID
-   `SECRET_ACCESS_KEY` - DO Spaces/AWS S3 Secret access key
-   `GITHUB_EMAIL` - Email of GitHub user
-   `GITHUB_OAUTH_TOKEN` - GitHub auth token

## Contributing

**If you have any questions please ask our development community on [Discord](https://discord.gg/vvUtWJB).**

[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

## License

[![License](https://img.shields.io/github/license/skalenetwork/skale-node-cli.svg)](LICENSE)

Copyright (C) 2018-present SKALE Labs
