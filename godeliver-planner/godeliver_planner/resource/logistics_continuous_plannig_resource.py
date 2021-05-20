from typing import List, Optional

from flask_restful import request
from flask_restful_swagger_2 import Schema, swagger

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.logs.log_helper import LogHelper
from godeliver_planner.model.courier import Courier, CourierModel
from godeliver_planner.model.delivery import Delivery, DeliveryModel
from godeliver_planner.model.plan import PlanModel, Plan
from godeliver_planner.model.planner_config import PlannerConfig
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.resource.abstract_resource import AbstractResource
from godeliver_planner.routing.routing_base import RoutingBase
from godeliver_planner.service.planning_service import PlanningService


class LogisticsContinuousResponse(Schema):
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


class LogisticsContinuousRequest(Schema):
    type = 'object'
    properties = {
        'deliveries': {
            'type': 'array',
            'items': DeliveryModel
        },
        'couriers': {
            'type': 'array',
            'items': CourierModel
        },
        'minimal_number_of_plans': {
            'type': 'integer',
        },
        'current_plans': {
            'type': 'array',
            'items': PlanModel
        }
    }
    required = ['deliveries', 'couriers', 'minimal_number_of_plans']


class LogisticsContinuousPlan(AbstractResource):

    def __init__(self, **kwargs):
        super(LogisticsContinuousPlan, self).__init__()

        routing: RoutingBase = kwargs['routing']
        self.planning_service: PlanningService = PlanningService(routing=routing)

    @swagger.doc({
        'tags': ['Logistics'],
        'summary': "Create plans - continuous replaning",
        'description': 'Create plans with passed deliveries. The number of created plans is '
                       'least minimal_number_of_plans, unless the number of online couriers is bigger.',
        'parameters': [
            {
                'name': 'body',
                'description': 'Request body with the deliveries, that shall be planed.',
                'in': 'body',
                'schema': LogisticsContinuousRequest,
                'required': True,
            }
        ],
        'responses': {
            '200': {
                'description': 'Created plans response.',
                'schema': LogisticsContinuousResponse,
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

        deliveries = list(
            map(lambda x: Delivery.parse_obj(x), body['deliveries'])
        )

        couriers = list(
            map(lambda x: Courier.parse_obj(x), body['couriers'])
        )

        min_number_of_plans = int(body['min_number_of_plans'])

        current_plans = [] if 'current_plans' not in body else [Plan.parse_obj(x) for x in body['current_plans']]

        config = None
        try:
            config = PlannerConfig.parse_obj(body['config']) if 'config' in body else None
        except Exception as e:
            print(f"Unable to parse config - {e}")

        return {
            'deliveries': deliveries,
            'couriers': couriers,
            'min_number_of_plans': min_number_of_plans,
            'current_plans': current_plans,
            'config': config
        }

    def validate(self, deliveries: List[Delivery], couriers: List[Courier],
                 min_number_of_plans: int, current_plans: List[Plan],
                 config: Optional[PlannerConfig]):
        for delivery in deliveries:
            msg = "Either origin + pickup_time shall be empty and assigned_courier_id filled or " \
                  "assigned_courier_id shall be empty a and origin + pickup_time shall be filled." \
                  f"Delivery {delivery.id}"
            if delivery.assigned_courier_id is not None or delivery.origin is None or delivery.pickup_time is None:
                assert delivery.assigned_courier_id is not None, msg
                assert delivery.origin is None, msg
                assert delivery.pickup_time is None, msg

            if delivery.assigned_courier_id is not None:
                t_couriers = list(filter(lambda x: x.id == delivery.assigned_courier_id, couriers))
                assert len(t_couriers) == 1, f"There should be exactly one online courier " \
                                             f"with id {delivery.assigned_courier_id}."

    def execute(self, deliveries: List[Delivery], couriers: List[Courier],
                min_number_of_plans: int, current_plans: List[Plan],
                config: Optional[PlannerConfig]):
        ConfigProvider.set_current_config(config)

        try:
            plans = self.planning_service.create_plans(deliveries=deliveries,
                                                       couriers=couriers,
                                                       min_number_of_plans=min_number_of_plans,
                                                       previous_plans=current_plans)
        except Exception as e:
            try:
                LogHelper.log_failed_to_solve(deliveries=deliveries, couriers=couriers,
                                              min_number_of_plans=min_number_of_plans, exception=e)
            finally:
                raise e

        return {
            'plans': list(map(lambda x: x.dict(), plans))
        }
