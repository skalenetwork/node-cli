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
        "isort>=4.2.15,<4.3.22",
    ],
    'dev': [
        "boto3==1.9.233",
        "bumpversion==0.5.3",
        "PyInstaller==3.5",
        "pytest==5.2.1",
        "pytest-cov==2.8.1",
        "twine==2.0.0",
        "mock==3.0.5",
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
        "readsettings==3.4.5",
        "web3==5.2.2",
        "texttable==1.6.2",
        "python-dateutil==2.8.1",
        "Jinja2==2.11.1",
        "skale-py==2.0b0",
        "psutil==5.6.6",
        "pycryptodome==3.9.7",
        "python-dotenv==0.10.3",
        "terminaltables==3.1.0"
    ],
    python_requires='>=3.6,<4',
    extras_require=extras_require,

    keywords=['skale', 'cli'],
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
)
