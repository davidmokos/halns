from enum import Enum


# imported from godeliver-service
class Mode(str, Enum):
    CAR = 'CAR'
    BIKE = 'BIKE'
    ELECTRIC_BIKE = 'ELECTRIC_BIKE'
    TRANSIT = 'TRANSIT'
    WALK = 'WALK'
