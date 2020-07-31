import os
from dotenv import load_dotenv


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
    'DOCKER_LVMPY_STREAM': ''
}


optional_params = {
    'MONITORING_CONTAINERS': '',
    'TG_API_KEY': '',
    'TG_CHAT_ID': '',
    'CONTAINER_CONFIGS_DIR': ''
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
    return params
