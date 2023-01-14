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
        "flake8==5.0.4",
        "isort>=4.2.15,<5.10.2",
    ],
    'dev': [
        "bumpversion==0.6.0",
        "pytest==7.2.1",
        "pytest-cov==3.0.0",
        "twine==4.0.1",
        "mock==4.0.3",
        "freezegun==1.2.2"
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
        "click==8.1.3",
        "PyInstaller==5.6.2",
        "docker==6.0.1",
        "texttable==1.6.4",
        "python-dateutil==2.8.2",
        "Jinja2==3.1.2",
        "psutil==5.9.1",
        "python-dotenv==0.21.0",
        "terminaltables==3.1.10",
        "requests==2.28.1",
        "GitPython==3.1.27",
        "packaging==21.3",
        "python-debian==0.1.48",
        "python-iptables==1.0.0",
        "PyYAML==6.0",
        "MarkupSafe==2.1.1",
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
