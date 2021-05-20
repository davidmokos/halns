import os
import time
from enum import Enum
from itertools import product
from pprint import pprint
from typing import List

import aiohttp
import numpy as np

from godeliver_planner.helper.utils import YamlConfig, run_async
from godeliver_planner.model.location import Location
from godeliver_planner.routing.routing_base import RoutingBase


class OSRMProfile(Enum):
    car = 'CAR'
    bike = 'BIKE'
    walk = 'FOOT'
    driving = 'DRIVING'


class OSRMRegion(Enum):
    prague = 'prague'
    czechia = 'czechia'


class OSRMRouting(RoutingBase):

    def __init__(self, session=None):
        d = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        config_file = os.path.join(d, "config", "config.yml")

        self.config = YamlConfig(file_path=config_file)
        self.session = session
        self.osrm_time_coeficient = 1.5

    def _build_url(self, locations: List[Location], mode: OSRMProfile, region: OSRMRegion=OSRMRegion.czechia):

        base_url = self.config['osrm'][region.value]['base_url']

        # We may extend the config to build the whole url based on the components
        # service = self.config['osrm'][region.value]['service']
        # version = self.config['osrm'][region.value]['version']

        coordinates = ";".join(map(lambda loc: f"{loc.longitude},{loc.latitude}", locations))
        return f"{base_url}/{coordinates}"

    def auth_header(self):
        return {
            'Authorization': 'Basic c2tvZGFkaWdpbGFiOlVhQmg2Uk5UN1F4cUQ1Umg2eDl1'
        }

    def create_duration_distance_matrix(self,
                                        locations: List[Location],
                                        mode: OSRMProfile = OSRMProfile.driving,
                                        hour: int = 12,
                                        chunk_size: int = 100):

        assert 0 <= hour <= 23

        locations = np.array(locations)
        index_map = self._get_combinations(list(range(len(locations))), chunk_size)

        result_duration, result_distance = self._get_result_for_combinations(locations, index_map, mode)

        result_duration = (np.array(result_duration) * self.osrm_time_coeficient).astype(int).tolist()

        return result_duration, result_distance

    def _get_result_for_combinations(self, locations, index_map, mode):
        start_t = time.time()

        result_duration = [[None for _ in range(len(locations))] for _ in range(len(locations))]
        result_distance = [[None for _ in range(len(locations))] for _ in range(len(locations))]

        print("OSRM started")

        async def async_fetch():
            for imap in index_map:
                async with aiohttp.ClientSession() as session:
                    indmap = imap[0] + imap[1]
                    locs = locations[indmap]
                    # print("Get data for indexes: ", imap)
                    # pprint(locs)
                    url = self._build_url(locs, mode)

                    params_url = {'sources': ";".join(map(str, range(0, len(imap[0])))),
                                  'destinations': ";".join(map(str, range(len(imap[0]), len(locs)))),
                                  'annotations': 'duration,distance',
                                  # 'time': hour #  TODO see doc
                                  }

                    async with session.get(url, params=params_url, headers=self.auth_header()) as response:
                        response.raise_for_status()
                        data = await response.json()
                        # print(f'Response: {data}')

                    self._insert_to(from_matrix=data['distances'],
                                    to_matrix=result_distance,
                                    x_axe_indexes=imap[0], y_axe_indexes=imap[1])
                    self._insert_to(from_matrix=data['durations'],
                                    to_matrix=result_duration,
                                    x_axe_indexes=imap[0], y_axe_indexes=imap[1])

        run_async(async_fetch)
        print("OSRM finished in time: ", time.time() - start_t)

        return result_duration, result_distance

    def _insert_to(self, from_matrix, to_matrix, x_axe_indexes, y_axe_indexes):
        for i, x in enumerate(x_axe_indexes):
            for j, y in enumerate(y_axe_indexes):
                to_matrix[x][y] = from_matrix[i][j]

    def _chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def _get_combinations(self, locations, chunk_size):
        chunks = list(self._chunks(locations, chunk_size))
        return list(product(chunks, repeat=2))

    def _get_pairs(self, locations, chunk_size):
        sources = [locations[i] for i in range(len(locations) - 1)]
        destinations = [locations[i] for i in range(1, len(locations) )]
        sources_ch = list(self._chunks(sources, chunk_size))
        dest_ch = list(self._chunks(destinations, chunk_size))
        return list(zip(sources_ch, dest_ch))

    def _get_duration_distance_route(self, locations: List[Location],
                                     mode: OSRMProfile = OSRMProfile.driving,
                                         hour: int = 12,
                                         chunk_size: int = 25) -> List[int]:
        start_t = time.time()
        assert 0 <= hour <= 23

        locations = np.array(locations)
        n_locations = len(locations)
        locations_idx = list(range(n_locations))
        index_map = self._get_pairs(locations_idx, chunk_size)

        result_duration_matrix, result_distance_matrix = self._get_result_for_combinations(locations, index_map, mode)

        result_duration_vector = [0]
        result_distance_vector = [0]

        for i in range(n_locations - 1):
            result_duration_vector.append(int(result_duration_matrix[i][i + 1]))
            result_distance_vector.append(int(result_distance_matrix[i][i+1]))

        result_duration_vector = (np.array(result_duration_vector) * self.osrm_time_coeficient).astype(np.int).tolist()

        return result_duration_vector, result_distance_vector


if __name__ == "__main__":
    osrm_routing = OSRMRouting()

    locations = [
        Location.from_str('50.09966861137477,14.395826276405387'),
        Location.from_str('50.09752743564536,14.407465388008859'),
        Location.from_str('50.07149965096569,14.404273607076334'),
        Location.from_str('50.08149965092269,14.504273607068092'),
        Location.from_str('50.08142235096111,14.504273247076336'),
        Location.from_str('50.08124535096111,14.509473247076336'),
        # Location.from_str('50.08142235096111,14.011213247076336'),
        # Location.from_str('50.08109825096111,14.512373247076336')
    ]

    pprint(osrm_routing.create_duration_distance_matrix(locations=locations, mode=OSRMProfile.car))
