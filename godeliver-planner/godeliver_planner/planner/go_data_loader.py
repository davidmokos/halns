from godeliver_planner.planner.abstract_planner import AbstractPlanner
from godeliver_planner.planner.adapters.golang_adapter import GoLangAdapter
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemSolution
from godeliver_planner.planner.plan_timetable.lp_plan_timetable_computer import LpPlanTimetableComputer
from godeliver_planner.routing.routing_base import RoutingBase


class GoDataLoader(AbstractPlanner):

    def __init__(self, routing: RoutingBase, instance_name: str):
        super().__init__(routing)
        self.plan_flow_computer = LpPlanTimetableComputer()
        self.instance_name = instance_name

    def get_name(self) -> str:
        return "Go Data Loader"

    def solve(self, vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:

        halns_solution = GoLangAdapter().load_computed_solution(self.instance_name)

        return self.optimize_times_in_solution(
            solution=halns_solution,
            vrp_instance=vrp_instance,
        )
