from typing import List

from benchmarking.evaluation.metrics.abstract_metric import AbstractMetric
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.plan import Plan


class TimeSpentMetric(AbstractMetric):
    def get_name(self) -> str:
        return "Time spent"

    def get_id(self) -> str:
        return f"TIME-SPENT-METRIC"

    def _compute_values(self, deliveries: List[Delivery], plans: List[Plan]) -> List[int]:
        ret = []
        for plan in plans:
            if len(plan.delivery_events) == 0:
                continue

            start = plan.delivery_events[0].event_time.to_time
            end = plan.delivery_events[-1].event_time.from_time
            ret.append((end - start) / 60)

        return ret



