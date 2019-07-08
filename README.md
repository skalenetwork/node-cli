# SKALE node CLI

SKALE Node CLI, part of the SKALE suite of validator tools, is the command line to setup, register and maintain your SKALE node.

## Table of Contents
1. [Installation](#installation)
2. [CLI usage](#cli-usage)  
    2.1 [Top level commands](#top-level-commands)  
    2.2 [User](#user-commands)   
    2.3 [Node](#node-commands)  
    2.4 [Wallet](#wallet-commands)  
    2.5 [sChains](#schain-commands)  
    2.6 [Containers](#containers-commands)  
    2.7 [Logs](#logs-commands)  
3. [Development](#development)



## Installation

- Download executable
```bash
VERSION_NUM=0.0.0 && curl -L https://skale-cli.sfo2.cdn.digitaloceanspaces.com/skale-$VERSION_NUM-`uname -s`-`uname -m` > /usr/local/bin/skale
```

With `sudo`:

```bash
VERSION_NUM=0.0.0 && sudo -E bash -c "curl -L https://skale-cli.sfo2.cdn.digitaloceanspaces.com/skale-$VERSION_NUM-`uname -s`-`uname -m` >  /usr/local/bin/skale"
```

- Apply executable permissions to the binary:

```bash
chmod +x /usr/local/bin/skale
```

- Test the installation

```bash
skale --help
```

## CLI usage

### Top level commands

##### host

Prints current SKALE node host

```bash
skale host
```

##### Attach 

```bash
skale attach http://127.0.0.1:3007
```

> For old nodes use `--skip-check` option


### User commands

##### token

Show user registration token

> Local-only

```bash
skale user token
```

##### register

Interactive:
```bash
skale user register
```

Non-interactive:
```bash
skale user register -u/--username USERNAME -p/--password PASSWORD -t/--token TOKEN
```

##### login

Interactive:
```bash
skale user login
```

Non-interactive:
```bash
skale user login -u/--username user -p/--password pass
```

##### logout

```bash
skale user logout
```


### Node commands

> Prefix: `skale node`


##### node init

Init SKALE node on current machine

> Local-only

```bash
skale node init
```

Required arguments:
- `--github-token` - token for accessing `skale-node` repo
- `--docker-username` - username for DockerHub
- `--docker-password` - password for DockerHub
- `--db-password` - MySQL password for local node database

Optional arguments:
- `--git-branch` - git branch of `skale-node` to use
- `--rpc-ip` - RPC IP of the network with SKALE Manager
- `--rpc-port` - RPC port of the network with SKALE Manager
- `--db-user` - MySQL user for local node database 
- `--db-root-password` - Password for root user of node internal database 
(equal to user password by default)  
- `--db-root-password` - Port for of node internal database (default is `3306`)

##### node register

Register SKALE node on SKALE Manager contracts

- Login required

```bash
skale node register
```

Required arguments:
- `--name` - SKALE node name
- `--ip` - public IP for RPC connections & consensus
- `--port` - base port for node sChains
 
##### node info 

Get base info about SKALE node

- Login required

```bash
skale node info
```

Options:

`-f/--format json/text` - optional

### Wallet commands

> Prefix: `skale wallet`

Commands related to Ethereum wallet associated with SKALE node

##### wallet info

- Login required

```bash
skale wallet info
```

Options:

`-f/--format json/text` - optional

### sChain commands

> Prefix: `skale schains`

##### sChains list

List of sChains served by connected node

```bash
skale schains ls
```

##### schains config

```bash
skale schains config SCHAIN_NAME
```

### Containers commands

Node containers commands

> Prefix: `skale containers`


##### SKALE containers 

List of SKALE containers running on connected node

```bash
skale containers ls
```

Options:

- `-a/--all` - list all containers (by default - only running) 

##### sChain containers 

List of sChain containers running on connected node

```bash
skale containers schains
```

Options:

- `-a/--all` - list all sChain containers (by default - only running)


### Logs commands 

> Prefix: `skale logs`


##### Logs list

```bash
skale logs ls
```

##### Download log file

Base logs:

```bash
skale logs download `filename`
```

sChain logs 

```bash
skale logs download --schain/-s `schain_name` `filename`
```


### Validator commands (not implemented yet)

> Prefix: `skale validator`


##### validator list

```bash
skale validator list
```


## Development

Create release:

```bash
bash build.sh patch/minor/major
```

Build executable:

```bash
pyinstaller --onefile main.spec
```

Run commands in dev mode:

```bash
ENV=dev python main.py YOUR_COMMAND
```
