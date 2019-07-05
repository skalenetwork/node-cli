import click
from core.helper import login_required, get
from core.print_formatters import print_containers


@click.group()
def containers_cli():
    pass


@containers_cli.group('containers', help="Node containers commands")
def containers():
    pass


@containers.command(help="List of sChain containers running on connected node")
@click.option('--all', '-a', is_flag=True)
@login_required
def schains(all):
    schain_containers = get('schains_containers', {'all': all})
    if schain_containers is None:
        return
    print_containers(schain_containers)


@containers.command(help="List of SKALE containers running on connected node")
@click.option('--all', '-a', is_flag=True)
@login_required
def ls(all):
    containers_list = get('skale_containers', {'all': all})
    if not containers_list: return
    print_containers(containers_list)
