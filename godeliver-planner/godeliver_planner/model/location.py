from flask_restful_swagger_2 import Schema
from haversine import haversine, Unit
from pydantic import BaseModel


class LocationModel(Schema):

    type = 'object'
    properties = {
        'latitude': {
            'type': 'number'
        },
        'longitude': {
            'type': 'number'
        }
    }


class Location(BaseModel):
    latitude: float
    longitude: float

    @classmethod
    def from_str(cls, loc_str: str):
        cords = loc_str.split(',')

        latitude = float(cords[0])
        longitude = float(cords[1])

        return cls(latitude=latitude, longitude=longitude)

    def __hash__(self):
        return hash((self.latitude, self.longitude))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.latitude == other.latitude and self.longitude == other.longitude

    def __str__(self) -> str:
        return f'{self.longitude},{self.latitude}'

    def to_osrm_string(self):
        return f'{self.longitude},{self.latitude}'

    def to_string(self):
        return f'{self.latitude},{self.longitude}'

    def distance_from(self, other):
        dst = haversine((self.latitude, self.longitude), (other.latitude, other.longitude), unit=Unit.METERS)
        return dst


class TimeLocation(BaseModel):
    location: Location
    time: int = None


class TimeLocationModel(Schema):

    type = 'object'
    properties = {
        'location': LocationModel,
        'time': {
            'type': 'int'
        },
    }
    required = ['location', 'time']


if __name__ == '__main__':
    loc_1 = Location(latitude=50.1, longitude=14.1)
    loc_2 = Location(latitude=50.1, longitude=14.1)

    print(';'.join([loc_1.to_osrm_string(), loc_2.to_osrm_string()]))
