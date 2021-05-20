from typing import Optional

from flask_restful_swagger_2 import Schema
from pydantic import BaseModel
from godeliver_planner.model.location import Location, LocationModel
from godeliver_planner.model.timeblock import TimeBlock, TimeBlockModel


class DeliveryModel(Schema):
    type = 'object'
    properties = {
        'id': {
            'type': 'string'
        },
        'assigned_user_id': {
            'type': 'string'
        },
        'origin': LocationModel,
        'destination': LocationModel,
        'pickup_time': TimeBlockModel,
        'delivery_time': TimeBlockModel,
        'size': {
            'type': 'integer'
        }
    }
    required = ['id', 'destination', 'delivery_time']


class Delivery(BaseModel):
    id: str  # id of the delivery

    assigned_courier_id: Optional[str]  # id of assigned courier or None

    origin: Optional[Location]  # location to pickup the delivery or None if already visited
    destination: Location  # location to drop the delivery

    pickup_time: Optional[TimeBlock]  # time window when to pickup the delivery or None if already visited
    delivery_time: TimeBlock  # time window when to drop the delivery

    size: Optional[int] = None
