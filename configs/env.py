import os
from dotenv import load_dotenv
from configs import DOTENV_FILEPATH


env_params = {
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
}


def get_params(env_filepath=DOTENV_FILEPATH):
    load_dotenv(dotenv_path=env_filepath)
    for option_name in env_params:
        if option_name in os.environ:
            env_params[option_name] = str(os.getenv(option_name))

    return env_params
