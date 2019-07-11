import click
import pprint
from core.helper import login_required, get
from core.print_formatters import print_containers, print_schains


@click.group()
def schains_cli():
    pass


@schains_cli.group('schains', help="Node sChains commands")
def schains():
    pass


@schains.command(help="List of sChains served by connected node")
@login_required
def ls():
    schains_list = get('node_schains')
    if not schains_list:
        print('No sChains found')
        return
    print_schains(schains_list)


@schains.command('config', help="sChain config")
@click.argument('schain_name')
@login_required
def get_schain_config(schain_name):
    schain_config = get('schain_config', {'schain-name': schain_name})
    if not schain_config:
        return
    pprint.pprint(schain_config)
