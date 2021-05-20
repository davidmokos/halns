from abc import abstractmethod
from typing import List

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.model.courier import Courier
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.delivery_event import DeliveryEventType, DeliveryEvent
from godeliver_planner.model.mode import Mode
from godeliver_planner.model.plan import Plan
from godeliver_planner.model.planner_config import PlannerConfig
from godeliver_planner.model.timeblock import TimeBlock
from godeliver_planner.planner.plan_timetable.fixed_time_computer import FixedTimeComputer
from godeliver_planner.planner.plan_timetable.lp_plan_timetable_computer import LpPlanTimetableComputer
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemMapping, \
    VehicleRoutingProblemSolution, VrpInstanceBuilder
from godeliver_planner.routing.routing_base import RoutingBase


class AbstractPlanner:

    def __init__(self, routing: RoutingBase):
        self.instance_builder = VrpInstanceBuilder(routing)

    @property
    def config(self) -> PlannerConfig:
        return ConfigProvider.get_config()

    @abstractmethod
    def solve(self, data_model: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:
        raise NotImplementedError()

    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()

    def logistics_planner(self, deliveries: List[Delivery], couriers: List[Courier], min_number_of_plans: int,
                          previous_plans: List[Plan] = None):
        deliveries, couriers = self._sort_input(deliveries, couriers)

        number_of_plans = max(len(couriers), min_number_of_plans)

        vrp_instance, vrp_mapping = self.instance_builder.create_instance(deliveries, couriers,
                                                                          number_of_plans, previous_plans)

        solution = self.solve(vrp_instance)

        plans = self.solution_to_plan(vrp_instance=vrp_instance,
                                      vrp_mapping=vrp_mapping,
                                      vrp_solution=solution)

        if previous_plans:
            for plan, delivery_plan_id in zip(plans, vrp_mapping.delivery_plan_ids):
                plan.delivery_plan_id = delivery_plan_id

        return plans

    @staticmethod
    def _sort_input(deliveries: List[Delivery], couriers: List[Courier]):
        def get_id(d):
            return d.id

        deliveries = sorted(deliveries, key=get_id)

        couriers = sorted(couriers, key=get_id)

        return deliveries, couriers

    @staticmethod
    def deffer_pickups_in_plan(delivery_events: List[DeliveryEvent]):
        pickup_location_per_order = {}

        orders_in_trunk = set()
        for delivery_event in delivery_events:
            if delivery_event.type == DeliveryEventType.pickup:
                if len(orders_in_trunk) > 0:
                    for order in orders_in_trunk:
                        original_order_event = pickup_location_per_order[order]
                        if original_order_event.location.distance_from(delivery_event.location) < 25:
                            original_order_event.delivery_order_ids.remove(order)
                            delivery_event.delivery_order_ids.append(order)

                for delivery_order_id in delivery_event.delivery_order_ids:
                    orders_in_trunk.add(delivery_order_id)
                    pickup_location_per_order[delivery_order_id] = delivery_event
            elif delivery_event.type == DeliveryEventType.drop:
                for delivery_order_id in delivery_event.delivery_order_ids:
                    try:
                        orders_in_trunk.remove(delivery_order_id)
                    except KeyError:
                        continue

        ret = []
        for delivery_event in delivery_events:
            if len(delivery_event.delivery_order_ids) != 0:
                ret.append(delivery_event)

        return ret

    @staticmethod
    def solution_to_plan(vrp_solution: VehicleRoutingProblemSolution, vrp_mapping: VehicleRoutingProblemMapping,
                         vrp_instance: VehicleRoutingProblemInstance):
        total_distance = 0
        total_duration = 0
        plans = []
        for vehicle_idx, (route, etas, etds) in enumerate(
                zip(vrp_solution.plans, vrp_solution.etas, vrp_solution.etds)):
            plan_output = 'Route for vehicle {}:\n'.format(vehicle_idx)
            route_distance = 0

            plan = Plan(delivery_events=[], delivery_order_ids=[], duration=0, distance=0, mode=Mode.CAR)

            if vehicle_idx in vrp_mapping.plan_idx_to_courier_id:
                plan.assigned_courier_id = vrp_mapping.plan_idx_to_courier_id[vehicle_idx]

            delivery_events = []
            last_event = None
            previous_node = None

            start_time = None
            for node, eta, etd in zip(route, etas, etds):

                if start_time is None:
                    start_time = eta

                if node in vrp_mapping.node_to_pickup:
                    delivery = vrp_mapping.node_to_pickup[node]
                    location = delivery.origin
                    delivery_type = DeliveryEventType.pickup
                elif node in vrp_mapping.node_to_drop:
                    delivery = vrp_mapping.node_to_drop[node]
                    location = delivery.destination
                    delivery_type = DeliveryEventType.drop
                else:
                    continue

                arrival_time = eta
                departure_time = etd

                if last_event is None \
                        or last_event.location.distance_from(location) > 25 \
                        or last_event.type != delivery_type \
                        or delivery_type == DeliveryEventType.drop:

                    if last_event is not None and previous_node is not None:
                        travel_duration = vrp_instance.car_duration_matrix[previous_node][node]

                        # is this really necessary??
                        last_event.event_time.to_time = max(last_event.event_time.to_time,
                                                            arrival_time - travel_duration)

                    delivery_event = DeliveryEvent(
                        type=delivery_type,
                        location=location,
                        delivery_order_ids=[delivery.id],
                        event_time=TimeBlock(
                            from_time=arrival_time,
                            to_time=departure_time
                        )
                    )
                    delivery_events.append(delivery_event)
                    last_event = delivery_event
                else:
                    last_event.delivery_order_ids.append(delivery.id)
                    last_event.event_time.from_time = min(last_event.event_time.from_time, arrival_time)
                    last_event.event_time.to_time = max(last_event.event_time.to_time, departure_time)

                plan.delivery_order_ids.append(delivery.id)

                if previous_node:
                    route_distance += vrp_instance.car_distance_matrix[previous_node][node]

                previous_node = node

            route_duration = round(etas[-1] - etds[0], 3)
            route_distance = round(route_distance, 3)
            plan.delivery_events = delivery_events
            plan.distance = route_distance
            plan.duration = route_duration

            plan.delivery_order_ids = list(set(plan.delivery_order_ids))

            print(plan_output)
            total_distance += route_distance
            total_duration += route_duration
            print(plan)
            plans.append(plan)

            print(f"route duration: {route_duration} sec")
            print(f"route distance: {route_distance} m")

        print('Total Duration of all routes: {} sec'.format(total_duration))
        print('\nTotal Distance of all routes: {} m'.format(total_distance))

        for plan in plans:
            plan.delivery_events = AbstractPlanner.deffer_pickups_in_plan(plan.delivery_events)

        for idx, plan in enumerate(plans):
            fixed_times = FixedTimeComputer.compute_fixed_times(plan=plan,
                                                                start_node=vrp_instance.starts[idx],
                                                                vrp_instance=vrp_instance,
                                                                vrp_mapping=vrp_mapping)

            for event, fixed_time in zip(plan.delivery_events, fixed_times):
                event.fixed_time = fixed_time

        return plans

    @staticmethod
    def optimize_times_in_solution(solution: VehicleRoutingProblemSolution,
                                   vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:
        ret = VehicleRoutingProblemSolution(
            plans=solution.plans,
            etas=[],
            etds=[]
        )

        for i in range(len(solution.plans)):
            etas, etds, _ = LpPlanTimetableComputer().compute_optimal_timetable(
                drop_nodes=vrp_instance.drop_nodes,
                pickup_nodes=vrp_instance.pickup_nodes,
                car_duration_matrix=vrp_instance.car_duration_matrix,
                route=solution.plans[i],
                time_windows=vrp_instance.time_windows_dict
            )
            ret.etas.append(etas)
            ret.etds.append(etds)

        return ret