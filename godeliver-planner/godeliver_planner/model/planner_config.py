import collections
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator

from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.location import Location


class PlannerType(str, Enum):
    or_tools = 'OR_TOOLS'
    insertion_heuristic = 'INSERTION_HEURISTIC'
    jackpot_heuristic = 'JACKPOT_HEURISTIC'
    jackpot_or_tools = 'JACKPOT_OR_TOOLS'
    or_tools_insertion = 'OR_TOOLS_INSERTION'
    go_or_tools_insertion = 'GO_OR_TOOLS_INSERTION'
    opta_planner = 'OPTA_PLANNER'
    halns = 'HALNS'
    go_insertion_opta_planner = 'GO_INSERTION_OPTA_PLANNER'


class PenaltyDirection(str, Enum):
    earliness = "EARLINESS"
    lateness = "LATENESS"


class PenaltySpecification(BaseModel):
    is_hard: bool = False
    weight: int = 1
    offset: int = 0
    node_type: DeliveryEventType = DeliveryEventType.drop
    direction: PenaltyDirection = PenaltyDirection.lateness


class PlannerConfig(BaseModel):
    pickup_waiting_time: int = 0
    pickup_asap_tolerance: int = 1200
    drop_waiting_time: int = 240
    drop_asap_tolerance: int = 1200

    default_first_point_arrival_time: int = 1200
    default_first_point_arrival_distance: int = 10000
    default_courier_capacity: int = 10

    planner_type: PlannerType = PlannerType.or_tools
    use_previous_solution: bool = True
    use_courier_capacity: bool = False

    fixed_time_buffer: int = 600

    return_to_hub: bool = False
    hub_location: Location = None

    penalties: List[PenaltySpecification] = [
        PenaltySpecification(node_type=DeliveryEventType.pickup, direction=PenaltyDirection.earliness, is_hard=True),
        PenaltySpecification(node_type=DeliveryEventType.pickup, direction=PenaltyDirection.lateness),
        PenaltySpecification(node_type=DeliveryEventType.drop, direction=PenaltyDirection.earliness, weight=10),
        PenaltySpecification(node_type=DeliveryEventType.drop, direction=PenaltyDirection.lateness, weight=25),
        PenaltySpecification(node_type=DeliveryEventType.drop, direction=PenaltyDirection.lateness, weight=50, offset=1200),
        PenaltySpecification(node_type=DeliveryEventType.drop, direction=PenaltyDirection.lateness, weight=100, offset=2400)
    ]

    allow_wait_on_drop: bool = True

    def get_service_time(self, delivery_type: DeliveryEventType):
        if delivery_type == DeliveryEventType.pickup:
            return self.pickup_waiting_time
        elif delivery_type == DeliveryEventType.drop:
            return self.drop_waiting_time
        else:
            return 0

    def get_asap_tolerance(self, delivery_type: DeliveryEventType):
        if delivery_type == DeliveryEventType.pickup:
            return self.pickup_asap_tolerance
        elif delivery_type == DeliveryEventType.drop:
            return self.drop_asap_tolerance
        else:
            return 0

