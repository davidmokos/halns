import json
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, Optional, Dict

import numpy as np

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.helper.timestamp_helper import TimestampHelper
from godeliver_planner.model.courier import Courier
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.plan import Plan
from godeliver_planner.model.planner_config import PenaltySpecification, PenaltyDirection
from godeliver_planner.routing.osrm_service import OSRMProfile
from godeliver_planner.routing.routing_base import RoutingBase

MAX_TIMESTAMP_VALUE = 2147483647


class TimeWindowConstraint:

    def __init__(self, node: int, is_hard: bool = False, from_time: int = 0, to_time: int = MAX_TIMESTAMP_VALUE,
                 weight: int = 1) -> None:
        self.node = node
        self.is_hard = is_hard
        self.from_time = from_time
        self.to_time = to_time
        self.weight = weight

    def has_upper_bound(self) -> bool:
        return self.to_time is not None and self.to_time < MAX_TIMESTAMP_VALUE

    def has_lower_bound(self) -> bool:
        return self.from_time is not None and self.from_time > 0

    def __str__(self) -> str:
        from_time_str = datetime.fromtimestamp(self.from_time).strftime('%H:%M') if self.from_time > 0 else ""
        to_time_str = datetime.fromtimestamp(self.to_time).strftime('%H:%M') if self.to_time < MAX_TIMESTAMP_VALUE else ""
        is_hard_str = "hard" if self.is_hard else "soft"
        return f"Node {self.node}: {from_time_str} -> " \
               f"{to_time_str} | {is_hard_str} | {self.weight}"


class VehicleRoutingProblemInstance:

    def __init__(self,
                 car_distance_matrix,
                 car_duration_matrix,
                 num_plans_to_create: int,
                 starts: List[int],
                 ends: List[int],
                 courier_capacities: List[int],
                 start_utilizations: List[int],
                 node_demands: List[int],
                 pickup_nodes: List[int],
                 drop_nodes: List[int],
                 deliveries_not_started: List[Tuple[int, int]],
                 deliveries_in_progress: List[Tuple[int, int]],
                 node_time_windows: List[TimeWindowConstraint],
                 start_time_windows: List[TimeWindowConstraint],
                 time_windows: List[TimeWindowConstraint],
                 time_windows_dict: Dict[int, List[TimeWindowConstraint]],
                 pickup_service_time: ConfigProvider.get_config().get_service_time(DeliveryEventType.pickup),
                 drop_service_time: ConfigProvider.get_config().get_service_time(DeliveryEventType.drop),
                 previous_plans: List[List[int]],
                 time_limit: int = 120,
                 ) -> None:
        super().__init__()

        self.car_distance_matrix = car_distance_matrix
        self.car_duration_matrix = car_duration_matrix
        self.num_plans_to_create = num_plans_to_create
        self.starts = list(starts)
        self.ends = list(ends)

        self.courier_capacities = courier_capacities
        self.start_utilizations = start_utilizations
        self.node_demands = node_demands

        self.pickup_nodes = pickup_nodes
        self.drop_nodes = drop_nodes

        self.deliveries_not_started = deliveries_not_started
        self.deliveries_in_progress = deliveries_in_progress

        self.node_time_windows = node_time_windows
        self.start_time_windows = start_time_windows
        self.time_windows = time_windows
        self.time_windows_dict = time_windows_dict
        self.pickup_service_time = pickup_service_time
        self.drop_service_time = drop_service_time

        self.previous_plans = previous_plans
        self.time_limit = time_limit

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


class VehicleRoutingProblemMapping:

    def __init__(self, plan_idx_to_courier_id, drop_to_node, pickup_to_node, node_to_drop, node_to_pickup,
                 delivery_plan_ids) -> None:
        self.plan_idx_to_courier_id = plan_idx_to_courier_id
        self.drop_to_node = drop_to_node
        self.pickup_to_node = pickup_to_node
        self.delivery_plan_ids = delivery_plan_ids

        self.node_to_pickup = node_to_pickup
        self.node_to_drop = node_to_drop


class VehicleRoutingProblemSolution:
    def __init__(self, plans: List[List[int]], etas: List[List[int]], etds: List[List[int]]) -> None:
        self.plans = plans
        self.etas = etas
        self.etds = etds

    def __str__(self):
        return f"VRPSolution\n" \
               f"  plans: {self.plans}\n" \
               f"  etas: {self.etas}\n" \
               f"  etds: {self.etds}"


