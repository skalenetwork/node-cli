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
        "flake8==3.7.9",
        "isort>=4.2.15,<5.8.1",
    ],
    'dev': [
        "bumpversion==0.6.0",
        "pytest==6.2.3",
        "pytest-cov==2.9.0",
        "twine==2.0.0",
        "mock==4.0.3",
        "freezegun==0.3.15"
    ]
}

extras_require['dev'] = (
    extras_require['linter'] + extras_require['dev']
)


setup(
    name='node-cli',
    # *IMPORTANT*: Don't manually change the version here.
    # Use the 'bumpversion' utility instead.
    version=find_version("node_cli", "cli", "__init__.py"),
    include_package_data=True,
    description='SKALE client tools',
    long_description_markdown_filename='README.md',
    author='SKALE Labs',
    author_email='support@skalelabs.com',
    url='https://github.com/skalenetwork/node-cli',
    install_requires=[
        "click==7.1.2",
        "docker==4.2.2",
        "PyInstaller==3.6",
        "texttable==1.6.2",
        "python-dateutil==2.8.1",
        "Jinja2==2.11.2",
        "psutil==5.7.0",
        "python-dotenv==0.13.0",
        "terminaltables==3.1.0",
        "requests==2.23.0",
        "GitPython==3.1.14",
        "PyYAML==5.4.1",
        "packaging==20.9",
        "python-debian==0.1.39",
        "python-iptables==1.0.0"
    ],
    python_requires='>=3.6,<4',
    extras_require=extras_require,

    keywords=['skale', 'cli'],
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
)
