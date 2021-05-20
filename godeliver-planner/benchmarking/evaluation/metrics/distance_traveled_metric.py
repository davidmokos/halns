from typing import List

from benchmarking.evaluation.metrics.abstract_metric import AbstractMetric
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.plan import Plan


class DistanceTraveledMetric(AbstractMetric):
    def get_name(self) -> str:
        return "Distance traveled"

    def get_id(self) -> str:
        return f"DISTANCE-TRAVELED-METRIC"

    def _compute_values(self, deliveries: List[Delivery], plans: List[Plan]) -> List[int]:
        ret = []
        for plan in plans:
            ret.append(plan.distance/1000)

        return ret

    def get_unit(self) -> str:
        return "km"


