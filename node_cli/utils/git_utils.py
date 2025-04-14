#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#
#   Copyright (C) 2021 SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import logging

from git.repo.base import Repo
from node_cli.utils.helper import error_exit

logger = logging.getLogger(__name__)


def check_is_branch(repo: Repo, ref_name: str) -> bool:
    return ref_name in (branch.name for branch in repo.heads)


def clone_repo(repo_url: str, repo_path: str, ref_name: str) -> None:
    try:
        logger.info(f'Cloning {repo_url} → {repo_path}')
        Repo.clone_from(repo_url, repo_path)
        fetch_pull_repo(repo_path, ref_name)
    except Exception as e:
        error_exit(f'Unexpected error cloning repository: {str(e)}')


def sync_repo(repo_url: str, repo_path: str, ref_name: str) -> None:
    """
    Sync Git repository by cloning if it doesn't exist locally. If it exists, fetch latest changes.
    """

    logger.info(f'Sync repo {repo_url} → {repo_path}')
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        clone_repo(repo_url, repo_path, ref_name)
    else:
        fetch_pull_repo(repo_path, ref_name)


def fetch_pull_repo(repo_path: str, ref_name: str) -> None:
    """Fetch latest changes and checkout/pull specific git reference."""

    try:
        repo = Repo(repo_path)
        repo_name = os.path.basename(repo.working_dir)

        logger.info(f'Fetching latest changes for {repo_name}')
        repo.remotes.origin.fetch()

        logger.info(f'Checking out {ref_name} in {repo_name}')
        repo.git.checkout(ref_name)

        if check_is_branch(repo, ref_name):
            logger.info(f'Pulling latest changes for branch {ref_name}')
            repo.remotes.origin.pull()

    except Exception as e:
        error_exit(f'Repository operation failed: {str(e)}')
