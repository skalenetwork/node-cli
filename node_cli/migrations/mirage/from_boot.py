import glob
import logging
import os
from pathlib import Path

from node_cli.core.docker_config import restart_docker_service
from node_cli.utils.helper import run_cmd

logger = logging.getLogger(__name__)

NFT_CHAIN_BASE_PATH = '/etc/nft.conf.d/skale/chains'
NFT_COMMITTEE_SCOPE_CHAIN_NAME = 'mirage-committee'


class NoLegacyNFTChainConfigError(Exception):
    pass


def rename_chain_file(old_filepath: str, new_filepath: str) -> None:
    old_path = Path(old_filepath)
    new_path = Path(new_filepath)
    if not old_path.exists():
        raise NoLegacyNFTChainConfigError(f'File {old_filepath} does not exists')
    old_path.rename(Path(new_path))


def rename_chain_in_config(config_path: str, old_chain_name: str, new_chain_name: str) -> None:
    content = ''
    with open(config_path, 'r') as f:
        content = f.read()

    updated_content = content.replace(old_chain_name, new_chain_name)

    with open(config_path, 'w') as f:
        f.write(updated_content)


def migrate_nft_chain() -> None:
    after_boot_chain_path = glob.glob(os.path.join(NFT_CHAIN_BASE_PATH, '*'))[0]
    old_chain_name = Path(after_boot_chain_path).name.removesuffix('.conf')
    new_chain_name = NFT_COMMITTEE_SCOPE_CHAIN_NAME
    rename_chain_in_config(after_boot_chain_path, old_chain_name, new_chain_name)
    after_migration_chain_path = os.path.join(
        NFT_CHAIN_BASE_PATH, f'{NFT_COMMITTEE_SCOPE_CHAIN_NAME}.conf'
    )
    rename_chain_file(after_boot_chain_path, after_migration_chain_path)


def reload_nft():
    run_cmd(['nft', '-f', '/etc/nftables.conf'])


def migrate_nftables_from_boot():
    logger.info('Starting nftables migration from boot')
    migrate_nft_chain()
    logger.info('Reloading nftables rules')
    reload_nft()
    logger.info('Restart docker service')
    restart_docker_service()
