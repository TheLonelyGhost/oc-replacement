import logging
import platform
import os
from typing import Any, Dict, List, Iterator, Union

from ruamel import yaml


_missing = object()
_default_kube_config = os.path.expanduser('~/.kube/config')

if platform.system() == 'Windows':
    _path_separator = ';'
else:
    _path_separator = ':'


class KubeConfigData(object):
    def __init__(self, filename: str):
        self._filename = filename
        if filename != 'COMPUTED':
            with open(filename, 'r', encoding='utf-8') as f:
                self._yaml = yaml.load(f, Loader=yaml.RoundTripLoader)
        else:
            self._yaml = {}
        self.is_dirty = False

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def value(self) -> Any:
        return self._yaml

    def is_from_file(self, other):
        if not isinstance(other, KubeConfigData):
            return NotImplemented

        return self.filename == other.filename

    def persist(self):
        logging.info('Writing file {!r}'.format(self.filename))
        with open(self.filename, 'w', encoding='utf-8') as f:
            yaml.dump(self._yaml, f, Dumper=yaml.RoundTripDumper)
        self.is_dirty = False


class KubeConfigDataSnippet(KubeConfigData):
    def __init__(self, parent: KubeConfigData, data: Union[Dict, List], dirty=_missing):
        self._filename = parent.filename
        self._yaml = data
        if parent.filename == 'COMPUTED':
            self.is_dirty = False
        elif dirty == _missing:
            self.is_dirty = parent.is_dirty
        else:
            self.is_dirty = dirty

    def persist(self):
        raise NotImplementedError()


class KubeConfig(object):
    def __init__(self, config_files: List[str] = [_default_kube_config]):
        self.configs: List[KubeConfigData] = []
        for filename in config_files:
            if not filename:
                continue
            if not os.path.exists(filename):
                continue
            self.configs.append(KubeConfigData(filename))

    @classmethod
    def find_from_env(cls):
        path = os.environ.get('KUBECONFIG', _default_kube_config)
        files = path.split(_path_separator)
        return cls(config_files=files)

    @property
    def data(self) -> KubeConfigDataSnippet:
        obj: Dict[str, Any] = {}
        # This is reversed order since KUBECONFIG dictates first definition wins
        for config in reversed(self.configs):
            obj.update(config._yaml)

        source_obj = KubeConfigData(filename='COMPUTED')

        return KubeConfigDataSnippet(parent=source_obj, data=obj)

    def persist(self, snippet: KubeConfigData):
        for config in self.each_config():
            if config.is_from_file(snippet):
                if config.is_dirty or snippet.is_dirty:
                    config.persist()
                else:
                    # Found the config, so don't raise error, but nothing to do
                    pass
                return

        raise ValueError('Source config for {!r} was not found'.format(snippet))

    def each_config(self) -> Iterator[KubeConfigData]:
        for config in self.configs:
            yield config
