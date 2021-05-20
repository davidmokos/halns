from godeliver_planner.model.planner_config import PlannerType
from godeliver_planner.planner.abstract_planner import AbstractPlanner
from godeliver_planner.planner.adapters.golang_adapter import GoLangAdapter
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemSolution
from godeliver_planner.planner.plan_timetable.lp_plan_timetable_computer import LpPlanTimetableComputer
from godeliver_planner.routing.routing_base import RoutingBase


class HALNSPlanner(AbstractPlanner):

    def __init__(self, routing: RoutingBase):
        super().__init__(routing)
        self.plan_flow_computer = LpPlanTimetableComputer()

    def get_name(self) -> str:
        return PlannerType.halns.value

    def solve(self, vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:

        halns_solution = GoLangAdapter().halns_impl(vrp_instance)

        return self.optimize_times_in_solution(
            solution=halns_solution,
            vrp_instance=vrp_instance,
        )
