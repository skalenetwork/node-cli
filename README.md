# Node CLI

![Build and publish](https://github.com/skalenetwork/node-cli/workflows/Build%20and%20publish/badge.svg)
![Test](https://github.com/skalenetwork/node-cli/workflows/Test/badge.svg)
[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

SKALE Node CLI, part of the SKALE suite of validator tools, is the command line to setup, register and maintain your SKALE node.
## Installation

-   Prerequisites

Ensure that the following package is installed: **docker**, **docker-compose** (1.27.4+)

-   Download the executable

```shell
VERSION_NUM={put the version number here} && sudo -E bash -c "curl -L https://github.com/skalenetwork/node-cli/releases/download/$VERSION_NUM/skale-$VERSION_NUM-`uname -s`-`uname -m` >  /usr/local/bin/skale"
```

For versions `<1.1.0`:

```shell
VERSION_NUM=0.0.0 && sudo -E bash -c "curl -L https://skale-cli.sfo2.cdn.digitaloceanspaces.com/skale-$VERSION_NUM-`uname -s`-`uname -m` >  /usr/local/bin/skale"
```

-   Apply executable permissions to the downloaded binary:

```shell
chmod +x /usr/local/bin/skale
```

-   Test the installation

```shell
skale --help
```

## Development

### Setup repo

#### Install development dependencies

```shell
pip install -e .[dev]
```

##### Add flake8 git hook

In file `.git/hooks/pre-commit` add:

```shell
#!/bin/sh
flake8 .
```

### Debugging

Run commands in dev mode:

```shell
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

[![License](https://img.shields.io/github/license/skalenetwork/node-cli.svg)](LICENSE)

Copyright (C) 2018-present SKALE Labs
