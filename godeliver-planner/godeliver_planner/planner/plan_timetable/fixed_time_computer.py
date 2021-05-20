from typing import List, Optional

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.plan import Plan
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemMapping


class FixedTimeComputer:

    @staticmethod
    def compute_fixed_times(plan: Plan,
                            start_node: int,
                            vrp_instance: VehicleRoutingProblemInstance,
                            vrp_mapping: VehicleRoutingProblemMapping) -> List[Optional[int]]:
        config = ConfigProvider.get_config()

        nodes = [start_node] + \
                [vrp_mapping.pickup_to_node[event.delivery_order_ids[0]] if event.type == DeliveryEventType.pickup
                 else vrp_mapping.drop_to_node[event.delivery_order_ids[0]] for event in plan.delivery_events]

        if plan.assigned_courier_id is None:
            return [None] * (len(nodes) - 1)

        fixed_times = []
        for from_node, to_node, event in zip(nodes[:-1], nodes[1:], plan.delivery_events):

            travel_time = vrp_instance.car_duration_matrix[from_node][to_node]
            buffer_time = config.fixed_time_buffer
            service_time = vrp_instance.pickup_service_time if event.type == DeliveryEventType.pickup else vrp_instance.drop_service_time
            event_time = event.event_time.to_time if event.type == DeliveryEventType.pickup else event.event_time.from_time

            fixed_time = int(event_time - service_time - travel_time - buffer_time)
            fixed_times.append(fixed_time)

        return fixed_times

