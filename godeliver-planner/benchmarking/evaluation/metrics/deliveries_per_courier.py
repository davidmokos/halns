from typing import List

from benchmarking.evaluation.metrics.abstract_metric import AbstractMetric
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.plan import Plan


class DeliveriesPerCourierMetric(AbstractMetric):
    def get_name(self) -> str:
        return "Number of 📦 per 👷"

    def get_id(self) -> str:
        return f"DELIVERIES-PER-COURIER-METRIC"

    def get_unit(self) -> str:
        return "pcs"

    def _compute_values(self, deliveries: List[Delivery], plans: List[Plan]) -> List[int]:
        ret = []
        for plan in plans:
            no_deliveries = len(set(plan.delivery_order_ids))
            ret.append(no_deliveries)
        return ret

