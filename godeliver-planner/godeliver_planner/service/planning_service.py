from typing import List

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.model.courier import Courier
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.plan import Plan
from godeliver_planner.model.planner_config import PlannerType
from godeliver_planner.planner.abstract_planner import AbstractPlanner
from godeliver_planner.planner.insertion_heuristics_planner import InsertionHeuristicsPlanner
from godeliver_planner.planner.insertion_ortools_planner import InsertionHeuristicORToolsPlanner
from godeliver_planner.planner.insertion_ortools_planner import InsertionHeuristicORToolsPlanner
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.routing.routing_base import RoutingBase


class PlanningService:

    def __init__(self, routing: RoutingBase) -> None:
        super().__init__()
        self.routing = routing

    def _get_planner(self) -> AbstractPlanner:
        config = ConfigProvider.get_config()

        planner_type = config.planner_type

        if planner_type == PlannerType.or_tools:
            return ORToolsPlanner(routing=self.routing)
        elif planner_type == PlannerType.insertion_heuristic:
            return InsertionHeuristicsPlanner(routing=self.routing)
        elif planner_type == PlannerType.or_tools_insertion:
            return InsertionHeuristicORToolsPlanner(routing=self.routing)
        elif planner_type == PlannerType.go_or_tools_insertion:
            return InsertionHeuristicORToolsPlanner(routing=self.routing)
        else:
            return ORToolsPlanner(routing=self.routing)

    def create_plans(self,
                     deliveries: List[Delivery],
                     couriers: List[Courier],
                     min_number_of_plans: int,
                     previous_plans: List[Plan] = None):

        planner = self._get_planner()

        return planner.logistics_planner(
            deliveries=deliveries,
            couriers=couriers,
            min_number_of_plans=min_number_of_plans,
            previous_plans=previous_plans
        )
