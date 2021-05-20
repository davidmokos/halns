import json
import os
from datetime import datetime
from typing import List

from godeliver_planner.model.courier import Courier
from godeliver_planner.model.delivery import Delivery


class LogHelper:

    @staticmethod
    def log_failed_to_solve(deliveries: List[Delivery], couriers: List[Courier], min_number_of_plans: int,
                            exception: Exception):

        data = {
            'deliveries': [delivery.dict() for delivery in deliveries],
            'couriers': [courier.dict() for courier in couriers],
            'min_number_of_plans': min_number_of_plans,
            'exception': str(exception)
        }

        now = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

        root_path = os.getcwd()

        path = os.path.join(root_path, 'logs')
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, f"failed_instance_{now}.json")

        with open(path, "w") as f:
            json.dump(data, f)

