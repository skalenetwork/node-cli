import os
from dotenv import load_dotenv
from node_cli.configs import SKALE_DIR, CONTAINER_CONFIG_PATH


SKALE_DIR_ENV_FILEPATH = os.path.join(SKALE_DIR, '.env')
CONFIGS_ENV_FILEPATH = os.path.join(CONTAINER_CONFIG_PATH, '.env')


ALLOWED_ENV_TYPES = ['mainnet', 'testnet', 'qanet', 'devnet']

REQUIRED_PARAMS = {
    'CONTAINER_CONFIGS_STREAM': '',
    'ENDPOINT': '',
    'MANAGER_CONTRACTS_ABI_URL': '',
    'IMA_CONTRACTS_ABI_URL': '',
    'FILEBEAT_HOST': '',
    'DISK_MOUNTPOINT': '',
    'SGX_SERVER_URL': '',
    'DOCKER_LVMPY_STREAM': '',
    'ENV_TYPE': '',
}

REQUIRED_PARAMS_SYNC = {
    'SCHAIN_NAME': '',
    'CONTAINER_CONFIGS_STREAM': '',
    'ENDPOINT': '',
    'MANAGER_CONTRACTS_ABI_URL': '',
    'IMA_CONTRACTS_ABI_URL': '',
    'DISK_MOUNTPOINT': '',
    'DOCKER_LVMPY_STREAM': '',
    'ENV_TYPE': ''
}

OPTIONAL_PARAMS = {
    'MONITORING_CONTAINERS': '',
    'TG_API_KEY': '',
    'TG_CHAT_ID': '',
    'CONTAINER_CONFIGS_DIR': '',
    'DISABLE_DRY_RUN': '',
    'DEFAULT_GAS_LIMIT': '',
    'DEFAULT_GAS_PRICE_WEI': '',
    'SKIP_DOCKER_CONFIG': '',
    'ENFORCE_BTRFS': '',
    'SKIP_DOCKER_CLEANUP': ''
}


def absent_params(params):
    return list(filter(
        lambda key: key not in OPTIONAL_PARAMS and not params[key],
        params)
    )


def get_env_config(env_filepath: str = SKALE_DIR_ENV_FILEPATH, sync_node: bool = False):
    load_dotenv(dotenv_path=env_filepath)
    params = REQUIRED_PARAMS_SYNC.copy() if sync_node else REQUIRED_PARAMS.copy()
    params.update(OPTIONAL_PARAMS)
    for option_name in params:
        env_param = os.getenv(option_name)
        if env_param is not None:
            params[option_name] = str(env_param)
    validate_params(params)
    return params


def validate_params(params):  # todo: temporary fix
    if params['ENV_TYPE'] not in ALLOWED_ENV_TYPES:
        raise NotValidEnvParamsError(
            f'Allowed ENV_TYPE values are {ALLOWED_ENV_TYPES}. '
            f'Actual: "{params["ENV_TYPE"]}"'
        )


class NotValidEnvParamsError(Exception):
    """Raised when something is wrong with provided env params"""
