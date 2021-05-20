import abc
from abc import ABC
from typing import List


class AbstractPlanTimetableComputer(ABC):

    @abc.abstractmethod
    def compute_optimal_timetable(self,
                                  drop_nodes: List[int],
                                  pickup_nodes: List[int],
                                  car_duration_matrix,
                                  time_windows: dict,
                                  route: List[int]) -> (List[int], List[int], float):
        pass
