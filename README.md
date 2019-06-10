# SKALE node CLI

SKALE Node CLI, part of the SKALE suite of validator tools, is the command line to setup, register and maintain your SKALE node.

## Installation

- Download executable
```bash
curl -L https://skale-cli.sfo2.cdn.digitaloceanspaces.com/skale-VERSION_NUM-`uname -s`-`uname -m` > /usr/local/bin/skale
```

With `sudo`:

```bash
sudo bash -c "curl -L https://skale-cli.sfo2.cdn.digitaloceanspaces.com/skale-VERSION_NUM-`uname -s`-`uname -m` >  /usr/local/bin/skale"
```

- Apply executable permissions to the binary:

```bash
chmod +x /usr/local/bin/skale
```

- Test the installation

```bash
skale --help
```

## Base commands


### Top level commands

##### host

Prints current SKALE node host

```bash
skale host
```

##### setHost 

```bash
skale setHost http://127.0.0.1:3007
```

> For old nodes use `--skip-check` option


### User commands

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


##### node register

Register SKALE node on SKALE Manager contracts

- Login required

```bash
skale node register
```

 
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

### sChain commands (not implemented yet)

> Prefix: `skale schains`

##### schains list

```bash
skale schains list
```

##### schains config 

```bash
skale schains config schain_name
```

### Validator commands (not implemented yet)

> Prefix: `skale validator`


##### validator list

```bash
skale validator list
```


### Logs commands (not implemented yet)

> Prefix: `skale log`


##### log list

```bash
skale log list
```

##### log download

```bash
skale log download /url/
```



## Development

Build executable:

```bash
pyinstaller --onefile main.spec
```

Run in dev mode:

```bash
ENV=dev python main.py YOUR_COMMAND
```
