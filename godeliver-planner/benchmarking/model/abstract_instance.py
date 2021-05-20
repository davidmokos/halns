import datetime
import json
import os
from abc import abstractmethod
from typing import List

from godeliver_planner.model.courier import Courier
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.plan import Plan


class AbstractInstance:

    def __init__(self, name: str, dataset_name: str, file: str, min_num_plans: int):
        self.name = name
        self.dataset_name = dataset_name
        self.file = file
        self.min_num_plans = min_num_plans
        self.data: (List[Delivery], List[Courier], int, List[Plan]) = None

    def load_data(self) -> (List[Delivery], List[Courier], int, List[Plan]):
        if not os.path.exists(self.file):
            raise FileNotFoundError(f"File {self.file} does not exits!")

        with open(self.file) as f:
            data = json.load(f)

        deliveries = []
        for o in data['deliveries']:
            delivery = Delivery.parse_obj(o)
            deliveries.append(delivery)

        self.data = deliveries, [], self.min_num_plans, None
        return self.data

    @abstractmethod
    def get_date_of_instance(self) -> datetime.datetime:
        raise NotImplementedError()
