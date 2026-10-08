"""Provision and read the per-node admin API credential without logging it."""

import os
import pwd
import re
import secrets
import stat
import tempfile
from pathlib import Path

from node_cli.configs import ADMIN_API_TOKEN_PATH, G_CONF_USER


class APIAuthError(RuntimeError):
    pass


def read_api_token() -> str | None:
    try:
        fd = os.open(ADMIN_API_TOKEN_PATH, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        # Allows the updated CLI to talk to the old API during the first upgrade.
        return None
    except OSError as err:
        raise APIAuthError('Cannot read the admin API credential') from err
    try:
        with os.fdopen(fd, 'r', encoding='ascii') as token_file:
            info = os.fstat(token_file.fileno())
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
                raise ValueError('Invalid token file permissions')
            token = token_file.read(66).removesuffix('\n')
        if not re.fullmatch(r'[0-9a-f]{64}', token):
            raise ValueError('Invalid token file contents')
    except (OSError, ValueError) as err:
        raise APIAuthError(
            'Admin API credential must be a valid token in a mode 0600 file'
        ) from err
    return token


def ensure_api_token() -> None:
    """Publish a complete credential atomically; never overwrite an existing token."""
    owner = pwd.getpwnam(G_CONF_USER)
    if os.geteuid() not in (0, owner.pw_uid):
        raise APIAuthError('Only the configured node user or root can provision the API credential')

    path = Path(ADMIN_API_TOKEN_PATH)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Restrict the dedicated directory as well as the token. In particular, a
    # root-run CLI must leave it traversable by the configured node user.
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            if os.geteuid() == 0:
                os.fchown(directory_fd, owner.pw_uid, owner.pw_gid)
            os.fchmod(directory_fd, 0o700)
        finally:
            os.close(directory_fd)
    except OSError as err:
        raise APIAuthError('Cannot secure the admin API auth directory') from err

    if read_api_token() is not None:
        return

    fd, tmp_path = tempfile.mkstemp(prefix='.admin-api-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='ascii') as token_file:
            if os.geteuid() == 0:
                os.fchown(token_file.fileno(), owner.pw_uid, owner.pw_gid)
            token_file.write(secrets.token_hex(32) + '\n')
            token_file.flush()
            os.fsync(token_file.fileno())
        try:
            os.link(tmp_path, path)
        except FileExistsError:
            # Another CLI process may have provisioned it concurrently.
            pass
    finally:
        os.unlink(tmp_path)
    if read_api_token() is None:
        raise APIAuthError('Admin API credential disappeared during provisioning')


def get_api_headers() -> dict[str, str]:
    token = read_api_token()
    return {'Authorization': f'Bearer {token}'} if token is not None else {}
