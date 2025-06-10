import abc
import json
import os
from dataclasses import dataclass
from typing import Optional

from node_cli.configs import META_FILEPATH

DEFAULT_VERSION = '1.0.0'
DEFAULT_CONFIG_STREAM = '1.1.0'
DEFAULT_DOCKER_LVMPY_STREAM = '1.0.0'
DEFAULT_OS_ID = 'ubuntu'
DEFAULT_OS_VERSION = '18.04'


@dataclass
class CliMetaBase(abc.ABC):
    version: str = DEFAULT_VERSION
    config_stream: str = DEFAULT_CONFIG_STREAM
    os_id: str = DEFAULT_OS_ID
    os_version: str = DEFAULT_OS_VERSION

    @abc.abstractmethod
    def asdict(self) -> dict:
        pass


class CliMeta(CliMetaBase):
    docker_lvmpy_stream: str = DEFAULT_DOCKER_LVMPY_STREAM

    def asdict(self) -> dict:
        return {
            'version': self.version,
            'config_stream': self.config_stream,
            'docker_lvmpy_stream': self.docker_lvmpy_stream,
            'os_id': self.os_id,
            'os_version': self.os_version,
        }


class MirageCliMeta(CliMetaBase):
    def asdict(self) -> dict:
        return {
            'version': self.version,
            'config_stream': self.config_stream,
            'os_id': self.os_id,
            'os_version': self.os_version,
        }


class BaseCliMetaManager(abc.ABC):
    def __init__(self, meta_filepath: str = META_FILEPATH):
        self.meta_filepath = meta_filepath

    def _get_plain_meta(self) -> dict:
        if not os.path.isfile(self.meta_filepath):
            return {}
        with open(self.meta_filepath) as meta_file:
            return json.load(meta_file)

    @abc.abstractmethod
    def get_meta_info(self, raw: bool = False) -> CliMetaBase | dict:
        pass

    def save_meta(self, meta: CliMetaBase) -> None:
        with open(self.meta_filepath, 'w') as meta_file:
            json.dump(meta.asdict(), meta_file)

    @abc.abstractmethod
    def compose_default_meta(self) -> CliMetaBase:
        pass

    def ensure_meta(self, meta: CliMetaBase | None = None) -> None:
        if not self.get_meta_info():
            meta = meta or self.compose_default_meta()
            self.save_meta(meta)

    @abc.abstractmethod
    def update_meta(self, *args, **kwargs) -> None:
        pass


class CliMetaManager(BaseCliMetaManager):
    def get_meta_info(self, raw: bool = False) -> CliMeta | dict:
        plain_meta = self._get_plain_meta()
        required_fields = set(CliMeta.__dataclass_fields__.keys())
        clean_plain_meta = {k: v for k, v in plain_meta.items() if k in required_fields}
        if raw:
            return clean_plain_meta
        return CliMeta(**clean_plain_meta)

    def compose_default_meta(self) -> CliMeta:
        return CliMeta(
            version=DEFAULT_VERSION,
            docker_lvmpy_stream=DEFAULT_DOCKER_LVMPY_STREAM,
            config_stream=DEFAULT_CONFIG_STREAM,
            os_id=DEFAULT_OS_ID,
            os_version=DEFAULT_OS_VERSION,
        )

    def update_meta(
        self,
        version: str,
        config_stream: str,
        docker_lvmpy_stream: Optional[str],
        os_id: str,
        os_version: str,
    ) -> None:
        self.ensure_meta()
        meta = CliMeta(version, config_stream, docker_lvmpy_stream, os_id, os_version)
        self.save_meta(meta)


class MirageCliMetaManager(BaseCliMetaManager):
    def get_meta_info(self, raw: bool = False) -> MirageCliMeta | dict:
        plain_meta = self._get_plain_meta()
        required_fields = set(MirageCliMeta.__dataclass_fields__.keys())
        clean_plain_meta = {k: v for k, v in plain_meta.items() if k in required_fields}
        if raw:
            return clean_plain_meta
        return MirageCliMeta(**clean_plain_meta)

    def compose_default_meta(self) -> MirageCliMeta:
        return MirageCliMeta(
            version=DEFAULT_VERSION,
            config_stream=DEFAULT_CONFIG_STREAM,
            os_id=DEFAULT_OS_ID,
            os_version=DEFAULT_OS_VERSION,
        )

    def update_meta(
        self,
        version: str,
        config_stream: str,
        os_id: str,
        os_version: str,
    ) -> None:
        self.ensure_meta()
        meta = MirageCliMeta(version, config_stream, os_id, os_version)
        self.save_meta(meta)
