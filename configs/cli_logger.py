import os
from configs.node import HOME_DIR

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

LOG_FILE_SIZE_MB = 300
LOG_FILE_SIZE_BYTES = LOG_FILE_SIZE_MB * 1000000

LOG_BACKUP_COUNT = 1
LOG_DATA_PATH = os.path.join(HOME_DIR, '.skale-cli-log')

LOG_FILENAME = 'node-cli.log'
DEBUG_LOG_FILENAME = 'debug-node-cli.log'
LOG_FILEPATH = os.path.join(LOG_DATA_PATH, LOG_FILENAME)
DEBUG_LOG_FILEPATH = os.path.join(LOG_DATA_PATH, DEBUG_LOG_FILENAME)