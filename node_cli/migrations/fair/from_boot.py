import logging
import os
from pathlib import Path

from node_cli.core.docker_config import restart_docker_service
from node_cli.utils.helper import run_cmd

logger = logging.getLogger(__name__)

NFT_CHAIN_BASE_PATH = '/etc/nft.conf.d/skale/chains'
NFT_COMMITTEE_SCOPE_CHAIN_NAME = 'fair-committee'


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


def migrate_nft_chain(chain_name: str) -> None:
    after_boot_chain_path = os.path.join(NFT_CHAIN_BASE_PATH, f'skale-{chain_name}.conf')
    new_chain_name = NFT_COMMITTEE_SCOPE_CHAIN_NAME
    after_migration_chain_path = os.path.join(
        NFT_CHAIN_BASE_PATH, f'{NFT_COMMITTEE_SCOPE_CHAIN_NAME}.conf'
    )
    logger.debug('Renaming %s to %s', after_boot_chain_path, after_migration_chain_path)
    if os.path.isfile(after_boot_chain_path):
        rename_chain_in_config(after_boot_chain_path, f'skale-{chain_name}', new_chain_name)
        if os.path.isfile(after_migration_chain_path):
            os.remove(after_boot_chain_path)
        else:
            rename_chain_file(after_boot_chain_path, after_migration_chain_path)


def reload_nft():
    run_cmd(['nft', '-f', '/etc/nftables.conf'])


def migrate_nftables_from_boot(chain_name: str):
    logger.info('Starting nftables migration from boot')
    migrate_nft_chain(chain_name=chain_name)
    logger.info('Reloading nftables rules')
    reload_nft()
    logger.info('Restart docker service')
    restart_docker_service()
