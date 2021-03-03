import os
from dotenv import load_dotenv


ALLOWED_ENV_TYPES = ['mainnet', 'testnet', 'qanet', 'devnet']


base_params = {
    'IMA_ENDPOINT': '',
    'CONTAINER_CONFIGS_STREAM': '',
    'ENDPOINT': '',
    'DB_USER': 'root',
    'DB_PASSWORD': '',
    'DB_ROOT_PASSWORD': '',
    'DB_PORT': '3306',
    'MANAGER_CONTRACTS_ABI_URL': '',
    'IMA_CONTRACTS_ABI_URL': '',
    'FILEBEAT_HOST': '',
    'DISK_MOUNTPOINT': '',
    'SGX_SERVER_URL': '',
    'CONTAINER_CONFIGS_DIR': '',
    'DOCKER_LVMPY_STREAM': '',
    'ENV_TYPE': '',
}


optional_params = {
    'MONITORING_CONTAINERS': '',
    'TG_API_KEY': '',
    'TG_CHAT_ID': '',
    'CONTAINER_CONFIGS_DIR': '',
    'DISABLE_DRY_RUN': '',
    'DEFAULT_GAS_LIMIT': '',
    'DEFAULT_GAS_PRICE_WEI': ''
}


def absent_params(params):
    return list(filter(
        lambda key: key not in optional_params and not params[key],
        params)
    )


def get_params(env_filepath):
    load_dotenv(dotenv_path=env_filepath)
    params = base_params.copy()
    params.update(optional_params)
    for option_name in params:
        env_param = os.getenv(option_name)
        if env_param is not None:
            params[option_name] = str(env_param)
    validate_params(params)
    return params


def validate_params(params):  # todo: temporary fix
    if params['ENV_TYPE'] not in ALLOWED_ENV_TYPES:
        raise NotValidEnvParamsError(
            f'Allowed ENV_TYPE are {ALLOWED_ENV_TYPES}. '
            f'Actual: "{params["ENV_TYPE"]}"'
        )


class NotValidEnvParamsError(Exception):
    """Raised when something is wrong with provided env params"""
