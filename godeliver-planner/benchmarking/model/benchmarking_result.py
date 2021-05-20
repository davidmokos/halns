from typing import Any

from pydantic.main import BaseModel

from benchmarking.evaluation.metrics.abstract_metric import MetricResult
from godeliver_planner.helper.timestamp_helper import TimestampHelper


class BenchmarkingResult(BaseModel):

    model_name: str
    model_version: str

    dataset_name: str
    instance_name: str

    metric_name: str
    metric_average: float
    metric_max: float
    metric_min: float
    metric_total: float

    evaluated_on: str
    time_budget: int

    @classmethod
    def from_metric_result(cls, metric_name: str, metric_result: MetricResult,
                           model_name: str, model_version: str,
                           dataset_name: str, instance_name: str,
                           time_budget: int):
        return cls(
            model_name=model_name,
            model_version=model_version,
            dataset_name=dataset_name,
            instance_name=instance_name,
            metric_name=metric_name,
            metric_average=metric_result.average,
            metric_max=metric_result.max,
            metric_min=metric_result.min,
            metric_total=metric_result.total,
            time_budget=time_budget,
            evaluated_on=TimestampHelper.current_day_in_our_format()
        )

    def get_id(self) -> str:
        return f"{self.dataset_name}_{self.instance_name}_{self.model_name}_{self.model_version}_{self.metric_name}"

