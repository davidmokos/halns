from typing import Optional

from flask_restful_swagger_2 import Schema
from pydantic import BaseModel
from godeliver_planner.model.location import TimeLocation, TimeLocationModel


class CourierModel(Schema):
    type = 'object'
    properties = {
        'id': {
            'type': 'string'
        },
        'start_timelocation': TimeLocationModel,
        'is_finishing': {
            'type': 'bool'
        },
        'capacity': {
            'type': 'integer'
        },
        'start_utilization': {
            'type': 'integer'
        }
    }
    required = ['id', 'start_timelocation']


class Courier(BaseModel):
    id: str                                     # courier's ID
    start_timelocation: TimeLocation = None     # the couriers initial position and time
    is_finishing: Optional[bool] = False        # whether the courier is finishing - no more pickup tasks should be planned
    capacity: Optional[int] = None
    start_utilization: Optional[int] = None
