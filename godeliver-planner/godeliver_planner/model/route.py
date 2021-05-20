from enum import Enum
from typing import List
from pydantic import BaseModel
from godeliver_planner.model.location import Location
from godeliver_planner.model.mode import Mode


class TransportMode(str, Enum):
    walk = 'WALK'
    bike = 'BIKE'
    eletric_bike = 'ELECTRIC_BIKE'
    car = 'CAR'

    subway = 'SUBWAY'
    tram = 'TRAM'
    bus = 'BUS'
    rail = 'RAIL'

    @classmethod
    def from_fuzee(cls, mode):
        if mode == 'WALKING':
            return cls(TransportMode.walk)

        if mode == 'BIKING':
            return cls(TransportMode.bike)

        return cls(mode)


class Address(BaseModel):
    address: str
    location: Location
    address_note: str = None


class Leg(BaseModel):
    origin_address: Address
    destination_address: Address
    duration: int
    #waiting_duration: int
    distance: int
    mode: Mode
    polyline: str = None


class Step(BaseModel):
    duration: int
    distance: int
    waiting_time: int = None
    eta: int = None


class Route(BaseModel):
    origin_location: Location
    destination_location: Location
    duration: int
    distance: int
    mode: Mode
    steps: List[Step] = []
    legs: List[Leg] = []
