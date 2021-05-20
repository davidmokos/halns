from godeliver_planner.planner.plan_timetable.plan_timetable_computer import AbstractPlanTimetableComputer
from godeliver_planner.planner.plan_timetable.plan_timetable_optimizer import PlanTimetableOptimizer
from godeliver_planner.resource.logistics_continuous_plannig_resource import LogisticsContinuousPlan
from godeliver_planner.resource.logistics_plan import LogisticsPlan
from godeliver_planner.resource.plan_timetable_resource import PlanTimetableResource
from godeliver_planner.resource.routing_resource import RoutingResource
from godeliver_planner.resource.swagger_resource import SwaggerResource
from godeliver_planner.routing.routing_base import RoutingBase


class ResourceManager(object):

    @classmethod
    def register(cls, api, planner, continuous_planner,
                 timetable_optimizer: PlanTimetableOptimizer,
                 routing: RoutingBase):

        # ---REGISTER RESOURCE----
        # INFO: GoDeliver-Planner's API endpoints has to start with /delivery/planner because of GCP URL mapping

        # DELIVERY PLANS

        api.add_resource(LogisticsPlan, '/delivery/planner/logistics',
                         resource_class_kwargs={'routing': routing})

        api.add_resource(LogisticsContinuousPlan, '/delivery/planner/continuous',
                         resource_class_kwargs={'routing': routing})

        api.add_resource(RoutingResource, '/delivery/planner//routing',
                         resource_class_kwargs={'routing': routing})

        api.add_resource(PlanTimetableResource, '/delivery/planner/timetable/optimize',
                         resource_class_kwargs={'timetable_optimizer': timetable_optimizer})

        # SWAGGER
        api.add_resource(SwaggerResource, '/swagger')

