from node_cli.configs.env import NotValidEnvParamsError, validate_params


def test_validate_params():
    valid_config = {'ENV_TYPE': 'mainnet'}
    validate_params(valid_config)
    invalid_config = {'ENV_TYPE': ''}
    error = None
    try:
        validate_params(invalid_config)
    except NotValidEnvParamsError as e:
        error = e
    assert error is not None
    earg = 'Allowed ENV_TYPE values are [\'mainnet\', \'testnet\', \'qanet\', \'devnet\']. Actual: ""'  # noqa
    assert error.args[0] == earg
