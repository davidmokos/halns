from typing import List

from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.plan import Plan
from abc import ABC, abstractmethod


class MetricResult:
    def __init__(self, average: float, max_v: int, min_v: int, total: int) -> None:
        super().__init__()
        self.average = average
        self.max = max_v
        self.min = min_v
        self.total = total


class AbstractMetric(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_id(self) -> str:
        pass

    def get_unit(self) -> str:
        return "min"

    @abstractmethod
    def _compute_values(self, deliveries: List[Delivery], plans: List[Plan]) -> List[int]:
        pass

    @staticmethod
    def _get_delivery_to_events_mapping(deliveries: List[Delivery], plans: List[Plan]) -> (dict, dict):
        delivery_id_to_drop_event = {}
        delivery_id_to_pickup_event = {}

        for idx, plan in enumerate(plans):
            for delivery_event in plan.delivery_events:
                if delivery_event.type == DeliveryEventType.pickup:
                    for delivery_order_id in delivery_event.delivery_order_ids:
                        delivery_id_to_pickup_event[delivery_order_id] = delivery_event

                elif delivery_event.type == DeliveryEventType.drop:
                    for delivery_order_id in delivery_event.delivery_order_ids:
                        delivery_id_to_drop_event[delivery_order_id] = delivery_event

        return delivery_id_to_pickup_event, delivery_id_to_drop_event

    def compute(self, deliveries: List[Delivery], plans: List[Plan]) -> MetricResult:
        values = self._compute_values(deliveries, plans)
        return self._get_results(values)

    @staticmethod
    def _get_results(values: List[int]) -> MetricResult:
        total = sum(values)
        average = total / len(values) if len(values) > 0 else 0
        min_v = min(values) if len(values) > 0 else 0
        max_v = max(values) if len(values) > 0 else 0
        return MetricResult(average=average, max_v=max_v, min_v=min_v, total=total)
