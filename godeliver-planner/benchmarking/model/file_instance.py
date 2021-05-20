from datetime import datetime

from benchmarking.model.abstract_instance import AbstractInstance
from godeliver_planner.model.delivery import Delivery


class FileInstance(AbstractInstance):

    def __init__(self, path: str, min_num_plans: int, name: str, dataset_name: str) -> None:
        file = f'./../data/{path}'
        super().__init__(name, dataset_name, file, min_num_plans)

    def get_date_of_instance(self) -> datetime:
        if not self.data:
            raise AssertionError("You must call load_data() first!")

        deliveries = self.data[0]
        first_delivery: Delivery = deliveries[0]
        return datetime.fromtimestamp(first_delivery.pickup_time.from_time).replace(hour=0, minute=0, second=0)
