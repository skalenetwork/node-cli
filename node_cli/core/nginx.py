import logging
import os.path

from node_cli.configs import NODE_CERTS_PATH, NGINX_TEMPLATE_FILEPATH, NGINX_CONFIG_FILEPATH
from node_cli.utils.helper import process_template


logger = logging.getLogger(__name__)

SSL_KEY_NAME = 'ssl_key'
SSL_CRT_NAME = 'ssl_cert'


def generate_nginx_config():
    ssl_on = check_ssl_certs()
    template_data = {
        'ssl': ssl_on,
    }
    logger.info(f'Processing nginx template. ssl: {ssl_on}')
    process_template(NGINX_TEMPLATE_FILEPATH, NGINX_CONFIG_FILEPATH, template_data)


def check_ssl_certs():
    crt_path = os.path.join(NODE_CERTS_PATH, SSL_CRT_NAME)
    key_path = os.path.join(NODE_CERTS_PATH, SSL_KEY_NAME)
    return os.path.exists(crt_path) and os.path.exists(key_path)
