from flask_restful_swagger_2 import Schema
from pydantic import BaseModel
from typing import List, Optional
from godeliver_planner.model.delivery_event import DeliveryEvent, DeliveryEventModel
from godeliver_planner.model.mode import Mode


class PlanModel(Schema):
    type = 'object'
    properties = {
        'delivery_events': {
            'type': 'array',
            'items': DeliveryEventModel
        },
        'delivery_order_ids': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'duration': {
            'type': 'integer'
        },
        'distance': {
            'type': 'integer'
        },
        'assigned_courier_id': {
            'type': 'string',
        }
    }


class Plan(BaseModel):
    delivery_events: List[DeliveryEvent]

    delivery_order_ids: List[str]

    duration: int
    distance: int

    mode: Mode

    assigned_courier_id: Optional[str]       # id of assigned courier or None
    delivery_plan_id: Optional[str]

    def __str__(self) -> str:
        events = "\n\t".join(map(str, self.delivery_events))
        return f'Plan for {self.assigned_courier_id} \n Stops at: \n\t{events}'



