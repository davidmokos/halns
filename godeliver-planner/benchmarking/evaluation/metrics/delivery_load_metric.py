from typing import List

from benchmarking.evaluation.metrics.abstract_metric import AbstractMetric
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.plan import Plan


class NoPackagesPerPickup(AbstractMetric):
    def get_name(self) -> str:
        return "No of 📦 per 🆙"

    def get_id(self) -> str:
        return f"DELIVERIES-PER-PICKUP-METRIC"

    def _compute_values(self, deliveries: List[Delivery], plans: List[Plan]) -> List[int]:
        ret = []
        for plan in plans:

            for delivery_event in plan.delivery_events:
                if delivery_event.type == DeliveryEventType.pickup:
                    ret.append(len(delivery_event.delivery_order_ids))

        return ret

    def get_unit(self) -> str:
        return "pcs"


