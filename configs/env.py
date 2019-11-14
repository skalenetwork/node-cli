import os
from dotenv import load_dotenv
from configs import DOTENV_FILEPATH

load_dotenv(dotenv_path=DOTENV_FILEPATH)


settings = {
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


for option_name in settings:
    if option_name in os.environ:
        settings[option_name] = str(os.getenv(option_name))
