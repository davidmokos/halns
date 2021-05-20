from godeliver_planner.model.planner_config import PlannerType
from godeliver_planner.planner.abstract_planner import AbstractPlanner
from godeliver_planner.planner.adapters.golang_adapter import GoLangAdapter
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemSolution
from godeliver_planner.planner.plan_timetable.lp_plan_timetable_computer import LpPlanTimetableComputer
from godeliver_planner.routing.routing_base import RoutingBase


class InsertionHeuristicsPlanner(AbstractPlanner):

    def __init__(self, routing: RoutingBase):
        super().__init__(routing)
        self.plan_flow_computer = LpPlanTimetableComputer()

    def solve(self, vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:

        go_vrp_solution = GoLangAdapter().insertion_heuristics_impl(vrp_instance)

        return self.optimize_times_in_solution(
            solution=go_vrp_solution,
            vrp_instance=vrp_instance,
        )

    def get_name(self) -> str:
        return PlannerType.insertion_heuristic.value
