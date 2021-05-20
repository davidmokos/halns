import datetime
from benchmarking.model.abstract_instance import AbstractInstance


class MetadataInstance(AbstractInstance):

    def __init__(self, year: int, month: int, day: int, dataset_name: str, min_num_plans: int = 1, name: str = None) -> None:

        self.day: int = day
        self.month: int = month
        self.year: int = year

        if not name:
            name = f"{self.year}-{self.month:02d}-{self.day:02d}"

        file = f'./../data/{dataset_name}/{dataset_name}_export_{name}.json'

        super().__init__(name, dataset_name, file, min_num_plans)

    def get_date_of_instance(self) -> datetime.datetime:
        return datetime.datetime(year=self.year, month=self.month, day=self.day)
