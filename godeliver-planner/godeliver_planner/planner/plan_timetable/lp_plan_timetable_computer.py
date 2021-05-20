from typing import List

import typing
from scipy.optimize import linprog

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.planner.vrp_instance_builder import TimeWindowConstraint, MAX_TIMESTAMP_VALUE
import numpy as np

from godeliver_planner.planner.exceptions.planner_exceptions import PlanUnfeasibleException
from godeliver_planner.planner.plan_timetable.plan_timetable_computer import AbstractPlanTimetableComputer


class LpPlanTimetableComputer(AbstractPlanTimetableComputer):

    def compute_optimal_timetable(self,
                                  drop_nodes: List[int],
                                  pickup_nodes: List[int],
                                  car_duration_matrix,
                                  time_windows: typing.Dict[int, List[TimeWindowConstraint]],
                                  route: List[int]) -> (List[int], List[int], float):
        config = ConfigProvider.get_config()

        plan_len = len(route)
        A, b = [], []

        timestamps = []
        time_windows_len = 0
        for p in route:
            tws = time_windows.get(p)
            if tws:
                time_windows_len = time_windows_len + len(tws)
                for tw in filter(lambda x: x.from_time > 0, tws):
                    timestamps.append(tw.from_time)
        timestamp_shift = min(timestamps)

        row_length = 2 * plan_len + time_windows_len
        penalty_index = 0
        for idx, p in enumerate(route):
            eta_column = idx
            etd_column = plan_len + idx

            if p in drop_nodes:
                # departure time is grater than arrival time plus waiting time
                #  eta - etd <= -waiting
                row = np.zeros(row_length)
                row[eta_column], row[etd_column] = 1, -1
                A.append(row)
                b.append(- config.get_service_time(DeliveryEventType.drop))

                if not config.allow_wait_on_drop:
                    row = np.zeros(row_length)
                    row[eta_column], row[etd_column] = -1, 1
                    A.append(row)
                    b.append(config.get_service_time(DeliveryEventType.drop))

            if p in pickup_nodes:
                # departure time is grater than arrival time plus waiting time
                #  eta - etd <= -waiting
                row = np.zeros(row_length)
                row[eta_column], row[etd_column] = 1, -1
                A.append(row)
                b.append(- config.get_service_time(DeliveryEventType.pickup))

            if idx > 0:
                # Arrival time on current node is equal to departure time from previous plus travel time
                row = np.zeros(row_length)
                row[eta_column], row[etd_column - 1] = 1, -1
                A.append(row)
                tt = car_duration_matrix[route[idx - 1]][p]
                b.append(tt)
                row = np.zeros(row_length)
                row[eta_column], row[etd_column - 1] = -1, +1
                A.append(row)
                b.append(- tt)

            tws = time_windows.get(p, [])
            for tw in tws:
                tw_start = tw.from_time - timestamp_shift
                tw_end = tw.to_time - timestamp_shift

                penalty_column = 2 * plan_len + penalty_index

                if tw.is_hard:
                    if tw.from_time > 0:
                        row = np.zeros(row_length)
                        row[etd_column] = -1
                        A.append(row)
                        b.append(- tw_start)

                    if tw.to_time < MAX_TIMESTAMP_VALUE:
                        row = np.zeros(row_length)
                        row[eta_column] = 1
                        A.append(row)
                        b.append(tw_end)
                else:
                    if tw.from_time > 0:
                        row = np.zeros(row_length)
                        row[etd_column], row[penalty_column] = - tw.weight, -1
                        A.append(row)
                        b.append(- tw.weight * tw_start)

                    if tw.to_time < MAX_TIMESTAMP_VALUE:
                        row = np.zeros(row_length)
                        row[eta_column], row[penalty_column] = tw.weight, -1
                        A.append(row)
                        b.append(tw.weight * tw_end)

                penalty_index = penalty_index + 1

        A = np.vstack(tuple(A))
        b = np.array(b, dtype=int)
        c = np.array([0 if i < 2 * plan_len else 1 for i in range(row_length)], dtype=int)
        all_positive = [(0, None) for x in range(2 * plan_len)] + \
                       [(0, None) for x in range(time_windows_len)]
        # noinspection PyTypeChecker
        res = linprog(c, A_ub=A, b_ub=b, bounds=all_positive, method='revised simplex',
                      options={'presolve': True, 'tol': 0.00001})

        if res.success:
            penalty = round(res.fun, ndigits=2)
            etas = list(map(lambda e: e + timestamp_shift, res.x[0:plan_len]))
            etds = list(map(lambda e: e + timestamp_shift, res.x[plan_len:2 * plan_len]))

            return etas, etds, penalty

        raise PlanUnfeasibleException(res.message)
