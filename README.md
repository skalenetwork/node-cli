# SKALE node CLI


Build executable

```bash
 pyinstaller --onefile main.py
```


# Base commands


### Top level commands

##### setHost 

```bash
skale setHost http://127.0.0.1:3007
```

##### login

Interactive:
```bash
skale login
```

Non-interactive:
```bash
skale login -u/--username user -p/--password pass
```

##### logout

```bash
skale logout
```


### Node commands

> Prefix: `skale node`

 
##### node info 

Get base info about SKALE node

- Login required

```bash
skale node info
```

### Wallet commands

> Prefix: `skale wallet`

Commands related to Ethereum wallet associated with SKALE node

##### wallet info

- Login required

```bash
skale wallet info
```

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