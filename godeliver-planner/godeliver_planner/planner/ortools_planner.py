from collections import defaultdict
from typing import List
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver.pywrapcp import RoutingModel, RoutingIndexManager, Assignment, Solver, RoutingDimension
from ortools.constraint_solver.routing_parameters_pb2 import RoutingSearchParameters
from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.helper.exceptions import NoSolutionException
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.planner_config import PlannerType
from godeliver_planner.planner.abstract_planner import AbstractPlanner
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemSolution, \
    TimeWindowConstraint, MAX_TIMESTAMP_VALUE
from godeliver_planner.planner.plan_timetable.lp_plan_timetable_computer import LpPlanTimetableComputer
from godeliver_planner.routing.routing_base import RoutingBase


class ORToolsPlanner(AbstractPlanner):
    DURATION_DIMENSION_NAME = 'Duration'
    DISTANCE_DIMENSION_NAME = 'Distance'
    COUNT_DIMENSION_NAME = 'Count'
    CAPACITY_DIMENSION_NAME = 'CAPACITY'

    def __init__(self, routing: RoutingBase):
        super().__init__(routing)
        self.timetable_computer = LpPlanTimetableComputer()

    def get_name(self) -> str:
        return PlannerType.or_tools.value

    def solve(self, vrp_instance):
        manager, routing, search_parameters = self._init_pywrapcp(vrp_instance, len(vrp_instance.drop_nodes))

        self._set_optimization_criteria(routing, manager, vrp_instance)

        initial_routes = self._parse_initial_routes(vrp_instance, manager)

        assignment = self._solve(routing, search_parameters, initial_routes)

        # Print assignment on console.
        if not assignment:
            raise NoSolutionException('Failed to solve!')

        self.print_solution(vrp_instance, manager, routing, assignment)

        solution = self._extract_solution(assignment=assignment,
                                          manager=manager,
                                          routing=routing, vrp_instance=vrp_instance)

        try:
            solution = self.optimize_times_in_solution(
                solution=solution,
                vrp_instance=vrp_instance
            )
        except Exception as e:
            print(f"Unable to optimize the timetable for {vrp_instance.__dict__} with solution {solution.__dict__}")
            print(e)

        return solution

    def _parse_initial_routes(self, data: VehicleRoutingProblemInstance, manager: RoutingIndexManager):
        if not data.previous_plans:
            return None

        ret = []

        for route in data.previous_plans:
            ret.append([manager.NodeToIndex(node) for node in route])

        return ret

    def _extract_solution(self, assignment: Assignment, vrp_instance: VehicleRoutingProblemInstance,
                          manager: RoutingIndexManager, routing: RoutingModel) \
            -> VehicleRoutingProblemSolution:
        routes = []
        etas = []
        etds = []

        time_dimension = routing.GetDimensionOrDie(self.DURATION_DIMENSION_NAME)
        for vehicle_id in range(vrp_instance.num_plans_to_create):
            index = routing.Start(vehicle_id)

            route = []
            route_etas = []
            route_etds = []

            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)

                if node in vrp_instance.pickup_nodes:
                    this_event_time = vrp_instance.pickup_service_time
                elif node in vrp_instance.drop_nodes:
                    this_event_time = vrp_instance.drop_service_time
                else:
                    this_event_time = 0

                time_var = time_dimension.CumulVar(index)
                eta = assignment.Min(time_var)
                etd = assignment.Max(time_var) + this_event_time

                route.append(node)
                route_etas.append(eta)
                route_etds.append(etd)

                index = assignment.Value(routing.NextVar(index))

            routes.append(route)
            etas.append(route_etas)
            etds.append(route_etds)

        ret = VehicleRoutingProblemSolution(
            plans=routes,
            etas=etas,
            etds=etds
        )
        return ret

    def _solve(self, routing: RoutingModel, search_parameters: RoutingSearchParameters,
               initial_routes) -> Assignment:

        if initial_routes is None:
            solution = routing.SolveWithParameters(search_parameters)
        else:
            routing.CloseModelWithParameters(search_parameters)
            initial_solution = routing.ReadAssignmentFromRoutes(initial_routes, True)
            solution = routing.SolveFromAssignmentWithParameters(initial_solution, search_parameters)

        return solution

    @staticmethod
    def _init_pywrapcp(data_model: VehicleRoutingProblemInstance, no_deliveries: int):
        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(
            len(data_model.car_distance_matrix),  # number of points 2*len(deliveries)+1
            data_model.num_plans_to_create,
            data_model.starts,
            data_model.ends
        )

        solution_limit = 100 + 15 * no_deliveries

        # Setting first assignment heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = data_model.time_limit  # time limit
        search_parameters.solution_limit = solution_limit
        search_parameters.log_search = True

        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)

        solver = routing.solver()
        solver.ReSeed(100)

        return manager, routing, search_parameters

    def _set_optimization_criteria(self, routing: RoutingModel, manager: RoutingIndexManager,
                                   data: VehicleRoutingProblemInstance):

        tws_in_dimensions = self._split_tw_contraints_to_dimensions(time_windows=data.node_time_windows)

        for dimension in tws_in_dimensions.keys():
            self._set_arc_durations(data, manager, routing, dimension)

        self._set_arc_distance(data, manager, routing)

        for dimension in tws_in_dimensions.keys():
            self._set_time_dimension_constraints(routing, manager, dimension, data.start_time_windows,
                                                 tws_in_dimensions[dimension], data.num_plans_to_create)

        self._set_capacity_dimension_constraints(data, routing, manager)

        self._set_balance_constraints_on_number_of_packages(data, routing)
        self._set_pickup_delivery_constraints(data, routing, manager)
        # self._set_omit_node_penalty(data.pickup_nodes, routing, manager)
        # self._set_omit_node_penalty(data.drop_nodes, routing, manager)

    def _split_tw_contraints_to_dimensions(self, time_windows: List[TimeWindowConstraint]):
        node_to_tws = defaultdict(lambda: defaultdict(lambda: list()))

        for tw in time_windows:
            tws_of_node = node_to_tws[tw.node]

            if tw.has_lower_bound():
                tws_of_node['lower'].append(tw)
            if tw.has_upper_bound():
                tws_of_node['upper'].append(tw)

        no_dimensions_needed = max(map(lambda k: max(len(node_to_tws[k]['lower']), len(node_to_tws[k]['upper'])), node_to_tws.keys()))

        ret = defaultdict(lambda: list())
        for dimension in range(no_dimensions_needed):
            dimension_name = self.DURATION_DIMENSION_NAME + (str(dimension) if dimension else "")
            for node in node_to_tws:
                if len(node_to_tws[node]['lower']) > dimension:
                    ret[dimension_name].append(node_to_tws[node]['lower'][dimension])
                if len(node_to_tws[node]['upper']) > dimension:
                    ret[dimension_name].append(node_to_tws[node]['upper'][dimension])

        return ret

    def _set_arc_durations(self, data: VehicleRoutingProblemInstance,
                           manager: RoutingIndexManager, routing: RoutingModel,
                           dimension_name: str):
        # ========= DURATION CONSTRAIN =========
        cost_callback_indices = []
        # model "cost between nodes per vehicle"
        for vehicle_idx in range(data.num_plans_to_create):
            def vehicle_cost_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                time = data.car_duration_matrix[from_node][to_node]  # in seconds

                is_pickup = from_node in data.pickup_nodes
                is_drop = from_node in data.drop_nodes

                waiting_time = 0
                if is_pickup:
                    waiting_time = ConfigProvider.get_config().pickup_waiting_time
                elif is_drop:
                    waiting_time = ConfigProvider.get_config().drop_waiting_time

                return time + waiting_time

            cost_callback_index = routing.RegisterTransitCallback(vehicle_cost_callback)
            cost_callback_indices.append(cost_callback_index)

        routing.AddDimensionWithVehicleTransits(
            cost_callback_indices,
            MAX_TIMESTAMP_VALUE,  # waiting time
            MAX_TIMESTAMP_VALUE,  # maximum time per vehicle
            # since we are using timestamps as measuring unit we should not overflow
            False,  # Don't force start cumul to zero.
            dimension_name)

    def _set_arc_distance(self, data: VehicleRoutingProblemInstance,
                          manager: RoutingIndexManager, routing: RoutingModel):
        # ========= DISTANCE CONSTRAIN =========
        cost_callback_indices = []
        # model "cost between nodes per vehicle"
        for vehicle_idx in range(data.num_plans_to_create):
            def vehicle_cost_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                distance = data.car_distance_matrix[from_node][to_node]  # in meters

                return distance

            cost_callback_index = routing.RegisterTransitCallback(vehicle_cost_callback)
            cost_callback_indices.append(cost_callback_index)
            routing.SetArcCostEvaluatorOfVehicle(cost_callback_index, vehicle_idx)

        routing.AddDimensionWithVehicleTransits(
            cost_callback_indices,
            0,  # waiting time
            MAX_TIMESTAMP_VALUE,  # maximum distance per vehicle
            True,  # Force start cumul to zero.
            self.DISTANCE_DIMENSION_NAME)

    @staticmethod
    def _set_constraint_on_var(index: int, constraint: TimeWindowConstraint, time_dimension: RoutingDimension):
        if constraint.is_hard:
            time_dimension.CumulVar(index).SetRange(constraint.from_time, constraint.to_time)
        else:
            if constraint.from_time > 0:
                time_dimension.SetCumulVarSoftLowerBound(index, constraint.from_time, constraint.weight)
            if constraint.to_time < MAX_TIMESTAMP_VALUE:
                time_dimension.SetCumulVarSoftUpperBound(index, constraint.to_time, constraint.weight)

    def _set_time_dimension_constraints(self,
                                        routing: RoutingModel,
                                        manager: RoutingIndexManager,
                                        dimension_name: str,
                                        start_time_windows: List[TimeWindowConstraint],
                                        node_time_windows: List[TimeWindowConstraint],
                                        num_plans_to_create: int):

        # ========= TIME WINDOW =========
        time_dimension = routing.GetDimensionOrDie(dimension_name)
        for constraint in start_time_windows:
            index = routing.Start(constraint.node)
            self._set_constraint_on_var(index, constraint, time_dimension)

        for constraint in node_time_windows:
            index = manager.NodeToIndex(constraint.node)
            self._set_constraint_on_var(index, constraint, time_dimension)

        # Instantiate route start and end times to produce feasible times.
        for i in range(num_plans_to_create):
            routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(routing.Start(i)))
            routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(routing.End(i)))

    def _set_capacity_dimension_constraints(self,
                                            data: VehicleRoutingProblemInstance,
                                            routing: RoutingModel,
                                            manager: RoutingIndexManager):

        if data.courier_capacities is None:
            return

        def demand_callback(index):
            node = manager.IndexToNode(index)
            return data.node_demands[node]

        capacity_callback = routing.RegisterUnaryTransitCallback(demand_callback)

        routing.AddDimensionWithVehicleCapacity(
            capacity_callback,
            0,  # waiting time
            data.courier_capacities,  # maximum distance per vehicle
            False,  # Force start cumul to zero.
            self.CAPACITY_DIMENSION_NAME)

        capacity_dimension = routing.GetDimensionOrDie(self.CAPACITY_DIMENSION_NAME)

        for courier_idx, start_utilization in enumerate(data.start_utilizations):
            node_idx = routing.Start(courier_idx)
            self._set_constraint_on_var(node_idx,
                                        TimeWindowConstraint(node=node_idx,
                                                             is_hard=True,
                                                             from_time=start_utilization,
                                                             to_time=start_utilization),
                                        capacity_dimension)

    def _set_balance_constraints_on_number_of_packages(self, data: VehicleRoutingProblemInstance,
                                                       routing: RoutingModel):
        # ========= BALANCE DISTRIBUTION CONSTRAIN =========
        routing.AddConstantDimension(
            1,  # increment by one every time
            100000,  # max value forces equivalent # of jobs
            True,  # set count to zero
            self.COUNT_DIMENSION_NAME)

        average_load = int(2 * len(data.drop_nodes) // data.num_plans_to_create)  # each delivery has 2 locations
        count_dimension = routing.GetDimensionOrDie(self.COUNT_DIMENSION_NAME)
        for veh in range(0, data.num_plans_to_create):
            index_end = routing.End(veh)

            # https://github.com/google/or-tools/blob/v8.0/ortools/constraint_solver/routing.h#L2460
            # 5 min penalty for every order over average load
            count_dimension.SetCumulVarSoftUpperBound(index_end, average_load + 6, 5 * 60)

    def _set_balance_constraints_on_distance_driven(self, data: VehicleRoutingProblemInstance,
                                                    routing: RoutingModel, deliveries: List[Delivery]):
        # ========= BALANCE DISTRIBUTION CONSTRAIN =========
        # https://activimetrics.com/blog/ortools/counting_dimension/
        # A “fair” distribution of loads
        average_load = int(2 * len(deliveries) // data.num_plans_to_create)  # each delivery has 2 locations
        count_dimension = routing.GetDimensionOrDie(self.DISTANCE_DIMENSION_NAME)
        for veh in range(0, data.num_plans_to_create):
            index_end = routing.End(veh)

            # https://github.com/google/or-tools/blob/v8.0/ortools/constraint_solver/routing.h#L2460
            # 5 min penalty for every order over average load
            count_dimension.SetCumulVarSoftLowerBound(index_end, average_load, 5 * 60)

    def _set_pickup_delivery_constraints(self, data: VehicleRoutingProblemInstance,
                                         routing: RoutingModel, manager: RoutingIndexManager):
        time_dimension = routing.GetDimensionOrDie(self.DURATION_DIMENSION_NAME)

        # ========= PICKUP/DELIVERY CONSTRAIN =========
        # Define Transportation Requests.
        solver: Solver = routing.solver()
        for pickup_node, delivery_node in data.deliveries_not_started:
            pickup_index = manager.NodeToIndex(pickup_node)
            delivery_index = manager.NodeToIndex(delivery_node)
            routing.AddPickupAndDelivery(pickup_index, delivery_index)
            solver.Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
            solver.Add(time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index))

        # Define constraint of deliveries in progress - only vehicle that picked the order is able to finish it
        for courier_idx, node in data.deliveries_in_progress:
            index = manager.NodeToIndex(node)
            routing.SetAllowedVehiclesForIndex([courier_idx], index)

    @staticmethod
    def _set_omit_node_penalty(nodes: List[int],
                               routing: RoutingModel, manager: RoutingIndexManager):
        # Allow to drop nodes.
        penalty = 1000000
        for node in nodes:
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

    @staticmethod
    def print_solution(data: VehicleRoutingProblemInstance, manager: RoutingIndexManager, routing: RoutingModel,
                       solution: Assignment):
        """Prints assignment on console."""
        time_dimension = routing.GetDimensionOrDie('Duration')
        total_time = 0
        for vehicle_id in range(data.num_plans_to_create):
            start_time = None
            index = routing.Start(vehicle_id)
            plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
            while not routing.IsEnd(index):
                time_var = time_dimension.CumulVar(index)
                if start_time is None:
                    start_time = solution.Min(time_var)
                plan_output += '{0} Time({1},{2}) -> '.format(
                    manager.IndexToNode(index), solution.Min(time_var),
                    solution.Max(time_var))
                index = solution.Value(routing.NextVar(index))
            time_var = time_dimension.CumulVar(index)
            plan_output += '{0} Time({1},{2})\n'.format(manager.IndexToNode(index),
                                                        solution.Min(time_var),
                                                        solution.Max(time_var))
            plan_output += f'Start of the route: {start_time}\n'
            plan_output += 'Time of the route: {} sec\n'.format(solution.Min(time_var) - start_time)
            print(plan_output)

            total_time += solution.Min(time_var) - start_time
        print('Total time of all routes: {} sec'.format(total_time))
