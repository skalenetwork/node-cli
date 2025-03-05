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
from git.exc import GitCommandError, GitError
from node_cli.utils.exit_codes import CLIExitCodes
from node_cli.utils.helper import error_exit

logger = logging.getLogger(__name__)


def check_is_branch(repo: Repo, ref_name: str) -> bool:
    """Check if the given reference name is a valid git branch."""
    if not repo or not isinstance(repo, Repo):
        raise ValueError('Invalid repository object')
    if not ref_name or not isinstance(ref_name, str):
        raise ValueError('Invalid reference name')

    try:
        # Verify if ref_name exists as a branch using git show-ref
        repo.git.show_ref('--verify', f'refs/heads/{ref_name}')
        logger.debug(f'{ref_name} is a branch')
        return True
    except GitCommandError:
        # Expected error when reference is not found
        logger.debug(f'{ref_name} is not a branch')
        return False
    except GitError as e:
        # Git-specific errors (permissions, config, etc)
        logger.error(f'Git error checking branch: {str(e)}')
        raise RuntimeError(f'Git error checking branch: {str(e)}') from e
    except Exception as e:
        # Unexpected system errors
        logger.error(f'Unexpected error checking branch: {str(e)}')
        raise RuntimeError(f'Unexpected error checking branch: {str(e)}') from e


def clone_repo(repo_url: str, repo_path: str, ref_name: str) -> None:
    """Clone a git repository and checkout specified reference."""
    if not all([repo_url, repo_path, ref_name]):
        error_exit('Empty repository URL, path or reference', CLIExitCodes.FAILURE)
    if not all(isinstance(x, str) for x in [repo_url, repo_path, ref_name]):
        error_exit('Invalid input types', CLIExitCodes.FAILURE)

    try:
        logger.info(f'Cloning {repo_url} → {repo_path}')
        Repo.clone_from(repo_url, repo_path)
        fetch_pull_repo(repo_path, ref_name)
    except GitError as e:
        error_exit(
            f'Git error cloning repository: {str(e)}', CLIExitCodes.OPERATION_EXECUTION_ERROR
        )
    except Exception as e:
        error_exit(f'Unexpected error cloning repository: {str(e)}', CLIExitCodes.FAILURE)


def sync_repo(repo_url: str, repo_path: str, ref_name: str) -> None:
    """Sync Git repository by cloning if not exists or fetching latest changes."""
    if not all([repo_url, repo_path, ref_name]):
        error_exit('Empty repository URL, path or reference', CLIExitCodes.FAILURE)
    if not all(isinstance(x, str) for x in [repo_url, repo_path, ref_name]):
        error_exit('Invalid input types', CLIExitCodes.FAILURE)

    logger.info(f'Sync repo {repo_url} → {repo_path}')
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        clone_repo(repo_url, repo_path, ref_name)
    else:
        fetch_pull_repo(repo_path, ref_name)


def fetch_pull_repo(repo_path: str, ref_name: str) -> None:
    """Fetch latest changes and checkout/pull specific git reference."""
    # Validate inputs
    if not repo_path or not isinstance(repo_path, str):
        error_exit('Invalid repository path', CLIExitCodes.FAILURE)
    if not ref_name or not isinstance(ref_name, str):
        error_exit('Invalid reference name', CLIExitCodes.FAILURE)

    try:
        # Initialize repo and get name for logging
        repo = Repo(repo_path)
        repo_name = os.path.basename(repo.working_dir)

        # Fetch latest changes
        logger.info(f'Fetching latest changes for {repo_name}')
        repo.remotes.origin.fetch()

        # Checkout specified reference
        logger.info(f'Checking out {ref_name} in {repo_name}')
        repo.git.checkout(ref_name)

        # Pull latest changes if ref is a branch
        if check_is_branch(repo, ref_name):
            logger.info(f'Pulling latest changes for branch {ref_name}')
            repo.remotes.origin.pull()

    except GitError as e:
        error_exit(f'Git operation failed: {str(e)}', CLIExitCodes.OPERATION_EXECUTION_ERROR)
    except Exception as e:
        error_exit(f'Repository operation failed: {str(e)}', CLIExitCodes.FAILURE)
