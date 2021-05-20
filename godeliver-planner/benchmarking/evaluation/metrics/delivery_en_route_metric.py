from typing import List

from benchmarking.evaluation.metrics.abstract_metric import AbstractMetric
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.plan import Plan


class DeliveryEnRouteMetric(AbstractMetric):
    def get_name(self) -> str:
        return "🚚 Delivery En Route Time"

    def get_id(self) -> str:
        return f"DELIVERY-EN-ROUTE-METRIC"

    def _compute_values(self, deliveries: List[Delivery], plans: List[Plan]) -> List[int]:
        pickup_mapping, drop_mapping = super()._get_delivery_to_events_mapping(deliveries, plans)

        ret = []
        for delivery in deliveries:
            if delivery.id not in pickup_mapping or delivery.id not in drop_mapping:
                continue

            pickup_event = pickup_mapping[delivery.id]
            drop_event = drop_mapping[delivery.id]

            delay = self._compute_en_route_time(pickup_event, drop_event)
            ret.append(delay / 60)

        return ret

    @staticmethod
    def _compute_en_route_time(pickup_event, drop_event):
        return drop_event.event_time.to_time - pickup_event.event_time.get_to_time()