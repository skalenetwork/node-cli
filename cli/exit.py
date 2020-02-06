import click
import logging
from core.helper import get, post
from core.print_formatters import print_exit_status
from tools.texts import Texts

logger = logging.getLogger(__name__)
TEXTS = Texts()


@click.group()
def exit_cli():
    pass


@exit_cli.group('exit', help="Exit commands")
def node_exit():
    pass


@node_exit.command('start', help="Start exiting process")
def start():
    response = post('start_exit')
    if response is None:
        print(TEXTS['service']['empty_response'])
        return None
    if response['res']:
        msg = TEXTS['exit']['start']
        logger.info(msg)
        print(msg)
    else:
        logger.info('Bad response. Something went wrong. Try again')


@node_exit.command('status', help="Get exit process status")
def status():
    exit_status = get('exit_status')
    if not exit_status:
        return
    print_exit_status(exit_status)


@node_exit.command('finalize', help="Finalize exit process")
def finalize():
    pass
