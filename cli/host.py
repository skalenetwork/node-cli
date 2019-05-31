import os
import subprocess
from cli.config import DEPENDENCIES_SCRIPT

def install_host_dependencies():
    env = {
        **os.environ,
        'SKALE_CMD': 'host_deps'
    }
    res = subprocess.run(["sudo", "bash", DEPENDENCIES_SCRIPT], env=env)
    # todo: check execution status