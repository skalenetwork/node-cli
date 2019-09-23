import click
from core.helper import login_required, get
from core.print_formatters import print_metrics


@click.group()
def metrics_cli():
    pass


@metrics_cli.group('metrics', help="Node metrics commands")
def metrics():
    pass


@metrics.command(help="List of bounties and metrics for the first year")
@login_required
def first():
    print('Please wait - collecting metrics from blockchain...')
    bounty_list = get('first-bounties')
    if not bounty_list:
        print('No bounties found')
        return
    print_metrics(bounty_list)


@metrics.command(help="List of bounties and metrics for the last year")
@login_required
def last():
    print('Please wait - collecting metrics from blockchain...')
    bounty_list = get('last-bounties')
    if not bounty_list:
        print('No bounties found')
        return
    print_metrics(bounty_list)
