from typing import List

from godeliver_planner.model.courier import Courier
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.plan import Plan
from godeliver_planner.planner.plan_timetable.fixed_time_computer import FixedTimeComputer
from godeliver_planner.planner.plan_timetable.plan_timetable_computer import AbstractPlanTimetableComputer
from godeliver_planner.planner.vrp_instance_builder import VrpInstanceBuilder
from godeliver_planner.routing.routing_base import RoutingBase


class PlanTimetableOptimizer:
    def __init__(self, timetable_computer: AbstractPlanTimetableComputer, routing: RoutingBase) -> None:
        super().__init__()
        self.timetable_computer: AbstractPlanTimetableComputer = timetable_computer
        self.instance_builder = VrpInstanceBuilder(routing)

    def update_etas_in_plan(self, plan: Plan, deliveries: List[Delivery], courier: Courier):

        vrp_instance, vrp_mapping = self.instance_builder.create_instance(
            deliveries=deliveries,
            num_plans_to_create=1,
            previous_plans=[plan],
            couriers=[courier]
        )

        route =[vrp_instance.starts[0]] + vrp_instance.previous_plans[0]
        node_id_to_road_idx = {node: next(filter(lambda n: n[1] == node, enumerate(route)))[0]
                               for node in vrp_instance.pickup_nodes + vrp_instance.drop_nodes}
        etas, etds, _ = self.timetable_computer.compute_optimal_timetable(
            pickup_nodes=vrp_instance.pickup_nodes,
            drop_nodes=vrp_instance.drop_nodes,
            car_duration_matrix=vrp_instance.car_duration_matrix,
            time_windows=vrp_instance.time_windows_dict,
            route=route
        )

        for event in plan.delivery_events:
            if event.type == DeliveryEventType.pickup:
                event_deliveries_etas = [etas[node_id_to_road_idx[vrp_mapping.pickup_to_node[delivery_id]]]
                                         for delivery_id in event.delivery_order_ids]
                event_deliveries_etds = [etds[node_id_to_road_idx[vrp_mapping.pickup_to_node[delivery_id]]]
                                         for delivery_id in event.delivery_order_ids]
            else:
                event_deliveries_etas = [etas[node_id_to_road_idx[vrp_mapping.drop_to_node[delivery_id]]]
                                         for delivery_id in event.delivery_order_ids]
                event_deliveries_etds = [etds[node_id_to_road_idx[vrp_mapping.drop_to_node[delivery_id]]]
                                         for delivery_id in event.delivery_order_ids]

            min_eta = min(event_deliveries_etas)
            max_etd = max(event_deliveries_etds)

            event.event_time.from_time = min_eta
            event.event_time.to_time = max_etd

        fixed_times = FixedTimeComputer.compute_fixed_times(plan=plan,
                                                            start_node=vrp_instance.starts[0],
                                                            vrp_instance=vrp_instance,
                                                            vrp_mapping=vrp_mapping)
        time_blocks = [event.event_time for event in plan.delivery_events]

        return time_blocks, fixed_times



