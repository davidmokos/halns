from datetime import datetime, timedelta

from flask_restful_swagger_2 import Schema
from pydantic import BaseModel
from typing import Optional

MAX_TIMESTAMP_VALUE = 2147483647


class TimeBlockModel(Schema):

    type = 'object'
    properties = {
        'from_time': {
            'type': 'integer',
            'required': True
        },
        'to_time': {
            'type': 'integer',
            'required': False
        },
        'asap': {
            'type': 'boolean',
            'required': False
        },
        'anytime': {
            'type': 'boolean',
            'required': False
        }
    }


class TimeBlock(BaseModel):
    from_time: int
    to_time: Optional[int]
    anytime: bool = False
    asap: bool = False

    def get_to_time(self):
        if self.to_time is not None:
            return self.to_time

        if self.asap:
            return self.from_time + 5 * 60

        if self.anytime:
            d = (datetime.fromtimestamp(self.from_time) + timedelta(days=1)).timestamp()
            d = int(d)
            ret = d - (d % (60 * 60 * 24)) - 60 * 60
            return ret

        return self.from_time

    def shift_by(self, by: int):
        self.from_time = self.from_time + by
        if self.to_time is not None:
            self.to_time = self.to_time + by

    def __str__(self) -> str:
        return f"{datetime.fromtimestamp(self.from_time).strftime('%H:%M')} - " \
               f"{datetime.fromtimestamp(self.get_to_time()).strftime('%H:%M')} "


