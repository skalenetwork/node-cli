import logging
import subprocess
import shlex

from tools.helper import run_cmd, extract_env_params
from configs import MYSQL_BACKUP_CONTAINER_PATH, MYSQL_BACKUP_PATH


logger = logging.getLogger(__name__)


def run_mysql_cmd(cmd, env_filepath):
    mysql_creds_str = mysql_creds_for_cmd(env_filepath)
    cmd_str = f'docker exec -t skale_mysql bash -c "{cmd} {mysql_creds_str}"'
    cmd = shlex.split(cmd_str)
    return run_cmd(cmd, secure=True)


def mysql_creds_for_cmd(env_filepath: str) -> str:
    """Returns string with user and password flags for MySQL CLI.

    :param env_filepath: Path to the environment params file
    :type address: str
    :returns: Formatted string
    :rtype: str
    """
    env_params = extract_env_params(env_filepath)
    return f'-u \'{env_params["DB_USER"]}\' -p\'{env_params["DB_PASSWORD"]}\''


def create_mysql_backup(env_filepath: str) -> bool:
    try:
        print('Creating MySQL backup...')
        run_mysql_cmd(
            f'mysqldump --all-databases --single-transaction --quick --lock-tables=false \
                > {MYSQL_BACKUP_CONTAINER_PATH}',
            env_filepath
        )
        print(f'MySQL backup succesfully created: {MYSQL_BACKUP_PATH}')
        return True
    except subprocess.CalledProcessError as e:
        logger.error(e)
        print('Something went wrong while trying to create MySQL backup, check out CLI logs')
        return False


def restore_mysql_backup(env_filepath: str) -> bool:
    try:
        print('Restoring MySQL from backup...')
        run_mysql_cmd(
            f'mysql < {MYSQL_BACKUP_CONTAINER_PATH}',
            env_filepath
        )
        print(f'MySQL DB was succesfully restored from backup: {MYSQL_BACKUP_PATH}')
        return True
    except subprocess.CalledProcessError as e:
        logger.error(e)
        print('Something went wrong while trying to restore MySQL from backup, check out CLI logs')
        return False
