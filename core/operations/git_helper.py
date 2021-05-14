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
import shutil
import logging

from git.repo.base import Repo
from git.exc import GitCommandError


logger = logging.getLogger(__name__)


def check_is_branch(repo: Repo, ref_name: str) -> bool:
    try:
        repo.git.show_ref('--verify', f'refs/heads/{ref_name}')
        logger.debug(f'{ref_name} is branch')
        return True
    except GitCommandError:
        logger.debug(f'{ref_name} is not branch')
        return False


def sync_repo(repo_url: str, repo_path: str, ref_name: str) -> None:
    logger.info(f'Sync repo {repo_url} → {repo_path}')
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        logger.info(f'Cloning {repo_url} → {repo_path}')
        repo = Repo.clone_from(repo_url, repo_path)
    else:
        repo = Repo(repo_path)
    logger.info(f'Updating {repo_path} sources')
    fetch_pull_repo(repo, ref_name)


def fetch_pull_repo(repo: Repo, ref_name: str) -> None:
    repo_name = os.path.basename(repo.working_dir)
    logger.info(f'Fetching {repo_name} changes')
    repo.remotes.origin.fetch()
    logger.info(f'Checkouting docker-lvmpy to {ref_name}')
    repo.git.checkout(ref_name)
    if check_is_branch(repo, ref_name):
        repo.remotes.origin.pull()


def rm_local_repo(repo_path: str) -> None:
    if os.path.exists(repo_path):
        logger.info(f'{repo_path} exists, removing...')
        shutil.rmtree(repo_path)
    else:
        logger.info(f'{repo_path} doesn\'t exist, skipping...')
