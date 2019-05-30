import subprocess
from cli.config import DEPENDENCIES_SCRIPT

def install_host_dependencies():
    res = subprocess.run(["bash", DEPENDENCIES_SCRIPT])
    # todo: check execution status