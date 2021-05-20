import ctypes
import json
import os
import time

from godeliver_planner.planner.exceptions.planner_exceptions import PlanUnfeasibleException
from godeliver_planner.planner.vrp_instance_builder import VehicleRoutingProblemInstance, VehicleRoutingProblemSolution


def get_go_lib_path():
    d = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
    f = os.path.join(d, 'golang_impl.so')
    return f


class GoLangAdapter:
    def _call_go_library(self, vrp_instance: VehicleRoutingProblemInstance, function: str,
                         name: str) -> VehicleRoutingProblemSolution:
        encoded_instance = vrp_instance.to_json().encode('utf-8')
        so = ctypes.cdll.LoadLibrary(get_go_lib_path())
        solver = getattr(so, function)
        solver.argtypes = [ctypes.c_char_p]
        solver.restype = ctypes.c_void_p
        free = so.free
        free.argtypes = [ctypes.c_void_p]
        print(f"{name} Started")
        start_t = time.time()
        res = solver(encoded_instance)
        print(f"{name} finished in time {time.time() - start_t}")
        output = ctypes.string_at(res).decode('utf-8')
        try:
            x = json.loads(output, object_hook=lambda d: VehicleRoutingProblemSolution(**d))
            free(res)
            return x
        except Exception:
            raise PlanUnfeasibleException(output)

    def halns_impl(self, vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:
        return self._call_go_library(vrp_instance=vrp_instance, function="HALNS", name="HALNS")

    def jackpot_heuristics_impl(self, vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:
        return self._call_go_library(vrp_instance=vrp_instance, function="JackpotHeuristics", name="Jackpot Heuristics")

    def insertion_heuristics_impl(self, vrp_instance: VehicleRoutingProblemInstance) -> VehicleRoutingProblemSolution:
        return self._call_go_library(vrp_instance=vrp_instance, function="GOInsertionHeuristics",
                                     name="Insertion Heuristics")

    def save_instance(self, vrp_instance: VehicleRoutingProblemInstance, path: str):
        encoded_instance = vrp_instance.to_json()
        with open(path, 'w') as outfile:
            outfile.write(encoded_instance)

    def load_computed_solution(self, name: str):
        path = os.path.join(os.path.dirname(get_go_lib_path()), "solutions", f"{name}.json")
        with open(path, "rb") as text_file:
            output = text_file.read()

        try:
            x = json.loads(output, object_hook=lambda d: VehicleRoutingProblemSolution(**d))
            return x
        except Exception:
            raise PlanUnfeasibleException(output)


