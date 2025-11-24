from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("node-cli")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

if __name__ == '__main__':
    print(__version__)
