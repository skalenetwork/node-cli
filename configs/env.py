import os
from dotenv import load_dotenv
from configs import DOTENV_FILEPATH


base_params = {
    'IMA_ENDPOINT': '',
    'GIT_BRANCH': '',
    'GITHUB_TOKEN': '',
    'DOCKER_USERNAME': '',
    'DOCKER_PASSWORD': '',
    'ENDPOINT': '',
    'DB_USER': 'root',
    'DB_PASSWORD': '',
    'DB_ROOT_PASSWORD': '',
    'DB_PORT': '3306',
    'MANAGER_CONTRACTS_INFO_URL': '',
    'IMA_CONTRACTS_INFO_URL': '',
    'FILEBEAT_HOST': '',
    'DISK_MOUNTPOINT': '',
    'SGX_SERVER_URL': '',
}


def get_params(env_filepath=DOTENV_FILEPATH):
    load_dotenv(dotenv_path=env_filepath)
    params = base_params.copy()
    for option_name in params:
        env_param = os.getenv(option_name)
        if env_param is not None:
            params[option_name] = str(env_param)
    return params
