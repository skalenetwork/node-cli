import time
import logging
from logging import StreamHandler


logging.basicConfig(
    handlers=[
        StreamHandler(),
    ],
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    for i in range(20000):
        logger.info(f'Test {i}')
    logger.info('Waiting')

    while True:
        time.sleep(30)


if __name__ == '__main__':
    main()
