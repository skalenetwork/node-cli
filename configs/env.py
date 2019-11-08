import os
from dotenv import load_dotenv

load_dotenv()


settings = {
    'IMA_ENDPOINT': '',
    'GIT_BRANCH': '',
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
    'DKG_CONTRACTS_INFO_URL': '',
}


for option_name in settings:
    if option_name in os.environ:
        settings[option_name] = str(os.getenv(option_name))
