import os
import logging
import urllib.request
import subprocess
from subprocess import PIPE
import json

from jinja2 import Environment

logger = logging.getLogger(__name__)


def read_json(path):
    with open(path, encoding='utf-8') as data_file:
        return json.loads(data_file.read())


def write_json(path, content):
    with open(path, 'w') as outfile:
        json.dump(content, outfile, indent=4)


def run_cmd(cmd, env={}, shell=False):
    logger.info(f'Running: {cmd}')
    res = subprocess.run(cmd, shell=shell, stdout=PIPE, stderr=PIPE, env={**env, **os.environ})
    if res.returncode:
        logger.error('Error during shell execution:')
        logger.error(res.stderr.decode('UTF-8').rstrip())
        raise subprocess.CalledProcessError(res.returncode, cmd)
    return res


def format_output(res):
    return res.stdout.decode('UTF-8').rstrip(), res.stderr.decode('UTF-8').rstrip()


def download_file(url, filepath):
    return urllib.request.urlretrieve(url, filepath)


def process_template(source, destination, data):
    """
    :param source: j2 template source path
    :param destination: out file path
    :param data: dictionary with fields for template
    :return: Nothing
    """
    template = read_file(source)
    processed_template = Environment().from_string(template).render(data)
    with open(destination, "w") as f:
        f.write(processed_template)


def read_file(path):
    file = open(path, 'r')
    text = file.read()
    file.close()
    return text


def get_username():
    return os.environ.get('USERNAME') or os.environ.get('USER')
