from typing import Collection
from benchmarking.model.abstract_instance import AbstractInstance


class Dataset:
    def __init__(self, name: str, instances: Collection[AbstractInstance]) -> None:
        super().__init__()

        self.name: str = name

        self.instances = []
        for instance in instances:
            self.instances.append(instance)
            instance.dataset_name = self.name


