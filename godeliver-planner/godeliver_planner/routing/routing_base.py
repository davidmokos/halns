import abc
from typing import List, Optional

from godeliver_planner.helper.config_provider import ConfigProvider
from godeliver_planner.model.delivery_event import DeliveryEventType
from godeliver_planner.model.location import Location, TimeLocation


class RoutingBase(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def create_duration_distance_matrix(self, locations: List[Location],  **kwargs):
        raise NotImplemented

    @abc.abstractmethod
    def _get_duration_distance_route(self, locations: List[Location]) -> List[int]:
        pass

    def compute_time_along_route(self, locations: List[Location], starting_time: int) -> List[TimeLocation]:
        ret = []

        durations, distances = self._get_duration_distance_route(locations)

        time = starting_time
        for duration_time, location in zip(durations, locations):
            time = time + duration_time

            ret.append(
                TimeLocation(
                    time=time,
                    location=location
                )
            )

        return ret, distances

