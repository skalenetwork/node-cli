# SKALE node CLI


Build executable:

```bash
 pyinstaller --onefile main.spec
```

Run in dev mode:

```bash
ENV=dev python main.py YOUR_COMMAND
```


# Base commands


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

##### schains list

```bash
skale schains list
```

##### schains config 

```bash
skale schains config schain_name
```

### Validator commands

> Prefix: `skale schains`


##### validator list

```bash
skale validator list
```


### Logs commands

> Prefix: `skale log`


##### log list

```bash
skale log list
```

##### log download

```bash
skale log download /url/
```