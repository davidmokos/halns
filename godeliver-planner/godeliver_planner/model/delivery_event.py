from enum import Enum

from flask_restful_swagger_2 import Schema
from pydantic import BaseModel
from typing import List, Optional
from godeliver_planner.model.location import Location, LocationModel
from godeliver_planner.model.timeblock import TimeBlock, TimeBlockModel


class DeliveryEventType(str, Enum):
    pickup = 'PICKUP'
    drop = 'DROP'


class DeliveryEvent(BaseModel):
    type: DeliveryEventType
    location: Location

    delivery_order_ids: List[str]

    event_time: TimeBlock
    fixed_time: Optional[int] = None

    def to_string(self, pretty: bool = False) -> str:
        return f"{self.type} of {self.delivery_order_ids} at {self.location} | {self.event_time}"

    def __str__(self) -> str:
        return f"{self.type} of {self.delivery_order_ids} at {self.location} | {self.event_time}"


class DeliveryEventTypeModel(Schema):
    type = 'object'
    properties = {
        'value': {
            'type': 'string',
            'enum': [val.value for val in DeliveryEventType],
        }
    }


class DeliveryEventModel(Schema):
    type = 'object'
    properties = {
        'type': DeliveryEventTypeModel,
        'location': LocationModel,
        'delivery_order_ids': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'event_time': TimeBlockModel
    }
    required = ['type, location', 'delivery_order_ids', 'event_time']

