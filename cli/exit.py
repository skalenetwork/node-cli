import click
import logging
from core.helper import get_request, post_request
from core.print_formatters import print_err_response, print_exit_status
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
    status, payload = post_request('start_exit')
    if status == 'ok':
        msg = TEXTS['exit']['start']
        logger.info(msg)
        print(msg)
    else:
        print_err_response(payload)


@node_exit.command('status', help="Get exit process status")
def status():
    status, payload = get_request('exit_status')
    if status == 'ok':
        exit_status = payload
        print_exit_status(exit_status)
    else:
        print_err_response(payload)


@node_exit.command('finalize', help="Finalize exit process")
def finalize():
    pass
