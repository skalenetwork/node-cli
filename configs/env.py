import os
from dotenv import load_dotenv


base_params = {
    'IMA_ENDPOINT': '',
    'CONTAINER_CONFIGS_STREAM': '',
    'DOCKER_USERNAME': '',
    'DOCKER_PASSWORD': '',
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
    'DOCKER_LVMPY_STREAM': ''
}


def absent_params(params):
    return list(filter(
        lambda key: key != 'CONTAINER_CONFIGS_DIR' and not params[key],
        params)
    )


def get_params(env_filepath):
    load_dotenv(dotenv_path=env_filepath)
    params = base_params.copy()
    for option_name in params:
        env_param = os.getenv(option_name)
        if env_param is not None:
            params[option_name] = str(env_param)
    return params
