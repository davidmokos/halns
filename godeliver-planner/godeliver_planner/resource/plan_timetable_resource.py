from typing import List

from flask_restful import request
from flask_restful_swagger_2 import Schema, swagger

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.logs.log_helper import LogHelper
from godeliver_planner.model.courier import Courier, CourierModel
from godeliver_planner.model.delivery import Delivery, DeliveryModel
from godeliver_planner.model.plan import PlanModel, Plan
from godeliver_planner.model.planner_config import PlannerConfig
from godeliver_planner.model.timeblock import TimeBlockModel
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.planner.plan_timetable.plan_timetable_optimizer import PlanTimetableOptimizer
from godeliver_planner.resource.abstract_resource import AbstractResource


class PlanTimetableResponse(Schema):
    type = 'object'
    properties = {
        'status': {
            'type': 'string'
        },
        'time_blocks': {
            'type': 'array',
            'items': TimeBlockModel
        },
        'fixed_times': {
            'type': 'array',
            'items': 'integer'
        }
    }


class PlanTimetableRequest(Schema):
    type = 'object'
    properties = {
        'deliveries': {
            'type': 'array',
            'items': DeliveryModel
        },
        'courier': {
            'type': CourierModel
        },
        'plan': {
            'type': PlanModel
        }
    }
    required = ['deliveries', 'courier', 'plan']


class PlanTimetableResource(AbstractResource):

    def __init__(self, **kwargs):
        super(PlanTimetableResource, self).__init__()

        self.timetable_optimizer: PlanTimetableOptimizer = kwargs['timetable_optimizer']

    @swagger.doc({
        'tags': ['Logistics'],
        'summary': "Plan Timetable",
        'description': 'Find optimal timetable for given plan, orders and courier.',
        'parameters': [
            {
                'name': 'body',
                'description': 'Request body with the plan, that shall be optimized.',
                'in': 'body',
                'schema': PlanTimetableRequest,
                'required': True,
            }
        ],
        'responses': {
            '200': {
                'description': 'Found optimal timetable in timeblocks. Each timeblock corresponds to '
                               'a delivery event in the passed plan.',
                'schema': PlanTimetableResponse,
                'headers': {},
                'examples': {}
            }
        }
    })
    def post(self):
        return self.handle_request(
            parse_body=self.parse_body,
            execute=self.execute
        )

    def parse_body(self):
        body = request.get_json(force=True)

        deliveries = list(
            map(lambda x: Delivery.parse_obj(x), body['deliveries'])
        )

        courier = Courier.parse_obj(body['courier'])

        plan = Plan.parse_obj(body['plan'])
        config = PlannerConfig.parse_obj(body.get('config', {}))

        return {
            'deliveries': deliveries,
            'courier': courier,
            'plan': plan,
            'config': config
        }

    def execute(self, deliveries: List[Delivery], courier: Courier, plan: Plan, config: PlannerConfig):
        config.use_previous_solution = True     # enforcing the use of previous solution - otherwise the computing fails
                                                # as the VRP instance will not contain the plan

        ConfigProvider.set_current_config(config)

        time_blocks, fixed_times = self.timetable_optimizer.update_etas_in_plan(
                deliveries=deliveries,
                courier=courier,
                plan=plan
        )
        return {
            'time_blocks': list(map(lambda x: x.dict(), time_blocks)),
            'fixed_times': fixed_times
        }
