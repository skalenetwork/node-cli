import click
from core.helper import login_required


@click.group()
def exit_cli():
    pass


@exit_cli.group('exit', help="Exit commands")
def node_exit():
    pass


@node_exit.command('start', help="Start exiting process")
@login_required
def start():
    pass


@node_exit.command('status', help="Get exit process status")
@login_required
def status():
    pass


@node_exit.command('finalize', help="Finalize exit process")
@login_required
def finalize():
    pass