EDGE_FORBIDDEN = 1000000000


class VrpInstanceBuilder:

    def __init__(self, routing: RoutingBase) -> None:
        super().__init__()
        self.routing = routing

    def create_instance(self, deliveries: List[Delivery], couriers: List[Courier], num_plans_to_create: int,
                        previous_plans: List[Plan]) \
            -> (VehicleRoutingProblemInstance, VehicleRoutingProblemMapping):

        duration_matrix, distance_matrix, start_locations, end_locations\
            = self._create_duration_and_distance_matrix(deliveries, couriers, num_plans_to_create)

        node_to_pickup, node_to_drop, pickup_to_node, drop_to_node = \
            self._create_node_delivery_mappings(deliveries, num_plans_to_create)

        node_time_windows, start_time_windows, time_windows = \
            self._create_time_windows(deliveries, couriers, num_plans_to_create, pickup_to_node, drop_to_node)

        deliveries_not_started, deliveries_in_progress = \
            self._create_info_deliveries(deliveries=deliveries,
                                         couriers=couriers,
                                         pickup_to_node=pickup_to_node,
                                         drop_to_node=drop_to_node)

        previous_routes, delivery_plan_ids = \
            self._create_routes_from_plans(previous_plans=previous_plans,
                                           couriers=couriers,
                                           num_plans_to_create=num_plans_to_create,
                                           pickup_to_node=pickup_to_node,
                                           drop_to_node=drop_to_node)

        veh_id_to_courier_id = {idx: courier.id for idx, courier in enumerate(couriers)}

        courier_capacities, start_utilizations = self._create_courier_capacities(couriers=couriers,
                                                                                 num_vehicles=num_plans_to_create)

        num_of_nodes = len(duration_matrix)

        node_demands = self._create_node_demands(deliveries,
                                                 pickup_to_node,
                                                 drop_to_node,
                                                 num_of_nodes)

        return VehicleRoutingProblemInstance(
            car_distance_matrix=distance_matrix,
            car_duration_matrix=duration_matrix,
            num_plans_to_create=num_plans_to_create,
            starts=start_locations,
            ends=end_locations,
            courier_capacities=courier_capacities if ConfigProvider.get_config().use_courier_capacity else None,
            start_utilizations=start_utilizations if ConfigProvider.get_config().use_courier_capacity else None,
            node_demands=node_demands if ConfigProvider.get_config().use_courier_capacity else None,
            deliveries_not_started=deliveries_not_started,
            deliveries_in_progress=deliveries_in_progress,
            node_time_windows=node_time_windows,
            start_time_windows=start_time_windows,
            pickup_nodes=[pickup_to_node[key] for key in pickup_to_node.keys()],
            drop_nodes=[drop_to_node[key] for key in drop_to_node.keys()],
            time_windows_dict=time_windows,
            time_windows=node_time_windows + start_time_windows,
            pickup_service_time=ConfigProvider.get_config().get_service_time(DeliveryEventType.pickup),
            drop_service_time=ConfigProvider.get_config().get_service_time(DeliveryEventType.drop),
            previous_plans=previous_routes if ConfigProvider.get_config().use_previous_solution else None,
        ), VehicleRoutingProblemMapping(
            plan_idx_to_courier_id=veh_id_to_courier_id,
            pickup_to_node=pickup_to_node,
            drop_to_node=drop_to_node,
            node_to_pickup=node_to_pickup,
            node_to_drop=node_to_drop,
            delivery_plan_ids=delivery_plan_ids
        )

    def _create_duration_and_distance_matrix(self, deliveries: List[Delivery], couriers: List[Courier], num_plans: int):
        pickup_locations = list(map(lambda x: x.origin, filter(lambda x: x.origin is not None, deliveries)))
        drop_locations = list(map(lambda x: x.destination, deliveries))
        courier_locations = list(map(lambda x: x.start_timelocation.location, couriers))

        locations = pickup_locations + drop_locations + courier_locations

        config = ConfigProvider.get_config()
        if config.return_to_hub and config.hub_location:
            locations.append(config.hub_location)

        # TODO currently a lot of unnecessary transition is computed - distances between couriers locations and
        # TODO from delivery location to courier locations are not necessary - should not be computed and set to INT.max
        car_durations, car_distances = self.routing.create_duration_distance_matrix(locations, mode=OSRMProfile.car)

        final_matrix_dim = len(pickup_locations) + len(drop_locations) + num_plans * 2

        first_start_column_idx = len(pickup_locations) + len(drop_locations)
        first_end_column_idx = first_start_column_idx + num_plans

        def extend_matrix_by_starts_ends(matrix, default_start_value: int):
            extended = np.zeros(shape=(final_matrix_dim, final_matrix_dim), dtype=int)

            extended[:len(matrix), :len(matrix)] = matrix

            extended[first_start_column_idx + len(couriers):first_end_column_idx, :first_end_column_idx] = default_start_value
            extended[first_end_column_idx:, :] = EDGE_FORBIDDEN

            if config.return_to_hub:
                to_hub_distances = extended[:, first_start_column_idx+len(couriers)]
                for i in range(num_plans):
                    extended[:, first_end_column_idx+i] = to_hub_distances

            extended[:, first_start_column_idx:first_end_column_idx] = EDGE_FORBIDDEN

            reshaped = np.zeros_like(extended)

            a = 2 * num_plans
            b = first_start_column_idx
            reshaped[:a, :a] = extended[b:, b:]
            reshaped[:a, a:] = extended[b:, :b]
            reshaped[a:, :a] = extended[:b, b:]
            reshaped[a:, a:] = extended[:b, :b]

            return reshaped.tolist()

        car_distances = extend_matrix_by_starts_ends(matrix=car_distances,
                                                     default_start_value=config.default_first_point_arrival_distance)

        car_durations = extend_matrix_by_starts_ends(matrix=car_durations,
                                                     default_start_value=config.default_first_point_arrival_time)

        start_locations = [i for i in range(num_plans)]
        end_locations = [num_plans + i for i in range(num_plans)]

        return car_durations, car_distances, start_locations, end_locations

    def _create_node_delivery_mappings(self, deliveries: List[Delivery], n_plans: int):

        node_to_pickup = {}
        node_idx = 2 * n_plans
        for delivery in deliveries:
            if delivery.pickup_time is None:
                continue

            node_to_pickup[node_idx] = delivery
            node_idx += 1

        node_to_drop = {}
        for delivery in deliveries:
            node_to_drop[node_idx] = delivery
            node_idx += 1

        pickup_to_node = {node_to_pickup[k].id: k for k in node_to_pickup.keys()}
        drop_to_node = {node_to_drop[k].id: k for k in node_to_drop.keys()}

        return node_to_pickup, node_to_drop, pickup_to_node, drop_to_node

    @staticmethod
    def _create_time_windows(deliveries: List[Delivery], couriers: List[Courier], n: int,
                             pickup_to_node: dict, drop_to_node: dict):
        config = ConfigProvider.get_config()

        start_time_windows = []
        now_timestamp = TimestampHelper.current_timestamp()
        for node_idx in range(n):
            from_time = couriers[node_idx].start_timelocation.time if node_idx < len(couriers) else now_timestamp

            start_time_windows.append(TimeWindowConstraint(node=node_idx, from_time=from_time,
                                                           to_time=from_time, is_hard=True))

        def create_constraint_from_specification(delivery: Delivery,
                                                 specification: PenaltySpecification) -> Optional[TimeWindowConstraint]:
            if specification.node_type == DeliveryEventType.pickup and delivery.pickup_time is None:
                return None

            time_block = delivery.pickup_time if specification.node_type == DeliveryEventType.pickup else delivery.delivery_time

            if specification.node_type == DeliveryEventType.pickup:
                node = pickup_to_node[delivery.id]
            else:
                node = drop_to_node[delivery.id]

            ret = TimeWindowConstraint(node=node, is_hard=specification.is_hard, weight=specification.weight)

            if specification.direction == PenaltyDirection.earliness:
                ret.from_time = time_block.from_time - specification.offset
            elif specification.direction == PenaltyDirection.lateness:

                if time_block.anytime:
                    return None
                elif time_block.asap or time_block.to_time is not None:

                    if time_block.asap:
                        constrain_begin = delivery.delivery_time.from_time + config.get_asap_tolerance(specification.node_type)
                    else:
                        constrain_begin = delivery.delivery_time.to_time

                    ret.to_time = constrain_begin + specification.offset

            return ret

        node_time_windows = []
        for delivery in deliveries:
            for specification in config.penalties:
                tw = create_constraint_from_specification(delivery=delivery, specification=specification)
                if tw:
                    node_time_windows.append(tw)

        time_windows = defaultdict(lambda: list())
        for tw in node_time_windows + start_time_windows:
            time_windows[tw.node].append(tw)

        return node_time_windows, start_time_windows, time_windows

    @staticmethod
    def _create_info_deliveries(deliveries: List[Delivery], couriers: List[Courier],
                                pickup_to_node: dict, drop_to_node: dict):
        deliveries_not_started = []
        deliveries_in_progress = []

        courier_id_to_idx = {courier.id: idx for idx, courier in enumerate(couriers)}

        for delivery in deliveries:
            if delivery.assigned_courier_id is not None:
                courier_idx = courier_id_to_idx[delivery.assigned_courier_id]
                deliveries_in_progress.append((courier_idx, drop_to_node[delivery.id]))
            else:
                deliveries_not_started.append((pickup_to_node[delivery.id],
                                               drop_to_node[delivery.id]))

        return deliveries_not_started, deliveries_in_progress

    def _create_routes_from_plans(self, previous_plans: List[Plan], couriers: List[Courier], num_plans_to_create: int,
                                  drop_to_node, pickup_to_node) \
            -> (List[List[int]], List[int]):

        if previous_plans is None:
            return None, None

        routes = []
        delivery_plan_ids = []
        for courier in couriers:
            plan = [plan for plan in previous_plans if plan.assigned_courier_id == courier.id]

            plan = None if len(plan) == 0 else plan[0]

            route = self._route_from_plan(plan, drop_to_node, pickup_to_node)
            delivery_plan_ids.append(plan.delivery_plan_id if plan else None)
            routes.append(route)

        non_assigned_plans = [plan for plan in previous_plans if plan.assigned_courier_id is None]
        non_assigned_plans = sorted(non_assigned_plans, key=lambda x: len(x.delivery_order_ids))

        to_add = num_plans_to_create - len(routes)
        for i in range(to_add):
            plan = non_assigned_plans.pop() if non_assigned_plans else None
            route = self._route_from_plan(plan, drop_to_node, pickup_to_node)
            delivery_plan_ids.append(plan.delivery_plan_id if plan else None)
            routes.append(route)

        return routes, delivery_plan_ids

    @staticmethod
    def _route_from_plan(plan: Plan, delivery_drop_to_node: dict, delivery_pickup_to_node: dict):
        route = []

        if plan is None:
            return route

        for delivery_event in plan.delivery_events:
            for delivery_order_id in delivery_event.delivery_order_ids:
                if delivery_event.type == DeliveryEventType.pickup and delivery_order_id in delivery_pickup_to_node:
                    node = delivery_pickup_to_node[delivery_order_id]
                elif delivery_order_id in delivery_drop_to_node:
                    node = delivery_drop_to_node[delivery_order_id]
                else:
                    node = None
                if node:
                    route.append(node)

        return route

    @classmethod
    def _create_courier_capacities(cls, couriers: List[Courier], num_vehicles: int):
        config = ConfigProvider.get_config()

        capacities = [c.capacity for c in couriers] + \
                     [config.default_courier_capacity for _ in range(num_vehicles - len(couriers))]

        start_utilizations = [c.start_utilization for c in couriers] + \
                             [0 for _ in range(num_vehicles - len(couriers))]

        return capacities, start_utilizations

    @classmethod
    def _create_node_demands(cls, deliveries: List[Delivery], pickup_to_node: dict, drop_to_node: dict, num_of_nodes: int):
        ret = [0] * num_of_nodes

        for delivery in deliveries:
            pickup_node = pickup_to_node.get(delivery.id, None)

            if pickup_node:
                ret[pickup_node] = delivery.size

            drop_node = drop_to_node.get(delivery.id, None)
            if drop_node:
                ret[drop_node] = -delivery.size if delivery.size else None
        return ret
