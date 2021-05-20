import datetime
import os
from typing import List
import subprocess

from benchmarking.benchmarking_common import METRICS, n20_DATASET, n50_DATASET, \
    n100_DATASET, n500_DATASET, n200_DATASET
from benchmarking.database.firebase_manager import FirebaseManager
from benchmarking.model.abstract_instance import AbstractInstance
from benchmarking.model.benchmarking_result import BenchmarkingResult
from benchmarking.model.dataset import Dataset
from benchmarking.visualisation.plan_visualisation import PlanVisualisation
from godeliver_planner.helper.timestamp_helper import TimestampHelper
from godeliver_planner.planner.abstract_planner import AbstractPlanner
from godeliver_planner.planner.halns_planner import HALNSPlanner
from godeliver_planner.planner.insertion_heuristics_planner import InsertionHeuristicsPlanner
from godeliver_planner.planner.insertion_ortools_planner import InsertionHeuristicORToolsPlanner
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.routing.osrm_service import OSRMRouting


def get_current_commit():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'])[:-1]


def evaluate_model_on_instance(model: AbstractPlanner, instance: AbstractInstance) -> List[BenchmarkingResult]:
    results = []

    deliveries, couriers, n, previous_plans = instance.load_data()

    now = instance.get_date_of_instance() + datetime.timedelta(hours=8)
    TimestampHelper.set_current_timestamp(int(now.timestamp()))

    plans = model.logistics_planner(deliveries=deliveries, couriers=couriers,
                                    min_number_of_plans=n, previous_plans=previous_plans)

    PlanVisualisation.visualise_orders(deliveries, plans)

    for metric in METRICS:
        metric_result = metric.compute(deliveries=deliveries, plans=plans)

        benchmarking_result = BenchmarkingResult.from_metric_result(
            model_name=model.get_name(),
            model_version=get_current_commit(),
            dataset_name=instance.dataset_name,
            instance_name=instance.name,
            metric_name=metric.get_id(),
            metric_result=metric_result,
            time_budget=120  # TODO this should be taken from the settings
        )
        results.append(benchmarking_result)

    return results


def evaluate_model_on_dataset(dataset: Dataset, model: AbstractPlanner) -> List[BenchmarkingResult]:
    results = []

    for instance in dataset.instances:
        results_for_instance = evaluate_model_on_instance(model=model, instance=instance)
        results.extend(results_for_instance)
        store_results_to_firebase(results_for_instance)

    return results


def store_results_to_firebase(results: List[BenchmarkingResult]):
    firebase_key = os.environ.get('FIREBASE_CONFIG',
                                  os.path.join('config', 'godeliver-benchmarking-firebase-key.json'))

    manager = FirebaseManager(firebase_key)
    for result in results:
        data = result.dict()
        manager.database.collection(u'planner').document(result.get_id()).set(data)


def run_benchmarking():
    datasets = [n20_DATASET, n50_DATASET, n100_DATASET, n200_DATASET, n500_DATASET]
    routing = OSRMRouting()
    models = [
        InsertionHeuristicsPlanner(routing),
        HALNSPlanner(routing),
        InsertionHeuristicORToolsPlanner(routing),
        ORToolsPlanner(routing)
    ]

    for dataset in datasets:
        for model in models:
            results = evaluate_model_on_dataset(model=model, dataset=dataset)
            print(f"---- FINISHED EVALUATION {dataset.name} with {model.get_name()} ----")


if __name__ == '__main__':
    run_benchmarking()
