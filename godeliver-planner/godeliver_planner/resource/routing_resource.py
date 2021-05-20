from datetime import datetime
from typing import List, Optional

from flask_restful import request
from flask_restful_swagger_2 import Schema, swagger

from godeliver_planner.helper.timestamp_helper import  TimestampHelper
from godeliver_planner.model.courier import Courier, CourierModel
from godeliver_planner.model.delivery import Delivery, DeliveryModel
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.location import LocationModel, TimeLocationModel, Location
from godeliver_planner.model.plan import PlanModel
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.resource.abstract_resource import AbstractResource
from godeliver_planner.routing.routing_base import RoutingBase


class RoutingResponse(Schema):
    type = 'object'
    properties = {
        'time_locations': {
            'type': 'array',
            'items': TimeLocationModel
        }
    }


class RoutingRequest(Schema):
    type = 'object'
    properties = {
        'locations': {
            'type': 'array',
            'items': LocationModel
        },
        'starting_time': {
            'type': 'int'
        }
    }
    required = ['locations']


class RoutingResource(AbstractResource):

    def __init__(self, **kwargs):
        super(RoutingResource, self).__init__()

        self.routing: RoutingBase = kwargs['routing']

    @swagger.doc({
        'tags': ['Routing'],
        'summary': "Calculate lenght of a route",
        'description': 'Based on the provided location calculates its length.',
        'parameters': [
            {
                'name': 'body',
                'description': 'Request body with the points that shall be visited.'
                               ' If starting time is not provided the route is considered to start now.',
                'in': 'body',
                'schema': RoutingRequest,
                'required': True,
            }
        ],
        'responses': {
            '200': {
                'description': 'Created plans response.',
                'schema': RoutingResponse,
                'headers': {},
                'examples': {}
            }
        }
    })
    def post(self):
        return self.handle_request(
            parse_body=self.parse_body,
            validate_input=self.validate,
            execute=self.execute
        )

    def parse_body(self):
        body = request.get_json(force=True)

        locations = list(map(Location.parse_obj, body['locations']))

        starting_time = int(body['starting_time']) if 'starting_time' in body else TimestampHelper.current_timestamp()

        return {
            'locations': locations,
            'starting_time': starting_time,
        }

    def validate(self, locations: List[Location], starting_time: int):
        assert len(locations) > 0, "No locations provided"
        assert starting_time > 0, "Starting time can not be negative"

    def execute(self, locations: List[Location], starting_time: int):

        time_locations, distances = self.routing.compute_time_along_route(locations, starting_time)

        return {
            'time_locations': list(map(lambda x: x.dict(), time_locations)),
            'distances': distances
        }
