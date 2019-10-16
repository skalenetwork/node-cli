import os
import re
from setuptools import find_packages, setup


def read(*parts):
    path = os.path.join(os.path.dirname(__file__), *parts)
    f = open(path, "r")
    return f.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Couldn't parse version from file.")


extras_require = {
    'linter': [
        "flake8==3.4.1",
        "isort>=4.2.15,<4.3.5",
    ],
    'dev': [
        "boto3==1.9.250",
        "bumpversion==0.5.3",
        "PyInstaller==3.5",
        "pytest==5.2.1",
        "pytest-cov==2.7.1",
        "twine==1.12.1",
        "when-changed"
    ]
}

extras_require['dev'] = (
    extras_require['linter'] + extras_require['dev']
)


setup(
    name='skale-node-cli',
    # *IMPORTANT*: Don't manually change the version here.
    # Use the 'bumpversion' utility instead.
    version=find_version("cli", "__init__.py"),
    include_package_data=True,
    description='SKALE client tools',
    long_description_markdown_filename='README.md',
    author='SKALE Labs',
    author_email='support@skalelabs.com',
    url='https://github.com/skalenetwork/skale-node-cli',
    install_requires=[
        "click==7.0",
        "confuse",
        "readsettings==3.4.0",
        "web3==4.9.2",
        "texttable==1.6.2",
        "python-dateutil==2.8.0",
        "Jinja2==2.10.1",
        "skale-py==0.82.0",
        "eth-hash==0.2.0",
        "pycryptodome==3.8.2",
        "psutil==5.6.3"
    ],
    python_requires='>=3.6,<4',
    extras_require=extras_require,

    keywords=['skale', 'cli'],
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
)
