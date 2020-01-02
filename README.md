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
    2.6 [SSL](#ssl-commands)  
    2.7 [Logs](#logs-commands)  
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

#### Host

Print current SKALE node host

```bash
skale host
```

Options:

- `--reset` - Reset SKALE node host and remove saved cookies

#### Attach

Attach `skale-node-cli` to the remote node

```bash
skale attach $REMOTE_NODE_URL
```

Possible `REMOTE_NODE_URL` formats:

-   `http://NODE_IP:NODE_PORT`
-   `NODE_IP:NODE_PORT` - default schema is `http://`
-   `NODE_IP` - default port is `3007`

### User commands

#### Token

Show user registration token

> Local-only

```bash
skale user token
```

#### Register

Interactive:

```bash
skale user register
```

Non-interactive:

```bash
skale user register -u/--username USERNAME -p/--password PASSWORD -t/--token TOKEN
```

#### Login

Interactive:

```bash
skale user login
```

Non-interactive:

```bash
skale user login -u/--username user -p/--password pass
```

#### Logout

```bash
skale user logout
```

### Node commands

> Prefix: `skale node`

#### node init

Init SKALE node on current machine

> Local-only

```bash
skale node init
```

Required arguments(available through prompt):

-   `--disk-mountpoint` - mount point of the disk to be used for storing sChains data

You should also specify the following options through environment variables or .env file:

-   `GITHUB_TOKEN` - token for accessing `skale-node` repo
-   `DOCKER_USERNAME` - username for DockerHub
-   `DOCKER_PASSWORD` - password for DockerHub
-   `DB_PASSWORD` - MySQL password for local node database
-   `DISK_MOUNTPOINT` - Mount point of the disk to be used for storing sChains data
-   `GITHUB_TOKEN` - token for accessing `skale-node` repo 
-   `GIT_BRANCH` - stream of `skale-node` to use
-   `IMA_ENDPOINT` - IMA endpoint to connect
-   `ENDPOINT` - RPC endpoint of the node in the network where SKALE manager is deployed
- `MANAGER_URL` - URL to SKALE Manager contracts ABI and addresses  
- `IMA_URL` - URL to IMA contracts ABI and addresses  
- `FILEBEAT_URL` - URL to the Filebeat log server
- `DB_USER`'  - MySQL user for local node database - _optional_
- `DB_PASSWORD` - Password for root user of node internal database
    (equal to user password by default) - _optional_   
- `DB_PORT` - Port for of node internal database (default is `3306`) - _optional_


#### Node Register

Register SKALE node on SKALE Manager contracts

-   Login required

```bash
skale node register
```

Required arguments:

-   `--ip` - public IP for RPC connections & consensus

Optional arguments:

-   `--name` - SKALE node name
-   `--port` - base port for node sChains (default: `10000`)

#### Node info

Get base info about SKALE node

-  Login required

```bash
skale node info
```

Options:

`-f/--format json/text` - optional

#### Node purge

Remove SKALE node software from the machine.

> Local-only

```bash
skale node purge
```

Options:

-   `--yes` - remove without additional confirmation

#### Node update

Update SKALE node on current machine

> Local-only

```bash
skale node update
```

Options:

-   `--yes` - remove without additional confirmation

You should specify the following options through environment variables or .env file:

-   `GITHUB_TOKEN` - token for accessing `skale-node` repo
-   `DOCKER_USERNAME` - username for DockerHub
-   `DOCKER_PASSWORD` - password for DockerHub
-   `DB_PASSWORD` - MySQL password for local node database
-   `DISK_MOUNTPOINT` - Mount point of the disk to be used for storing sChains data
-   `GIT_BRANCH` - stream of `skale-node` to use
-   `IMA_ENDPOINT` - IMA endpoint to connect
-   `ENDPOINT` - RPC endpoint of the node in the network where SKALE manager is deployed
- `MANAGER_URL` - URL to SKALE Manager contracts ABI and addresses  
- `IMA_URL` - URL to IMA contracts ABI and addresses  
- `FILEBEAT_URL` - URL to the Filebeat log server
- `DB_USER`'  - MySQL user for local node database - _optional_
- `DB_PASSWORD` - Password for root user of node internal database
    (equal to user password by default) - _optional_   
- `DB_PORT` - Port for of node internal database (default is `3306`) - _optional_

### Wallet commands

> Prefix: `skale wallet`

Commands related to Ethereum wallet associated with SKALE node

#### Wallet info

-   Login required

```bash
skale wallet info
```

Options:

`-f/--format json/text` - optional

#### Wallet set

Set local wallet for the SKALE node

-   Login required
-   Local only
-   No node ony

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

### Containers commands

Node containers commands

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

- `-a/--all` - list all sChain containers (by default - only running)

### SSL commands

> Prefix: `skale ssl`

#### Status

Status of the SSL certificates on the node

```bash
skale ssl status
```

Admin API URL: [GET] `/api/ssl/status`

#### Upload

Upload new SSL certificates

```bash
skale ssl upload
```

##### Options

- `-c/--cert-path` - Path to the certificate file
- `-k/--key-path` - Path to the key file
- `-f/--force` - Overwrite existing certificates

Admin API URL: [GET] `/api/ssl/upload`

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

### Validator commands (not implemented yet)

> Prefix: `skale validator`

#### validator list

```bash
skale validator list
```

## Development

### Setup repo

#### Install development dependencies

```bash
pip install -r requirements-dev.txt
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
