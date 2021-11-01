import sys
import time
import signal
import logging
from logging import StreamHandler


logging.basicConfig(
    handlers=[
        StreamHandler(),
    ],
    level=logging.INFO
)

logger = logging.getLogger(__name__)

LINES = 10


def signal_handler(sig, frame):
    print('SIGTERM handled, sleeping for 10 seconds...')
    time.sleep(10)
    print('signal_handler completed, exiting...')
    sys.exit(0)


def main():
    for i in range(LINES):
        logger.info(f'Test {i}')
    logger.info('Waiting')

    while True:
        time.sleep(30)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    main()
