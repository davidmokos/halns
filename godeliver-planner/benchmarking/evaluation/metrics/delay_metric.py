from typing import List

from benchmarking.evaluation.metrics.abstract_metric import AbstractMetric
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.delivery_event import DeliveryEventType, DeliveryEvent
from godeliver_planner.model.plan import Plan


class DelayMetric(AbstractMetric):
    def __init__(self, delivery_event_type: DeliveryEventType) -> None:
        super().__init__()
        self.delivery_event_type = delivery_event_type

    def get_name(self) -> str:
        return f"📦 Delay of {self.delivery_event_type}"

    def get_id(self) -> str:
        return f"DELAY-{self.delivery_event_type.value}-METRIC"

    def _get_correct_mapping(self, pickup_mapping, drop_mapping):
        mapping = pickup_mapping if self.delivery_event_type == DeliveryEventType.pickup else drop_mapping
        return mapping

    def _get_correct_time_block(self, delivery: Delivery):
        time_block = delivery.pickup_time if self.delivery_event_type == DeliveryEventType.pickup else delivery.delivery_time
        return time_block

    def _compute_values(self, deliveries: List[Delivery], plans: List[Plan]) -> List[int]:
        pickup_mapping, drop_mapping = super()._get_delivery_to_events_mapping(deliveries, plans)

        mapping = self._get_correct_mapping(pickup_mapping, drop_mapping)

        ret = []
        for delivery in deliveries:
            if delivery.id not in mapping:
                continue

            event = mapping[delivery.id]

            delay = self._compute_delay(delivery, event)
            ret.append(delay / 60)

        return ret

    def _compute_delay(self, delivery: Delivery, event: DeliveryEvent) -> int:
        arrival_time = event.event_time.from_time
        expected_latest_arrival = self._get_correct_time_block(delivery).get_to_time()

        if arrival_time <= expected_latest_arrival:
            return 0
        return arrival_time - expected_latest_arrival

