import click
from core.helper import login_required, get, download_log_file, local_only, download_dump
from core.print_formatters import print_logs

from configs.cli_logger import LOG_FILEPATH, DEBUG_LOG_FILEPATH


@click.group()
def logs_cli():
    pass


@logs_cli.group(help="Logs commands")
def logs():
    pass


@logs.command(help="List of log files on connected node")
@login_required
def ls():
    logs = get('logs')
    if not logs:
        return
    print_logs(logs)


@logs.command(help="Download log file from connected node")
@click.argument('name')
@click.option('--schain', '-s', help='sChain log type')
@login_required
def download(name, schain):
    type = 'schain' if schain else 'base'
    res = download_log_file(name, type, schain)
    if res:
        print(f'File {res} downloaded')
    else:
        print('Something went wrong, couldn\'t download log file')


@logs.command(help="Fetch the logs of the node-cli")
@click.option('--debug', is_flag=True)
@local_only
def cli(debug):
    filepath = DEBUG_LOG_FILEPATH if debug else LOG_FILEPATH
    with open(filepath, 'r') as fin:
        print(fin.read())


@logs.command(help="Download log file from container on the connected node")
@click.argument('name')
@click.option(
    '--lines',
    '-l',
    help='Output specified number of lines at the end of logs',
    default=None
)
@login_required
def container(name, lines):
    params = {'container_name': name}
    if lines: params['lines'] = lines
    container_logs = get('container_logs', params)
    print(container_logs)



@logs.command(help="Dump all logs from the connected node")
@click.option(
    '--container',
    '-c',
    help='Dump logs only from specified container',
    default=None
)
@click.argument('path')
@login_required
def dump(container, path):
    res = download_dump(path, container)
    if res:
        print(f'File {res} downloaded')