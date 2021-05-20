from flask import Flask
from flask_cors import CORS
from flask_restful_swagger_2 import Api

from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.planner.ortools_planner import ORToolsPlanner
from godeliver_planner.planner.plan_timetable.lp_plan_timetable_computer import LpPlanTimetableComputer
from godeliver_planner.planner.plan_timetable.plan_timetable_optimizer import PlanTimetableOptimizer
from godeliver_planner.resource.resource_manager import ResourceManager
from godeliver_planner.routing.osrm_service import OSRMRouting


class AppFactory:

    @staticmethod
    def create_app():

        app = Flask(__name__, template_folder='./static')
        CORS(app)
        api = Api(app, api_version='0.2',
                  api_spec_url='/api/swagger',
                  title='GoDeliver Planner',
                  description='Planner for deliveries')

        app.config['DEBUG'] = True

        # ---INIT OBJECTS---
        # TODO: add dependecy injection!
        #routing = GoogleRouting()
        routing = OSRMRouting()
        planner = ORToolsPlanner(routing=routing)
        continuous_planner = ORToolsPlanner(routing=routing)
        timetable_computer = LpPlanTimetableComputer()
        timetable_optimizer = PlanTimetableOptimizer(
            routing=routing,
            timetable_computer=timetable_computer
        )

        # ---REGISTER RESOURCE----
        # TODO: add dependecy injection!
        ResourceManager.register(api=api, planner=planner,
                                 continuous_planner=continuous_planner,
                                 routing=routing,
                                 timetable_optimizer=timetable_optimizer)

        return app