import os
import re
from setuptools import setup


def read(*parts):
    path = os.path.join(os.path.dirname(__file__), *parts)
    f = open(path, "r")
    return f.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Couldn't parse version from file.")


setup(
    name='skale-node-cli',
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version=find_version("cli", "__init__.py"),
    include_package_data=True,
    install_requires=[
        'click',
    ]
)
