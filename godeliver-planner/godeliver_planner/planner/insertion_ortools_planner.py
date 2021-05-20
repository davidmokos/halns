import copy
from datetime import datetime
from godeliver_planner.model.planner_config import PlannerType
from godeliver_planner.planner.abstract_planner import AbstractPlanner
from godeliver_planner.planner.insertion_heuristics_planner import InsertionHeuristicsPlanner
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemSolution
from godeliver_planner.routing.routing_base import RoutingBase


class InsertionHeuristicORToolsPlanner(AbstractPlanner):

    def get_name(self) -> str:
        return PlannerType.go_or_tools_insertion.value

    def __init__(self, routing: RoutingBase):
        super().__init__(routing)
        self.ortools_planner = ORToolsPlanner(routing=routing)
        self.insertion_planner = InsertionHeuristicsPlanner(routing=routing)

    def solve(self, vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:
        start_time = datetime.now()
        original_vrp_instance = copy.deepcopy(vrp_instance)
        solution = self.insertion_planner.solve(vrp_instance)
        run_time = datetime.now() - start_time

        original_vrp_instance.time_limit -= run_time.seconds

        r = []
        for plan in solution.plans:
            r.append(plan[1:-1])
        original_vrp_instance.previous_plans = r

        return self.ortools_planner.solve(original_vrp_instance)
