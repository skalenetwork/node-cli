import glob
import logging
import os
from pathlib import Path

from node_cli.utils.helper import run_cmd

logger = logging.getLogger(__name__)

NFT_CHAIN_BASE_PATH = '/etc/nft.conf.d/skale/chains'
NFT_COMMITTEE_SCOPE_CHAIN_PATH = 'mirage-committee.conf'


class NoLegacyNFTChainConfigError(Exception):
    pass


def move_chain_to_new_name() -> None:
    after_boot_chain_path = glob.glob(os.path.join(NFT_CHAIN_BASE_PATH, '*'))[0]
    new_path = os.path.join(NFT_CHAIN_BASE_PATH, NFT_COMMITTEE_SCOPE_CHAIN_PATH)
    if Path(after_boot_chain_path).exists():
        raise NoLegacyNFTChainConfigError(f'File {after_boot_chain_path} does not exists')
    Path(after_boot_chain_path).rename(Path(new_path))


def reload_nft():
    run_cmd(['nft', '-f', '/etc/nftables.conf'])


def migrate_nftables_from_boot():
    logger.info('Starting nftables migration from boot')
    move_chain_to_new_name()
    logger.info('Reloading nftables rules')
    reload_nft()
