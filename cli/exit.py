import click
from core.helper import login_required, get, post
from core.print_formatters import print_exit_status


@click.group()
def exit_cli():
    pass


@exit_cli.group('exit', help="Exit commands")
def node_exit():
    pass


@node_exit.command('start', help="Start exiting process")
@login_required
def start():
    post('start_exit')


@node_exit.command('status', help="Get exit process status")
@login_required
def status():
    exit_status = get('exit_status')
    if not exit_status:
        return
    print_exit_status(exit_status)


@node_exit.command('finalize', help="Finalize exit process")
@login_required
def finalize():
    post('finalize_exit')