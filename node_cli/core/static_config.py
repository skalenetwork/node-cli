import os
import yaml

from node_cli.configs import (
    CONTAINER_CONFIG_PATH,
    MIRAGE_STATIC_PARAMS_FILEPATH,
    STATIC_PARAMS_FILEPATH,
)
from node_cli.utils.node_type import NodeType


def get_static_params(
    node_type: NodeType,
    env_type: str = 'mainnet',
    config_path: str = CONTAINER_CONFIG_PATH,
) -> dict:
    if node_type == NodeType.MIRAGE:
        static_params_base_filepath = MIRAGE_STATIC_PARAMS_FILEPATH
    else:
        static_params_base_filepath = STATIC_PARAMS_FILEPATH

    static_params_filename = os.path.basename(static_params_base_filepath)
    static_params_filepath = os.path.join(config_path, static_params_filename)
    with open(static_params_filepath) as requirements_file:
        ydata = yaml.load(requirements_file, Loader=yaml.Loader)
        return ydata['envs'][env_type]
