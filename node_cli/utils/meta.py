import abc
import json
import os
from dataclasses import dataclass

from node_cli.configs import META_FILEPATH

DEFAULT_VERSION = '1.0.0'
DEFAULT_CONFIG_STREAM = '1.1.0'
DEFAULT_DOCKER_LVMPY_VERSION = '1.0.0'
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


@dataclass
class CliMeta(CliMetaBase):
    docker_lvmpy_version: str | None = DEFAULT_DOCKER_LVMPY_VERSION

    def asdict(self) -> dict:
        return {
            'version': self.version,
            'config_stream': self.config_stream,
            'docker_lvmpy_version': self.docker_lvmpy_version,
            'os_id': self.os_id,
            'os_version': self.os_version,
        }


@dataclass
class FairCliMeta(CliMetaBase):
    def asdict(self) -> dict:
        return {
            'version': self.version,
            'config_stream': self.config_stream,
            'os_id': self.os_id,
            'os_version': self.os_version,
        }


class BaseCliMetaManager(abc.ABC):
    def __init__(self, meta_filepath: str = META_FILEPATH) -> None:
        self.meta_filepath = meta_filepath

    def _get_plain_meta(self) -> dict:
        if not os.path.isfile(self.meta_filepath):
            return {}
        with open(self.meta_filepath) as meta_file:
            return json.load(meta_file)

    @abc.abstractmethod
    def get_meta_info(self, raw: bool = False) -> CliMetaBase | dict | None:
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
    def get_meta_info(self, raw: bool = False) -> CliMeta | dict | None:
        plain_meta = self._get_plain_meta()
        if not raw and not plain_meta:
            return None
        allowed_fields = set(CliMeta.__dataclass_fields__.keys())
        clean_plain_meta = {k: v for k, v in plain_meta.items() if k in allowed_fields}

        if raw:
            return clean_plain_meta
        return CliMeta(**clean_plain_meta)

    def compose_default_meta(self) -> CliMeta:
        return CliMeta(
            version=DEFAULT_VERSION,
            docker_lvmpy_version=DEFAULT_DOCKER_LVMPY_VERSION,
            config_stream=DEFAULT_CONFIG_STREAM,
            os_id=DEFAULT_OS_ID,
            os_version=DEFAULT_OS_VERSION,
        )

    def update_meta(
        self,
        version: str,
        config_stream: str,
        docker_lvmpy_version: str | None,
        os_id: str,
        os_version: str,
    ) -> None:
        self.ensure_meta()
        meta = CliMeta(
            version,
            config_stream,
            os_id,
            os_version,
            docker_lvmpy_version,
        )
        self.save_meta(meta)


class FairCliMetaManager(BaseCliMetaManager):
    def get_meta_info(self, raw: bool = False) -> FairCliMeta | dict | None:
        plain_meta = self._get_plain_meta()
        if not raw and not plain_meta:
            return None
        allowed_fields = set(FairCliMeta.__dataclass_fields__.keys())
        clean_plain_meta = {k: v for k, v in plain_meta.items() if k in allowed_fields}
        if raw:
            return clean_plain_meta
        return FairCliMeta(**clean_plain_meta)

    def compose_default_meta(self) -> FairCliMeta:
        return FairCliMeta(
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
        meta = FairCliMeta(version, config_stream, os_id, os_version)
        self.save_meta(meta)
