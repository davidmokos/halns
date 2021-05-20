from typing import List
from flask import jsonify, abort
from flask_restful import Resource, request, reqparse, inputs
from flask_restful_swagger_2 import Schema, swagger

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.model.delivery import Delivery, DeliveryModel
from godeliver_planner.model.plan import Plan, PlanModel
from godeliver_planner.helper.exceptions import NoSolutionException
from godeliver_planner.model.planner_config import PlannerConfig
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.routing.routing_base import RoutingBase
from godeliver_planner.service.planning_service import PlanningService


class LogisticsResponse(Schema):
    type = 'object'
    properties = {
        'status': {
            'type': 'string'
        },
        'plans': {
            'type': 'array',
            'items': PlanModel
        },
    }


class LogisticsRequest(Schema):
    type = 'object'
    properties = {
        'deliveries': {
            'type': 'array',
            'items': DeliveryModel
        },
        'num_vehicles': {
            'type': 'integer',
        }
    }
    required = ['num_vehicles']


class LogisticsPlan(Resource):

    def __init__(self, **kwargs):
        super(LogisticsPlan, self).__init__()

        routing: RoutingBase = kwargs['routing']
        self.planning_service: PlanningService = PlanningService(routing=routing)

    @swagger.doc({
        'tags': ['Logistics'],
        'summary': "Create plans",
        'description': 'Create plans with passed deliveries. The numbed of created plans is equal to num_vehicles',
        'parameters': [
            {
                'name': 'body',
                'description': 'Request body with the deliveries, that shall be planed.',
                'in': 'body',
                'schema': LogisticsRequest,
                'required': True,
            }
        ],
        'responses': {
            '200': {
                'description': 'Created plans response. The number of plans is equal to num_vehicles.',
                'schema': LogisticsResponse,
                'headers': {},
                'examples': {}
            }
        }
    })
    def post(self):

        body = request.get_json(force=True)
        parser = reqparse.RequestParser()

        try:
            deliveries = list(
                map(lambda x: Delivery.parse_obj(x), body['deliveries'])
            )

            num_vehicles = body['num_vehicles']

            config = None
            try:
                config = PlannerConfig.parse_obj(body['config']) if 'config' in body else None
            except Exception as e:
                print(f"Unable to parse config - {e}")
            ConfigProvider.set_current_config(config)

            plans: List[Plan] = self.planning_service.create_plans(deliveries=deliveries, couriers=[],
                                                                   min_number_of_plans=num_vehicles,
                                                                   previous_plans=[])
        except NoSolutionException as e:
            abort(404, e.message)

        # add delivery_id
        return jsonify(status='success', plans=list(map(lambda x: x.dict(), plans)))
