import asyncio
import threading
from typing import Type, TypeVar, Optional

from pydantic.main import BaseModel
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

M = TypeVar('M', bound=BaseModel)
class YamlConfig(dict):

    def __init__(self, file_path):
        super().__init__()
        self.config_file = file_path
        with open(self.config_file, "r") as f:
            self.__config = load(f, Loader=Loader)

    def load(self, model: Type[M], section: str) -> Optional[M]:
        subsections = section.split('/')
        value = self.__config
        try:
            for subsection in subsections:
                value = value[subsection]
        except KeyError:
            return None
        return model(**value)

    def save(self, model: BaseModel, section: str) -> None:
        subsections = section.split('/')
        value = self.__config
        for subsection in subsections:
            if subsection not in value:
                value[subsection] = {}
            value = value[subsection]

        value.update(model.dict())

        with open(self.config_file, "w") as f:
            f.write(dump(self.__config, Dumper=Dumper))

    def __setitem__(self, key, item):
        self.__config[key] = item

    def __getitem__(self, key):
        return self.__config[key]

    def __repr__(self):
        return repr(self.__config)

    def __len__(self):
        return len(self.__config)

    def __delitem__(self, key):
        del self.__config[key]

    def clear(self):
        return self.__config.clear()

    def copy(self):
        return self.__config.copy()

    def has_key(self, k):
        return k in self.__config

    def update(self, *args, **kwargs):
        return self.__config.update(*args, **kwargs)

    def keys(self):
        return self.__config.keys()

    def values(self):
        return self.__config.values()

    def items(self):
        return self.__config.items()

    def pop(self, *args):
        return self.__config.pop(*args)

    def __cmp__(self, dict_):
        return self.__cmp__(self.__config, dict_)

    def __contains__(self, item):
        return item in self.__config

    def __iter__(self):
        return iter(self.__config)


class RunThread(threading.Thread):
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    def run(self):
        self.result = asyncio.run(self.func(*self.args, **self.kwargs))

def run_async(func, *args, **kwargs):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        thread = RunThread(func, args, kwargs)
        thread.start()
        thread.join()
        return thread.result
    else:
        return asyncio.run(func(*args, **kwargs))