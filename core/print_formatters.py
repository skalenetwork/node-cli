import os
import datetime
import texttable
from dateutil import parser

def get_tty_width():
    tty_size = os.popen('stty size 2> /dev/null', 'r').read().split()
    if len(tty_size) != 2:
        return 0
    _, width = tty_size
    return int(width)


class Formatter(object):
    def table(self, headers, rows):
        table = texttable.Texttable(max_width=get_tty_width())
        table.set_cols_dtype(['t' for h in headers])
        table.add_rows([headers] + rows)
        table.set_deco(table.HEADER)
        table.set_chars(['-', '|', '+', '-'])

        return table.draw()

def format_date(date):
    return date.strftime("%b %d %Y %H:%M:%S")

def print_containers(containers):
    headers = [
        'Name',
        'Status',
        'Started At',
        'Image'
    ]
    rows = []
    for container in containers:
        date = parser.parse(container["state"]["StartedAt"])
        status = container["state"]["Status"].capitalize()

        if not container['state']['Running']:
            finished_date = parser.parse(container["state"]["FinishedAt"])
            status = f'{status} ({format_date(finished_date)})'

        rows.append([
            container['name'],
            status,
            format_date(date),
            container['image']
        ])
    print(Formatter().table(headers, rows))


def print_schains(schains):
    headers = [
        'Name',
        'Owner',
        'Size',
        'Lifetime',
        'Created At',
        'Deposit'
    ]
    rows = []
    for schain in schains:
        date = datetime.datetime.fromtimestamp(schain['startDate'])
        rows.append([
            schain['name'],
            schain['owner'],
            schain['partOfNode'],
            schain['lifetime'],
            date.strftime("%b %d %Y %H:%M:%S"),
            schain['deposit'],
        ])
    print(Formatter().table(headers, rows))